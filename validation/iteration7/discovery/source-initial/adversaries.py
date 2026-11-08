"""Local-only sparring opponents. Every policy sees only its Observation.

These are deliberately diverse stress opponents, not claims about the best
possible strategy or independent tournament competitors.
"""
import math
import random
import importlib.util
import json
from pathlib import Path
import numpy as np

import fast_engine as engine
from game import Action, Street

_cases_path=Path(__file__).with_name('adversary_cases.json')
CASES={case['name']:case['params'] for case in json.loads(_cases_path.read_text())} if _cases_path.exists() else {}


PROFILES = {
    'nit': dict(value=.82, raise_value=.91, call_extra=.17, bluff=.0),
    'tight': dict(value=.69, raise_value=.82, call_extra=.08, bluff=.04),
    'balanced': dict(value=.60, raise_value=.76, call_extra=.06, bluff=.12),
    'loose': dict(value=.53, raise_value=.66, call_extra=.015, bluff=.23),
    'maniac': dict(value=.47, raise_value=.58, call_extra=-.035, bluff=.48),
    'trapper': dict(value=.66, raise_value=.77, call_extra=.055, bluff=.07, trap=True),
    'checkraise': dict(value=.62, raise_value=.71, call_extra=.06, bluff=.10, checkraise=True),
    'polarized': dict(value=.77, raise_value=.86, call_extra=.07, bluff=.24),
    'smallball': dict(value=.57, raise_value=.72, call_extra=.07, bluff=.17, half=True),
    'overfolder': dict(value=.72, raise_value=.87, call_extra=.25, bluff=.01),
    'bluffer': dict(value=.72, raise_value=.81, call_extra=.10, bluff=.65),
    'sticky': dict(value=.59, raise_value=.79, call_extra=-.08, bluff=.07),
}


class Opponent:
    def __init__(self, name, params=None):
        self.name = name
        self.params = params if params is not None else CASES.get(name)
        self.range_policy = None
        if name.startswith('independent-'):
            from independent_opponents import IndependentOpponent
            self.range_policy=None
            self.independent=IndependentOpponent(name)
        elif name=='release-9efa':
            from opponents import release_9efa
            self.range_policy=release_9efa
        elif name=='release-451b':
            from opponents import release_451b
            self.range_policy=release_451b
        elif name=='release-52c5':
            from opponents import release_52c5
            self.range_policy=release_52c5
        elif name=='release-f452':
            from opponents import release_f452
            self.range_policy=release_f452
        elif name=='release-b15a':
            from opponents import release_b15a
            self.range_policy=release_b15a
        elif name=='incumbent':
            from opponents import incumbent_36ba
            self.range_policy=incumbent_36ba
        elif name in ('range-aware','range-tight','range-flat'):
            spec=importlib.util.spec_from_file_location('challenger_'+name.replace('-','_'),
                                                       Path(__file__).with_name('reference_range.py'))
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            if name=='range-tight':module.SLOPES=np.array([0.,8.,16.])
            if name=='range-flat':module.SLOPES=np.array([0.,0.,0.])
            self.range_policy=module

    def new_half(self, config, memory):
        if hasattr(self,'independent'):
            return self.independent.new_half(config,memory)
        if self.range_policy:
            self.range_policy.initialize(config,memory)
            if self.name=='range-tight':memory['models']=np.array([.1,.3,.6])
            return
        memory.update(rng=random.Random(9127), state=np.uint64(0x2187A9B1C3),
                      key=None, eq=.5, seen=0, faced=0, folds=0, last=None)

    def choose_action(self, obs, memory):
        if hasattr(self,'independent'):
            return self.independent.choose_action(obs,memory)
        if self.range_policy:
            return self.range_policy.decide(obs,memory)
        legal = obs.legal_actions
        if self.name == 'fold':
            return Action.FOLD if obs.to_call else Action.CHECK_CALL
        if self.name == 'call':
            return Action.CHECK_CALL
        if self.name == 'pot':
            return Action.RAISE_POT if Action.RAISE_POT in legal else Action.CHECK_CALL
        if self.name == 'half':
            return Action.RAISE_HALF if Action.RAISE_HALF in legal else Action.CHECK_CALL
        if self.name == 'random':
            return memory['rng'].choice(legal)
        profile = self.params or PROFILES.get(self.name, PROFILES['balanced'])
        if self.name == 'switcher':
            profile = PROFILES[('nit','maniac','trapper','bluffer')[(obs.hand_index//100)%4]]
        if self.name == 'oscillating':
            profile = PROFILES[('nit','bluffer','checkraise','maniac')[(obs.hand_index//25)%4]]
        if self.name == 'opportunist':
            profile=dict(PROFILES['balanced'])
            checked=any(not a.is_me and a.street==obs.street and
                        a.action==Action.CHECK_CALL and a.amount==0 for a in obs.action_history)
            if checked and obs.street!=Street.PREFLOP:
                profile['bluff']=.95
        key = (obs.hand_index, obs.hole_cards, obs.board)
        if memory['key'] != key:
            hole = np.asarray(obs.hole_cards, dtype=np.int32)
            board = np.asarray(obs.board, dtype=np.int32)
            if not obs.board:
                eq = engine.preflop_equity(hole)
            else:
                r = engine.simulate(hole, board, 512, memory['state'])
                memory['state'] = np.uint64(r[-1])
                eq = float(r[2].mean())
            memory.update(key=key, eq=eq)
        eq = memory['eq']
        price = min(obs.to_call, obs.my_stack)/max(1, obs.pot+min(obs.to_call,obs.my_stack))
        pf = obs.street == Street.PREFLOP
        # Preflop equities occupy a much narrower band than river equities.
        value = .5+(profile['value']-.5)*(.38 if pf else 1)
        raising = .5+(profile['raise_value']-.5)*(.38 if pf else 1)
        bluff = profile['bluff'] * (.40 if pf else 1)
        strength = raising if obs.to_call and obs.raises_this_street else value
        good = eq > strength
        weak_bluff = eq < .42 and memory['rng'].random() < bluff
        if profile.get('trap') and eq > .80 and obs.street < Street.RIVER and not obs.to_call:
            good = False
        if profile.get('checkraise') and not obs.to_call and not obs.is_button and not pf:
            good = False
        if good or weak_bluff:
            bet = Action.RAISE_HALF if profile.get('half') else Action.RAISE_POT
            if bet in legal:
                return bet
        # Avoid pretending a strong preflop selection is a random-hand range.
        opp_raises = sum(not a.is_me and a.action in (Action.RAISE_POT,Action.RAISE_HALF)
                         for a in obs.action_history)
        premium = profile['call_extra'] + min(.15, .035*max(0,opp_raises-1))
        if obs.to_call and eq < price+premium:
            return Action.FOLD
        return Action.CHECK_CALL

    def on_hand_end(self, result, memory):
        if hasattr(self,'independent'):
            return self.independent.on_hand_end(result,memory)
        if self.range_policy:self.range_policy.finish(result,memory)


def names():
    return ['fold','call','pot','half','random',*PROFILES,'switcher','incumbent','release-b15a','release-f452',
            'range-aware','range-tight','range-flat','opportunist','oscillating','release-52c5',
            'independent-value','independent-polar','independent-adaptive','release-451b','release-9efa']
