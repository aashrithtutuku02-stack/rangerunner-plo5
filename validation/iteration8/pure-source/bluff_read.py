"""Price-aware fold evidence and mixed opening bluffs; no hidden-card input."""
import hashlib
import math
from game import Action


def observe(windows,event):
    _,street,context,action,price=event[:5]
    # A small-blind completion/fold precedes any voluntary hero bet and
    # samples an unselected starting range. Do not treat it as a bet response.
    if context!=1 or (street==0 and int(event[0])==0):return windows
    group=int(street!=0);updated=list(windows)
    updated[group]=(updated[group]+((float(price),int(action==0)),))[-128:]
    return tuple(updated)


def fold_bound(window,price):
    eligible=[fold for observed,fold in window if observed<=price+.015]
    n=len(eligible)
    if n<16:return 0.
    p=sum(eligible)/n;z=1.645;z2=z*z
    return (p+z2/(2*n)-z*math.sqrt(p*(1-p)/n+z2/(4*n*n)))/(1+z2/n)


def coin(obs):
    cards=tuple(sorted(obs.hole_cards))+tuple(sorted(obs.board[:3]))+tuple(obs.board[3:])
    frame=bytes(cards)+int(obs.hand_index).to_bytes(8,'little')+bytes([int(obs.street),len(obs.action_history)])
    return int.from_bytes(hashlib.blake2b(frame,digest_size=8,person=b'RR-bluff').digest(),'little')/2**64


def choose(obs,memory,equity,passive_ev,action,frequency=.25):
    memory['bluff_override']=False
    if action!=Action.CHECK_CALL or obs.to_call or equity>=.45 or coin(obs)>=frequency:return action
    best=passive_ev+.025*obs.pot+.08
    window=memory['fold_windows'][int(int(obs.street)!=0)]
    for candidate in (Action.RAISE_HALF,Action.RAISE_POT):
        if candidate not in obs.legal_actions:continue
        invest=obs.raise_to[candidate]-obs.my_bet
        call=min(obs.opp_stack,max(0,obs.raise_to[candidate]-obs.opp_bet))
        final=obs.pot+invest+call;fold=fold_bound(window,call/max(1,final))
        if fold<.42:continue
        # A conservative equity haircut for the stronger continuing range.
        # This remains an approximate score, not a guaranteed payoff bound.
        score=fold*obs.pot+(1-fold)*(.5*equity*final-invest)
        if score>best:action=candidate;best=score
    memory['bluff_override']=action!=Action.CHECK_CALL
    return action
