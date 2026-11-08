"""Compile raise-value integration without allocating response arrays."""
import math
import numpy as np
from numba import njit
from range_model import intercept,sigmoid


@njit
def raise_values(q, model_weights, models, outcomes, slopes, frequencies,
                 pot, my_stack, opp_stack, my_bet, opp_bet, raises, cap, targets, equity):
    values=np.full(2,-np.inf)
    for candidate in range(2):
        if targets[candidate]<0:continue
        if candidate==1 and targets[1]==targets[0]:
            values[1]=values[0]
            continue
        invest=targets[candidate]-my_bet
        call=min(opp_stack,max(0,targets[candidate]-opp_bet))
        final_pot=pot+invest+call
        price=call/max(1,final_pot)
        f=frequencies[0]*math.exp(3*(price-.28))
        c=frequencies[1]*math.exp(-1.5*(price-.28))
        r=frequencies[2]
        total=f+c+r;f/=total;c/=total;r/=total
        flatten=min(1.,4*(1-max(f,c,r)))
        can_raise=raises+1<cap and my_stack>invest and opp_stack>call
        ev=0.;reraise=0.
        for m in range(len(models)):
            sharp=slopes[m]*flatten
            af=intercept(f,sharp);ar=intercept(r,sharp)
            for i in range(len(q)):
                x=min(1.,max(0.,q[i]))-.5
                pf=sigmoid(af-sharp*x) if f>0 else 0.
                pr=sigmoid(ar+sharp*x) if can_raise and r>0 else 0.
                joint=models[m]*model_weights[m,i]
                showdown=outcomes[i]*final_pot-invest
                ev+=joint*(pf*pot+(1-pf)*showdown)
                reraise+=joint*pr
        behind=min(my_stack-invest,opp_stack-call)
        if behind>0:ev-=reraise*min(behind,final_pot)*max(0.,.68-equity)
        values[candidate]=ev
    return values


def warmup():
    q=np.zeros((2,4))
    raise_values(q[:,3],np.ones((3,2))/2,np.ones(3)/3,np.array([0.,1.]),
                 np.array([0.,8.,16.]),np.array([4.,6.,2.]),4,78,78,0,0,0,4,np.array([2,4]),.5)
