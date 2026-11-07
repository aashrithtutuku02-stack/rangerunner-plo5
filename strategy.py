"""Equity, Bayesian opponent ranges, and chip-EV action selection."""
import math
import time

import numpy as np

import fast_engine as engine
import range_model
from game import Action, Street

# Prepare once, during startup. No runtime downloads or disk caches.
engine.warm_engine()
range_model.warmup()

SLOPES = np.array([0.0, 8.0, 16.0])


def initialize(config, memory):
    memory.update(
        hands_played=0, config=config, cpu=0.0, decisions=0,
        rng=np.uint64(0x9E3779B97F4A7C15), cache=None, last=None,
        seen_hand=-1, seen_count=0,
        # Per street, separate unraised pots from facing a bet.
        counts=np.array([[[0.0, 7.0, 5.0], [4.0, 6.0, 2.0], [5.0, 5.0, 2.0]],
                         [[0.0, 7.0, 5.0], [4.0, 6.0, 2.0], [5.0, 5.0, 2.0]],
                         [[0.0, 8.0, 4.0], [5.0, 5.0, 2.0], [6.0, 4.0, 2.0]],
                         [[0.0, 8.0, 4.0], [5.0, 5.0, 2.0], [6.0, 4.0, 2.0]]]),
        models=np.array([0.10, 0.30, 0.60]),
    )


def history_events(obs,raise_cap=4):
    """Recover each opponent action's price from the public action log."""
    # Recover forced contributions from chip conservation. This remains
    # correct if blind/stack settings change, rather than hard-coding 1/2.
    start=(obs.pot+obs.my_stack+obs.opp_stack)//2
    mine=start-obs.my_stack-sum(a.amount for a in obs.action_history if a.is_me)
    theirs=start-obs.opp_stack-sum(a.amount for a in obs.action_history if not a.is_me)
    pot = mine+theirs
    my_remaining=start-mine;opp_remaining=start-theirs
    street = Street.PREFLOP
    raises=0
    opponent_raised=False
    events = []
    for idx, action in enumerate(obs.action_history):
        if action.street != street:
            mine = theirs = 0
            street = action.street
            opponent_raised=False
            raises=0
        if not action.is_me:
            facing = max(0, mine - theirs)
            context=0 if not facing else 2 if opponent_raised else 1
            available=raises<raise_cap and opp_remaining>facing and my_remaining>0
            events.append((idx, int(street), context, int(action.action),
                           facing / max(1, pot + facing),int(available)))
            theirs = action.street_total
            if action.action in (Action.RAISE_HALF,Action.RAISE_POT):opponent_raised=True
        else:
            mine = action.street_total
        if action.is_me:my_remaining-=action.amount
        else:opp_remaining-=action.amount
        if action.action in (Action.RAISE_HALF,Action.RAISE_POT):raises+=1
        pot += action.amount
    return events


def learn_actions(obs, memory):
    if memory['seen_hand'] != obs.hand_index:
        memory['seen_hand'] = obs.hand_index
        memory['seen_count'] = 0
    for event in history_events(obs,memory['config'].raise_cap):
        idx,street,facing,action,price=event[:5]
        if idx >= memory['seen_count']:
            observe_event(memory,event)
    memory['seen_count'] = len(obs.action_history)


def observe_event(memory,event):
    """Update opportunity-adjusted frequencies from a possibly censored action.

    A call when raising is impossible reveals only 'did not fold'. Preserve
    the existing call/raise ratio instead of counting it as evidence against
    raising. A compulsory free check reveals no preference at all.
    """
    _,street,context,action,price=event[:5]
    counts=memory['counts'][street,context]
    available=len(event)<6 or bool(event[5])
    action=min(action,2)
    if available or action==0:
        counts[action]+=1
    elif action==1 and context:
        nonfold=counts[1]+counts[2]
        share=counts[2]/nonfold if nonfold else 0.
        counts[1]+=1-share;counts[2]+=share


def action_prob(q, frequencies, slope, facing, price=0.25,can_raise=True):
    """Predict actions without inflating marginal frequencies as slope grows."""
    return range_model.action_prob(q,frequencies,slope,facing,price,can_raise)


def cache_samples(obs, memory):
    key = (obs.hand_index, obs.hole_cards, obs.board)
    cache = memory['cache']
    if cache is not None and cache['key'] == key:
        return cache
    # Spend less if the measured CPU budget gets ahead of the hand count.
    pace = memory['cpu'] / max(30, obs.hand_index + 1)
    count = 768 if len(obs.board) < 5 else 1280
    target = 0.40 * memory['config'].time_bank_seconds / max(1, memory['config'].num_hands)
    if pace > target:
        count //= 2
    if pace > 1.35 * target or memory['cpu'] > .60 * memory['config'].time_bank_seconds:
        count = 192
    hole = np.asarray(obs.hole_cards, dtype=np.int32)
    board = np.asarray(obs.board, dtype=np.int32)
    hands, values, outcomes, future, rng = engine.simulate(hole, board, count, memory['rng'])
    memory['rng'] = np.uint64(rng)
    q = engine.percentiles(values)
    # Early-street made-hand percentiles are less certain than river strength.
    # Shrink them rather than conditioning on a sampled, unseen future card.
    if len(board) >= 3:
        q[:, 1] = 0.78 * q[:, 1] + 0.22 * q[:, 0]
    if len(board) >= 4:
        q[:, 2] = 0.90 * q[:, 2] + 0.10 * q[:, 0]
    cache = dict(key=key, values=values, q=q, outcomes=outcomes,
                 hands=hands, board=board, hole=hole)
    memory['cache'] = cache
    return cache


def range_weights(obs, memory, cache):
    q = cache['q']
    events = history_events(obs,memory['config'].raise_cap)
    weights = range_model.likelihoods(q,memory['counts'],range_model.event_array(events),SLOPES)
    sums = weights.sum(axis=1)
    weights /= np.maximum(sums[:, None], 1e-100)
    mix = memory['models'] @ weights
    return mix, weights


def response_prob(obs, memory, cache, additional, price, model_weights=None):
    """Model an opponent's response to a proposed bet or raise."""
    street = int(obs.street)
    # Against a raise, opponents fold more often than against a first bet.
    context=2 if obs.to_call and obs.raises_this_street else 1
    frequencies = memory['counts'][street, context].copy()
    # action_prob applies the same price adjustment to observed calls and
    # prospective responses, so cheap calls do not imply the same range
    # as expensive ones.
    q = cache['q'][:, street]
    call=min(obs.opp_stack,max(0,obs.my_bet+additional-obs.opp_bet))
    available=(obs.raises_this_street+1<memory['config'].raise_cap
               and obs.my_stack>additional and obs.opp_stack>call)
    fp, cp, rp = action_prob(q[None, :], frequencies, SLOPES[:, None], True, price,available)
    if model_weights is None:
        return memory['models'] @ fp, memory['models'] @ rp
    # The response model and its hand range describe the same opponent.
    # Condition the model mixture on each candidate hand before predicting
    # its response; multiplying two separately averaged mixtures invents
    # cross-model combinations that were never part of the posterior.
    joint = memory['models'][:, None] * model_weights
    marginal = np.maximum(joint.sum(axis=0), 1e-100)
    return (joint * fp).sum(axis=0)/marginal, (joint * rp).sum(axis=0)/marginal


def decide(obs, memory):
    begin = time.perf_counter()
    if not memory:
        from game import AgentConfig
        initialize(AgentConfig(), memory)
    learn_actions(obs, memory)
    cache = cache_samples(obs, memory)
    weights, models = range_weights(obs, memory, cache)
    outcomes = cache['outcomes']
    equity = float(weights @ outcomes)
    if obs.street == Street.PREFLOP:
        lookup = engine.preflop_equity(cache['hole'])
        if lookup >= 0:
            # Control variate: use the offline estimate for the uniform
            # component, retaining simulated shifts from the betting range.
            equity += lookup - float(outcomes.mean())
            equity = min(1.0, max(0.0, equity))
            outcomes = outcomes + lookup - float(outcomes.mean())
    call = min(obs.to_call, obs.my_stack)
    street = int(obs.street)
    open_counts = memory['counts'][street, 0]
    aggression = float(open_counts[2] / open_counts.sum())
    # Equity realization: weak hands cannot always reach a free showdown.
    # The discount disappears when a call closes the action with all-ins.
    remaining = min(obs.my_stack - call, obs.opp_stack)
    discount = 0.0
    if street < 3 and remaining > 0:
        discount = (0.045, 0.035, 0.015)[street]
        discount *= (0.6 if obs.is_button else 1.0) * (0.5 + aggression)
        discount *= min(1.0, remaining / max(1, obs.pot + call))
    realized = max(0.0, equity - discount)
    passive_ev = realized * (obs.pot + call) - call
    action = Action.CHECK_CALL
    best_ev = passive_ev
    if call and best_ev < 0:
        action = Action.FOLD
        best_ev = 0.0
    for candidate in (Action.RAISE_HALF, Action.RAISE_POT):
        if candidate not in obs.legal_actions:
            continue
        invest = obs.raise_to[candidate] - obs.my_bet
        opp_call = min(obs.opp_stack, max(0, obs.raise_to[candidate] - obs.opp_bet))
        price = opp_call / max(1, obs.pot + invest + opp_call)
        fp, rp = response_prob(obs, memory, cache, invest, price, models)
        final_pot = obs.pot + invest + opp_call
        showdown_ev = outcomes * final_pot - invest
        ev = float(weights @ (fp * obs.pot + (1 - fp) * showdown_ev))
        # Reraises can force a marginal bettor off their equity. Account for
        # this cost when chips remain, without penalizing a true all-in bet.
        behind = min(obs.my_stack - invest, obs.opp_stack - opp_call)
        if behind > 0:
            reraise_risk = float(weights @ rp)
            ev -= reraise_risk * min(behind, final_pot) * max(0.0, 0.68 - equity)
        # Favor robust edges over changes caused by Monte Carlo noise.
        margin = 0.025 * obs.pot + 0.08
        if street == 0:
            margin += 0.25
        if ev > best_ev + margin:
            action, best_ev = candidate, ev
    if action not in obs.legal_actions:
        action = Action.CHECK_CALL
    memory['last'] = (obs, action, cache)
    memory['decisions'] += 1
    memory['cpu'] += time.perf_counter() - begin
    return action


def terminal_event(obs,action,result,raise_cap=4):
    """Infer a missing final response only when chip and street totals agree.

    Finished-hand callbacks do not contain action history. Inconsistent or
    stale results (for example after skipped requests) must not invent actions.
    """
    if action in (Action.RAISE_HALF,Action.RAISE_POT):
        invest=obs.raise_to[action]-obs.my_bet
        call=min(obs.opp_stack,max(0,obs.raise_to[action]-obs.opp_bet))
        context=2 if obs.to_call and obs.raises_this_street else 1
        if not result.went_to_showdown:
            if (result.winner!='me' or result.pot!=obs.pot+invest
                    or tuple(result.board)!=tuple(obs.board)):
                return None
            response=0
        else:
            immediate=(obs.street==Street.RIVER or invest==obs.my_stack or call==obs.opp_stack)
            if (not immediate or result.pot!=obs.pot+invest+call
                    or tuple(result.board[:len(obs.board)])!=tuple(obs.board)):
                return None
            response=1
        price=call/max(1,obs.pot+invest+call)
        available=(obs.raises_this_street+1<raise_cap and obs.my_stack>invest and obs.opp_stack>call)
        return (len(obs.action_history)+1,int(obs.street),context,response,price,int(available))
    if (action==Action.CHECK_CALL and obs.to_call==0 and obs.street==Street.RIVER
            and not obs.is_button and result.went_to_showdown
            and result.pot==obs.pot and tuple(result.board)==tuple(obs.board)):
        return (len(obs.action_history)+1,int(obs.street),0,1,0.,1)
    return None


def finish(result, memory):
    begin=time.perf_counter()
    memory['hands_played']=memory.get('hands_played',0)+1
    last=memory.get('last')
    if last is None or last[0].hand_index!=result.hand_index:
        return
    obs,action,cache=last
    events=history_events(obs,memory['config'].raise_cap)
    final=terminal_event(obs,action,result,memory['config'].raise_cap)
    if final is not None:
        events.append(final)
        observe_event(memory,final)
    complete=not (action in (Action.RAISE_HALF,Action.RAISE_POT) and final is None)
    if result.opp_hole and complete:
        opp=np.asarray(result.opp_hole,dtype=np.int32)
        values=cache['values']
        actual=np.zeros(4)
        actual[0]=engine.preflop_quality(opp)
        for s,n in ((1,3),(2,4),(3,5)):
            if len(obs.board)>=n:
                actual[s]=engine.score(opp,cache['board'][:n])
        actual_q=np.zeros((1,4))
        for s in range(4):
            if s==0 or len(obs.board)>=(0,3,4,5)[s]:
                col=values[:,s]
                actual_q[0,s]=(np.sum(col<actual[s])+.5*np.sum(col==actual[s]))/len(col)
        actual_q[0,1]=.78*actual_q[0,1]+.22*actual_q[0,0]
        actual_q[0,2]=.90*actual_q[0,2]+.10*actual_q[0,0]
        combined=np.concatenate((cache['q'],actual_q))
        L=range_model.likelihoods(combined,memory['counts'],range_model.event_array(events),SLOPES)
        evidence=(np.log(np.maximum(L[:,-1],1e-100))
                  -np.log(np.maximum(L[:,:-1].mean(axis=1),1e-100)))
        evidence-=evidence[0]
        posterior=memory['models']*np.exp(np.clip(evidence,-.6,.6))
        memory['models']=.985*posterior/posterior.sum()+.015/len(SLOPES)
    memory['last']=None;memory['cache']=None
    memory['cpu']+=time.perf_counter()-begin
