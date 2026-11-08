"""Independently written benchmark policies, sharing only card primitives.

These are local challengers, not externally developed elite bots. They do not
import strategy, range_model, bet_ev, or any released policy implementation.
"""
import random
import numpy as np
import fast_engine as cards
from game import Action,Street


class IndependentOpponent:
    def __init__(self,name):
        self.name=name
        assert name in ('independent-value','independent-polar','independent-adaptive')

    def new_half(self,config,memory):
        memory.clear()
        memory.update(config=config,rng=np.uint64(0xA0761D6478BD642F),
            coin=random.Random(28711),key=None,cache=None,pending=None,folds=2.,continues=6.)

    def _observe_response(self,obs,memory):
        pending=memory['pending']
        if pending is not None:
            hand,index=pending
            if hand==obs.hand_index and len(obs.action_history)>index+1:
                response=obs.action_history[index+1]
                if not response.is_me:memory['continues']+=1
            memory['pending']=None

    def choose_action(self,obs,memory):
        self._observe_response(obs,memory)
        key=(obs.hand_index,obs.hole_cards,obs.board)
        if key!=memory['key']:
            samples=cards.simulate(obs.hole_cards,obs.board,384,memory['rng'])
            memory['rng']=samples[-1]
            memory['cache']=(cards.percentiles(samples[1]),samples[2])
            memory['key']=key
        rank,outcomes=memory['cache']
        log_weights=np.zeros(len(outcomes))
        polar=self.name=='independent-polar'
        for record in obs.action_history:
            if record.is_me:continue
            q=np.clip(rank[:,int(record.street)],.005,.995)
            if record.action in (Action.RAISE_HALF,Action.RAISE_POT):
                tails=.3 if polar else .08 if self.name=='independent-adaptive' else .015
                density=(1-tails)*q**6+tails*(1-q)**6+.001
            elif record.amount:
                density=.2+q**1.5
            else:
                density=1-.45*q*q
            log_weights+=np.log(density)
        weights=np.exp(log_weights-log_weights.max());weights/=weights.sum()
        equity=float(weights@outcomes)
        if obs.street==Street.PREFLOP:
            uniform=cards.preflop_equity(obs.hole_cards)
            equity=np.clip(equity+uniform-float(outcomes.mean()),0.,1.)
        call=min(obs.to_call,obs.my_stack);price=call/max(1,obs.pot+call)
        discount=0. if obs.street==Street.RIVER or obs.opp_stack==0 or call==obs.my_stack else .025
        value=(equity-discount)*(obs.pot+call)-call
        selected=Action.FOLD if call and value<0 else Action.CHECK_CALL
        best=max(0.,value) if call else value
        q=rank[:,int(obs.street)]
        response_n=memory['folds']+memory['continues']
        fold_rate=memory['folds']/response_n
        for action in (Action.RAISE_HALF,Action.RAISE_POT):
            if action not in obs.legal_actions:continue
            invest=obs.raise_to[action]-obs.my_bet
            reply=min(obs.opp_stack,max(0,obs.raise_to[action]-obs.opp_bet))
            total=obs.pot+invest+reply
            threshold=np.clip(fold_rate+1.1*(reply/max(1,total)-.25),.03,.8)
            fold_probability=1/(1+np.exp(12*(q-threshold)))
            ev=float(weights@(fold_probability*obs.pot+(1-fold_probability)*(outcomes*total-invest)))
            if obs.my_stack>invest and obs.opp_stack>reply:ev-=.08*total*max(0.,.65-equity)
            if ev>best+.025*obs.pot+.1:selected=action;best=ev
        coin=memory['coin']
        if polar:
            threshold=.56 if obs.street==Street.PREFLOP else .72 if obs.to_call else .65
            bluff_chance=.12 if obs.street==Street.PREFLOP else .38
            bluff=equity<(.46 if obs.street==Street.PREFLOP else .30) and coin.random()<bluff_chance
            if equity>threshold or bluff:
                if Action.RAISE_POT in obs.legal_actions:selected=Action.RAISE_POT
        if self.name=='independent-adaptive':
            # Attack a conservatively estimated tendency to fold to bets.
            error=(fold_rate*(1-fold_rate)/response_n)**.5
            if response_n>24 and fold_rate-error>.42 and equity<.45:
                if Action.RAISE_HALF in obs.legal_actions:selected=Action.RAISE_HALF
            if not obs.to_call and equity>.85 and coin.random()<.25:selected=Action.CHECK_CALL
        if selected in (Action.RAISE_HALF,Action.RAISE_POT):
            memory['pending']=(obs.hand_index,len(obs.action_history))
        assert selected in obs.legal_actions
        return selected

    def on_hand_end(self,result,memory):
        pending=memory['pending']
        if pending is not None and pending[0]==result.hand_index:
            if not result.went_to_showdown and result.winner=='me':memory['folds']+=1
            else:memory['continues']+=1
        memory['pending']=None;memory['key']=None;memory['cache']=None
