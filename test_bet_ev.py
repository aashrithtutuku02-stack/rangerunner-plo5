import numpy as np
from types import SimpleNamespace
import pytest

import strategy
import bet_ev
from game import AgentConfig


@pytest.mark.parametrize('cap_reached,allin',[(False,False),(True,False),(False,True)])
def test_compiled_raise_values_match_existing_joint_posterior_formula(cap_reached,allin):
    rng=np.random.default_rng(71)
    for _ in range(30):
        memory={};strategy.initialize(AgentConfig(),memory)
        memory['models']=rng.dirichlet(np.ones(3))
        memory['counts'][3,1]=rng.uniform(.1,100,3)
        q=rng.random((37,4));models=rng.dirichlet(np.ones(37),3)
        weights=memory['models']@models
        outcomes=rng.choice([0.,.5,1.],37);equity=float(weights@outcomes)
        obs=SimpleNamespace(street=3,to_call=0,raises_this_street=3 if cap_reached else 1,
                            my_stack=20 if allin else 60,opp_stack=60,my_bet=0,opp_bet=0,pot=40)
        targets=np.array([20,20 if allin else 40])
        actual=bet_ev.raise_values(q[:,3],models,memory['models'],outcomes,strategy.SLOPES,
                    memory['counts'][3,1],obs.pot,obs.my_stack,obs.opp_stack,obs.my_bet,obs.opp_bet,
                    obs.raises_this_street,4,targets,equity)
        for i,target in enumerate(targets):
            invest=target;call=target;final=obs.pot+invest+call
            f,r=strategy.response_prob(obs,memory,{'q':q},invest,call/final,models)
            expected=float(weights@(f*obs.pot+(1-f)*(outcomes*final-invest)))
            behind=min(obs.my_stack-invest,obs.opp_stack-call)
            if behind>0:expected-=float(weights@r)*min(behind,final)*max(0.,.68-equity)
            assert actual[i]==pytest.approx(expected,abs=1e-11)
