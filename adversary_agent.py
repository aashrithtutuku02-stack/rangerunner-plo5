"""Serve one local adversary through the unchanged tournament protocol."""
import os
import uvicorn
import agent
from adversaries import Opponent

opponent=Opponent(os.environ.get('OPPONENT_PROFILE','balanced'))
agent.AGENT_NAME='Adversary-'+opponent.name
agent.new_half=opponent.new_half
agent.choose_action=opponent.choose_action
agent.on_hand_end=opponent.on_hand_end

if __name__=='__main__':
    uvicorn.run(agent.app,host='0.0.0.0',port=int(os.environ.get('PORT','5009')),access_log=False)
