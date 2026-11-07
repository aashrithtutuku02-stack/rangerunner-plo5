"""Additional local sparring opponent: honest equity-based value bettor.

This is a test opponent, not the submitted strategy.
"""
import os
import numpy as np
import uvicorn

import agent
import fast_engine as engine
from game import Action, Street


def start(config, memory):
    memory.update(rng=np.uint64(0xABCDEF1234), key=None, equity=0.5)


def choose(obs, memory):
    key = (obs.hand_index, obs.hole_cards, obs.board)
    if key != memory['key']:
        hole = np.array(obs.hole_cards, dtype=np.int32)
        board = np.array(obs.board, dtype=np.int32)
        r = engine.simulate(hole, board, 1024, memory['rng'])
        memory['rng'] = np.uint64(r[4])
        memory['equity'] = float(r[2].mean())
        if obs.street == Street.PREFLOP:
            table_eq = engine.preflop_equity(hole)
            if table_eq >= 0:
                memory['equity'] = table_eq
        memory['key'] = key
    e = memory['equity']
    street = int(obs.street)
    price = obs.to_call / max(1, obs.pot + obs.to_call)
    premium = (0.07, 0.09, 0.08, 0.06)[street]
    if obs.to_call and e < price + premium:
        return Action.FOLD
    threshold = (0.55, 0.64, 0.68, 0.73)[street]
    if obs.to_call and obs.raises_this_street:
        threshold += 0.09
    if e > threshold and Action.RAISE_POT in obs.legal_actions:
        return Action.RAISE_POT
    return Action.CHECK_CALL


agent.AGENT_NAME = 'EquityValueReference'
agent.new_half = start
agent.choose_action = choose
agent.on_hand_end = lambda result, memory: None

if __name__ == '__main__':
    uvicorn.run(agent.app, host='0.0.0.0', port=int(os.environ.get('PORT', '5009')), access_log=False)
