"""Official server with an explicitly selected offline-research policy."""
import os
import uvicorn
import agent
from research_candidates import make

policy=make(os.environ.get('RANGERUNNER_POLICY','release'))
agent.new_half=policy.new_half
agent.choose_action=policy.choose_action
agent.on_hand_end=policy.on_hand_end

if __name__=='__main__':
    uvicorn.run(agent.app,host='127.0.0.1',port=int(os.environ.get('PORT','5008')),access_log=False)
