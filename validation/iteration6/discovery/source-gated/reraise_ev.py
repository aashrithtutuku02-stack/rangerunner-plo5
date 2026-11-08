"""One opponent re-raise, followed by one information-set fold/call choice.

This replaces an unconditioned risk penalty with the sampled raise-branch
equity. It assumes subsequent streets check down and does not solve poker.
"""
import math
import numpy as np
from numba import njit
from range_model import parameters,probabilities


@njit
def reply_targets(pot,my_stack,opp_stack,my_bet,opp_bet,target):
    invest=target-my_bet
    call=min(opp_stack,max(0,target-opp_bet))
    after=pot+invest
    increment=target-max(my_bet,opp_bet)
    minimum=target+increment
    maximum=target+after+call
    cap=opp_bet+opp_stack
    return np.array([min(max(target+(after+call)//2,minimum),maximum,cap),
                     min(maximum,cap)],dtype=np.int64)


@njit
def raise_values(q,model_weights,models,outcomes,slopes,frequencies,
                 pot,my_stack,opp_stack,my_bet,opp_bet,raises,cap,targets,equity,blend=1.):
    values=np.full(2,-np.inf)
    for candidate in range(2):
        if targets[candidate]<0:continue
        if candidate==1 and targets[1]==targets[0]:values[1]=values[0];continue
        target=targets[candidate];invest=target-my_bet
        call=min(opp_stack,max(0,target-opp_bet));final=pot+invest+call
        price=call/max(1,final)
        f=frequencies[0]*math.exp(3*(price-.28));c=frequencies[1]*math.exp(-1.5*(price-.28));r=frequencies[2]
        total=f+c+r;f/=total;c/=total;r/=total
        flatten=min(1.,4*(1-max(f,c,r)))
        available=raises+1<cap and my_stack>invest and opp_stack>call
        base=0.;raise_mass=0.;raise_wins=0.
        for m in range(len(models)):
            params=parameters(f,r,slopes[m],flatten)
            for i in range(len(q)):
                pf,pr=probabilities(q[i],f,r,params)
                if not available:pr=0.
                joint=models[m]*model_weights[m,i]
                base+=joint*(pf*pot+(1-pf)*(outcomes[i]*final-invest))
                raise_mass+=joint*pr;raise_wins+=joint*pr*outcomes[i]
        behind=min(my_stack-invest,opp_stack-call)
        old=base
        if behind>0:old-=raise_mass*min(behind,final)*max(0.,.68-equity)
        if not available or raise_mass<=1e-100:
            values[candidate]=base;continue
        branches=reply_targets(pot,my_stack,opp_stack,my_bet,opp_bet,target)
        continuation=0.
        for size in range(2):
            extra=min(my_stack-invest,max(0,branches[size]-target))
            # Uncalled excess is returned to the opponent. Both matched
            # contributions therefore increase the called pot by 2*extra.
            called=raise_wins*(final+2*extra)-raise_mass*(invest+extra)
            folded=-raise_mass*invest
            # Crucially maximize AFTER integrating all hidden hands/models.
            # A sampled opponent hand must not choose a private hero action.
            continuation+=(.25 if size==0 else .75)*max(folded,called)
        original_raise_branch=raise_wins*final-raise_mass*invest
        one_step=base-original_raise_branch+continuation
        values[candidate]=(1-blend)*old+blend*one_step
    return values


def warmup():
    q=np.zeros((2,4))
    raise_values(q[:,3],np.ones((5,2))/2,np.ones(5)/5,np.array([0.,1.]),
                 np.array([0.,8.,16.,-8.,-16.]),np.array([4.,6.,2.]),4,78,78,0,0,0,4,np.array([2,4]),.5,1.)
