"""Opt-in bluff experiments; agent.py retains the validated tournament policy."""
import os
import uvicorn
import agent
from research_candidates import make

name=os.environ.get('RANGERUNNER_POLICY','bluff-quarter')
if name not in ('bluff-quarter','bluff-half','bluff-pure'):
    raise ValueError('Choose bluff-quarter, bluff-half or bluff-pure')
policy=make(name)
agent.new_half=policy.new_half
agent.choose_action=policy.choose_action
agent.on_hand_end=policy.on_hand_end

if __name__=='__main__':
    uvicorn.run(agent.app,host='0.0.0.0',port=int(os.environ.get('PORT','5008')))
