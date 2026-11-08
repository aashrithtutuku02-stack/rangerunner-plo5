"""Belief-state river best response to the learned opponent action model.

Every hero decision maximizes one expectation over its information set. Sampled
opponent cards never select a different hero action within that information set.
The bounded tree uses the referee's integer pot-limit sizes and raise cap.
"""
import numpy as np
from numba import njit
from range_model import intercept, sigmoid


@njit
def advance(state, action, big_blind):
    """Numeric river transition; result 0=continue, 1=showdown, 2=fold."""
    x=state.copy()
    p,s0,s1,b0,b1,raises,increment,turn,hacted,oacted,oraise,invest=x[:12]
    stack=s0 if turn==0 else s1
    other_stack=s1 if turn==0 else s0
    mine=b0 if turn==0 else b1
    theirs=b1 if turn==0 else b0
    call=max(0,theirs-mine)
    if action==0:return x,2
    if action==1:
        amount=min(call,stack)
        if turn==1 and call==0 and len(x)>12:x[12]=1
    else:
        target=theirs+(p+call)//2 if action==2 else theirs+p+call
        target=min(max(target,theirs+max(increment,big_blind)),theirs+p+call,mine+stack)
        amount=target-mine
        x[5]+=1;x[6]=target-theirs
        if turn==0:x[9]=0
        else:x[8]=0;x[10]=1
    x[0]+=amount
    if turn==0:
        x[1]-=amount;x[3]+=amount;x[8]=1;x[11]+=amount
    else:
        x[2]-=amount;x[4]+=amount;x[9]=1
    if x[8] and x[9] and x[3]==x[4]:return x,1
    x[7]=1-turn
    return x,0


@njit
def terminal_value(state, mass, outcomes, folded=False):
    value=0.
    for m in range(len(mass)):
        for i in range(len(outcomes)):
            if folded:
                payoff=-state[11] if state[7]==0 else state[0]-state[11]
            else:payoff=state[0]*outcomes[i]-state[11]
            value+=mass[m,i]*payoff
    return value


@njit
def legal(state, action, cap):
    turn=state[7]
    stack=state[1+turn];other=state[2-turn]
    call=max(0,state[4-turn]-state[3+turn])
    if action==0:return call>0
    if action==1:return True
    return state[5]<cap and stack>call and other>0


@njit
def response_mass(state, mass, q, counts, slopes, cap):
    facing=max(0,state[3]-state[4])
    context=0 if not facing else 2 if state[10] else 1
    if len(counts)>3:
        if not facing and state[8]:context=3
        elif facing and context==1 and len(state)>12 and state[12]:context=4
    f=counts[context,0] if facing else 0.
    c=counts[context,1];r=counts[context,2]
    price=min(state[2],facing)/max(1,state[0]+min(state[2],facing))
    if facing:
        f*=np.exp(3*(price-.28));c*=np.exp(-1.5*(price-.28))
    total=f+c+r;f/=total;c/=total;r/=total
    flatten=min(1.,4*(1-max(f,c,r)))
    can_raise=legal(state,2,cap)
    result=np.empty((3,len(mass),len(q)))
    for m in range(len(mass)):
        sharp=slopes[m]*flatten
        af=intercept(f,sharp);ar=intercept(r,sharp)
        for i in range(len(q)):
            x=min(1.,max(0.,q[i]))-.5
            pf=sigmoid(af-sharp*x) if facing and f>0 else 0.
            pr=sigmoid(ar+sharp*x) if r>0 else 0.
            pc=max(0.,1-pf-pr)
            if not can_raise:pc+=pr;pr=0.
            result[0,m,i]=mass[m,i]*pf
            result[1,m,i]=mass[m,i]*pc
            result[2,m,i]=mass[m,i]*pr
    return result,context


@njit
def search(state, mass, q, outcomes, counts, sizes, slopes, cap, big_blind, forced=-1):
    if state[7]==0:
        best=-np.inf
        for action in range(4):
            if (forced>=0 and action!=forced) or not legal(state,action,cap):continue
            child,terminal=advance(state,action,big_blind)
            if terminal:value=terminal_value(child,mass,outcomes,terminal==2)
            else:value=search(child,mass,q,outcomes,counts,sizes,slopes,cap,big_blind)
            best=max(best,value)
        return best
    branches,context=response_mass(state,mass,q,counts,slopes,cap)
    value=0.
    for action in range(4):
        if not legal(state,action,cap):continue
        probability=1.
        if action>=2:probability=sizes[context,action-2]/sizes[context].sum()
        branch=branches[min(action,2)]*probability
        if branch.sum()<1e-15:continue
        child,terminal=advance(state,action,big_blind)
        if terminal:value+=terminal_value(child,branch,outcomes,terminal==2)
        else:value+=search(child,branch,q,outcomes,counts,sizes,slopes,cap,big_blind)
    return value


def state_from_observation(obs, memory):
    # Last increment is exposed indirectly through the minimum legal raise.
    increment=obs.min_raise_to-obs.opp_bet
    history=[a for a in obs.action_history if a.street==obs.street]
    opp_raised=any(not a.is_me and int(a.action)>=2 for a in history)
    opp_acted=bool(history and not history[-1].is_me)
    opp_checked=any(not a.is_me and int(a.action)==1 and a.amount==0 for a in history)
    return np.array([obs.pot,obs.my_stack,obs.opp_stack,obs.my_bet,obs.opp_bet,
                     obs.raises_this_street,increment,0,0,int(opp_acted),int(opp_raised),0,int(opp_checked)],dtype=np.int64)


def action_values(obs, memory, cache, model_weights):
    state=state_from_observation(obs,memory)
    joint=memory['models'][:,None]*model_weights
    sizes=memory.get('sizes',np.tile(np.array([1.,3.]),(4,3,1)))[3]
    return np.array([search(state,joint,cache['q'][:,3],cache['outcomes'],
                            memory['counts'][3],sizes,np.array([0.,8.,16.]),
                            memory['config'].raise_cap,obs.big_blind,a) if a in obs.legal_actions else -np.inf
                     for a in range(4)])


def warmup():
    state=np.array([4,10,10,0,0,0,2,0,0,0,0,0],dtype=np.int64)
    q=np.zeros((2,4));q[:,3]=[.2,.8]
    # The live strength column is strided. Warm its exact layout before the
    # bank starts, rather than compiling that specialization on the first act.
    search(state,np.ones((3,2))/6,q[:,3],np.array([1.,0.]),
           np.array([[0.,7.,5.],[4.,6.,2.],[5.,5.,2.]]),np.ones((3,2)),np.array([0.,8.,16.]),4,2,1)
