"""Separate probing after a check from opening bets and check-raises."""
import numpy as np
from game import Street,Action


def refine_events(obs, events):
    hero_checked=False;opponent_checked=False
    contexts={}
    for idx,a in enumerate(obs.action_history):
        if a.street!=Street.RIVER:continue
        if not a.is_me:
            contexts[idx]=(hero_checked,opponent_checked)
        if a.action==Action.CHECK_CALL and a.amount==0:
            if a.is_me:hero_checked=True
            else:opponent_checked=True
    result=[]
    for event in events:
        idx,s,context,action,price,available=event
        if s==3:
            mine,theirs=contexts[idx]
            if context==0 and mine:context=3
            elif context==1 and theirs:context=4
        result.append((idx,s,context,action,price,available))
    return result


def response_context(obs):
    if obs.to_call and obs.raises_this_street:return 2
    if obs.street==Street.RIVER and any(not a.is_me and a.street==obs.street and
            a.action==Action.CHECK_CALL and a.amount==0 for a in getattr(obs,'action_history',())):return 4
    return 1


def shrink_counts(counts):
    """Use twelve observations of the broader read as a contextual prior.

    Parent buckets contain all opportunities, including their child context.
    Child buckets contain a fixed startup prior plus their own observations.
    Replacing that fixed prior retains broader learning when child data are rare.
    """
    result=counts.copy()
    for child,parent,prior in ((3,0,(0.,8.,4.)),(4,1,(5.,5.,2.))):
        base=counts[3,parent]
        result[3,child]=np.maximum(0.,counts[3,child]-prior)+12*base/base.sum()
    return result
