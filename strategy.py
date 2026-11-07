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


def history_events(obs):
    """Recover each opponent action's price from the public action log."""
    # Recover forced contributions from chip conservation. This remains
    # correct if blind/stack settings change, rather than hard-coding 1/2.
    start=(obs.pot+obs.my_stack+obs.opp_stack)//2
    mine=start-obs.my_stack-sum(a.amount for a in obs.action_history if a.is_me)
    theirs=start-obs.opp_stack-sum(a.amount for a in obs.action_history if not a.is_me)
    pot = mine+theirs
    street = Street.PREFLOP
    opponent_raised=False
    events = []
    for idx, action in enumerate(obs.action_history):
        if action.street != street:
            mine = theirs = 0
            street = action.street
            opponent_raised=False
        if not action.is_me:
            facing = max(0, mine - theirs)
            context=0 if not facing else 2 if opponent_raised else 1
            events.append((idx, int(street), context, int(action.action),
                           facing / max(1, pot + facing)))
            theirs = action.street_total
            if action.action in (Action.RAISE_HALF,Action.RAISE_POT):opponent_raised=True
        else:
            mine = action.street_total
        pot += action.amount
    return events


def learn_actions(obs, memory):
    if memory['seen_hand'] != obs.hand_index:
        memory['seen_hand'] = obs.hand_index
        memory['seen_count'] = 0
    for idx, street, facing, action, price in history_events(obs):
        if idx >= memory['seen_count']:
            memory['counts'][street, facing, min(action, 2)] += 1
    memory['seen_count'] = len(obs.action_history)


def action_prob(q, frequencies, slope, facing, price=0.25):
    """Smooth value/bluff models, including a card-independent model.

    Flatten selectivity as empirical behavior approaches a constant action.
    This prevents inventing a strong range for an opponent who always pots.
    """
    p = frequencies / frequencies.sum()
    if facing:
        p=p.copy()
        p[0]*=math.exp(3.0*(price-.28))
        p[1]*=math.exp(-1.5*(price-.28))
        p/=p.sum()
    sharpness = slope * min(1.0, 4.0 * (1.0 - float(p.max())))
    x = np.clip(q, 0.01, 0.99) - 0.5
    r = p[2] * np.exp(sharpness * x)
    c = np.full_like(q, p[1])
    f = p[0] * np.exp(-sharpness * x) if facing else np.zeros_like(q)
    total = f + c + r
    return f / total, c / total, r / total


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
    events = history_events(obs)
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
    fp, cp, rp = action_prob(q[None, :], frequencies, SLOPES[:, None], True, price)
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


def finish(result, memory):
    begin = time.perf_counter()
    memory['hands_played'] = memory.get('hands_played', 0) + 1
    last = memory.get('last')
    if last is None or last[0].hand_index != result.hand_index:
        return
    obs, action, cache = last
    # A final opponent call/fold isn't visible in another Observation.
    facing = action in (Action.RAISE_HALF, Action.RAISE_POT)
    if facing:
        response = 1 if result.went_to_showdown else 0
        context=2 if obs.to_call and obs.raises_this_street else 1
        memory['counts'][int(obs.street), context, response] += 1
    elif (action == Action.CHECK_CALL and obs.to_call == 0
          and (obs.is_button == (obs.street == Street.PREFLOP))
          and result.went_to_showdown):
        memory['counts'][int(obs.street), 0, 1] += 1
    if result.opp_hole and len(obs.board) >= 3:
        # Learn whether betting is related to card strength. A mixture keeps
        # uncertain reads conservative, rather than hard-classifying a bot.
        opp = np.asarray(result.opp_hole, dtype=np.int32)
        values = cache['values']
        actual = np.zeros((1, 4))
        actual[0, 0] = engine.preflop_quality(opp)
        for s, n in ((1, 3), (2, 4), (3, 5)):
            if len(obs.board) >= n:
                actual[0, s] = engine.score(opp, cache['board'][:n])
        actual_q = np.zeros((1, 4))
        for s in range(4):
            if s == 0 or len(obs.board) >= (0, 3, 4, 5)[s]:
                col = values[:, s]
                actual_q[0, s] = (np.sum(col < actual[0, s]) + .5 * np.sum(col == actual[0, s])) / len(col)
        actual_q[0, 1] = .78 * actual_q[0, 1] + .22 * actual_q[0, 0]
        actual_q[0, 2] = .90 * actual_q[0, 2] + .10 * actual_q[0, 0]
        combined_q = np.concatenate((cache['q'], actual_q), axis=0)
        likelihood = range_model.likelihoods(combined_q,memory['counts'],
                                             range_model.event_array(history_events(obs)),SLOPES)
        evidence = (np.log(np.maximum(1e-100, likelihood[:, -1]))
                    - np.log(np.maximum(1e-100, likelihood[:, :-1].mean(axis=1))))
        evidence -= evidence[0]
        posterior = memory['models'] * np.exp(np.clip(evidence, -.6, .6))
        posterior /= posterior.sum()
        memory['models'] = .985 * posterior + .015 / len(SLOPES)
    memory['last'] = None
    memory['cache'] = None
    memory['cpu'] += time.perf_counter() - begin
