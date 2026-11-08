"""Joint chip-EV integration using the calibrated polarized/value likelihood family."""
import math
import numpy as np
from numba import njit
from range_model import parameters,probabilities


@njit
def raise_values(q,model_weights,models,outcomes,slopes,frequencies,
                 pot,my_stack,opp_stack,my_bet,opp_bet,raises,cap,targets,equity):
    values=np.full(2,-np.inf)
    for candidate in range(2):
        if targets[candidate]<0:continue
        if candidate==1 and targets[1]==targets[0]:values[1]=values[0];continue
        invest=targets[candidate]-my_bet;call=min(opp_stack,max(0,targets[candidate]-opp_bet))
        final=pot+invest+call;price=call/max(1,final)
        f=frequencies[0]*math.exp(3*(price-.28));c=frequencies[1]*math.exp(-1.5*(price-.28));r=frequencies[2]
        total=f+c+r;f/=total;c/=total;r/=total
        flatten=min(1.,4*(1-max(f,c,r)))
        can_raise=raises+1<cap and my_stack>invest and opp_stack>call
        ev=0.;reraise=0.
        for m in range(len(models)):
            params=parameters(f,r,slopes[m],flatten)
            if slopes[m]==0.:
                pf,pr=probabilities(.5,f,r,params)
                if not can_raise:pr=0.
                for i in range(len(q)):
                    joint=models[m]*model_weights[m,i]
                    ev+=joint*(pf*pot+(1-pf)*(outcomes[i]*final-invest));reraise+=joint*pr
                continue
            for i in range(len(q)):
                pf,pr=probabilities(q[i],f,r,params)
                if not can_raise:pr=0.
                joint=models[m]*model_weights[m,i]
                ev+=joint*(pf*pot+(1-pf)*(outcomes[i]*final-invest));reraise+=joint*pr
        behind=min(my_stack-invest,opp_stack-call)
        if behind>0:ev-=reraise*min(behind,final)*max(0.,.68-equity)
        values[candidate]=ev
    return values


def warmup():
    q=np.zeros((2,4))
    raise_values(q[:,3],np.ones((3,2))/2,np.ones(3)/3,np.array([0.,1.]),
                 np.array([0.,8.,-8.]),np.array([4.,6.,2.]),4,78,78,0,0,0,4,np.array([2,4]),.5)
