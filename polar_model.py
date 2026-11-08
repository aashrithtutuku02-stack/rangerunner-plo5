"""Calibrated value and two-tail opponent likelihoods, initially for research.

Positive slopes retain the released ordered model. A negative slope denotes a
polarized model: fold probability still decreases with strength, while raises
target both tails of the conditional continuing-strength distribution.
"""
import math
import numpy as np
from numba import njit


def event_array(events):
    result=np.ones((len(events),6),dtype=np.float64)
    for i,event in enumerate(events):result[i,:len(event)]=event
    return result


@njit
def intercept(probability,sharpness):
    p=min(1-1e-12,max(1e-12,probability))
    if sharpness<1e-7:return math.log(p/(1-p))
    return math.log(math.expm1(sharpness*p))-math.log(-math.expm1(sharpness*(p-1)))-sharpness/2


@njit
def sigmoid(x):
    if x>=0:return 1/(1+math.exp(-x))
    e=math.exp(x);return e/(1+e)


@njit
def softplus(x):
    return x+math.log1p(math.exp(-x)) if x>0 else math.log1p(math.exp(x))


@njit
def parameters(f,r,slope,flatten):
    sharp=abs(slope)*flatten;polarized=slope<0
    af=intercept(f,sharp)
    rate=r/max(1e-12,1-f) if polarized else r
    return af,intercept(rate,sharp),sharp,softplus(af+sharp/2),polarized


@njit
def probabilities(rank,f,r,params):
    af,ar,sharp,upper,polarized=params
    q=min(1.,max(0.,rank));x=q-.5
    pf=sigmoid(af-sharp*x) if f>0 else 0.
    if not polarized:
        pr=sigmoid(ar+sharp*x) if r>0 else 0.
    else:
        integral=f*q if sharp<1e-7 else (upper-softplus(af+sharp/2-sharp*q))/sharp
        if f==0:integral=0.
        conditional=min(1.,max(0.,(q-integral)/max(1e-12,1-f)))
        tail=2*abs(conditional-.5)
        pr=(1-pf)*sigmoid(ar+sharp*(tail-.5)) if r>0 else 0.
    return pf,pr


@njit
def likelihoods(q,counts,events,slopes):
    out=np.ones((len(slopes),len(q)))
    for ev in events:
        s=int(ev[1]);context=int(ev[2]);action=min(2,int(ev[3]));price=ev[4]
        f=counts[s,context,0] if context else 0.
        c=counts[s,context,1];r=counts[s,context,2]
        if context:f*=math.exp(3*(price-.28));c*=math.exp(-1.5*(price-.28))
        total=f+c+r;f/=total;c/=total;r/=total
        flatten=min(1.,4*(1-max(f,c,r)))
        for m in range(len(slopes)):
            params=parameters(f,r,slopes[m],flatten)
            for j in range(len(q)):
                pf,pr=probabilities(q[j,s],f,r,params)
                pc=max(0.,1-pf-pr)
                if len(ev)>5 and ev[5]==0:pc+=pr;pr=0.
                out[m,j]*=pf if action==0 else pc if action==1 else pr
    return out


def action_prob(q,frequencies,slope,facing,price=.25,can_raise=True):
    p=np.asarray(frequencies,dtype=float).copy()
    if not facing:p[0]=0
    else:p[0]*=math.exp(3*(price-.28));p[1]*=math.exp(-1.5*(price-.28))
    p/=p.sum();slope=np.asarray(slope);sharp=abs(slope)*min(1.,4*(1-float(p.max())))
    flat=sharp.ravel()
    af=np.array([intercept(p[0],s) for s in flat]).reshape(sharp.shape)
    rates=np.where(slope<0,p[2]/max(1e-12,1-p[0]),p[2])
    ar=np.array([intercept(r,s) for r,s in zip(rates.ravel(),flat)]).reshape(sharp.shape)
    rank=np.clip(q,0.,1.);x=rank-.5
    f=1/(1+np.exp(-(af-sharp*x))) if facing and p[0]>0 else np.zeros_like(rank)
    value=1/(1+np.exp(-(ar+sharp*x)))
    integral=(np.logaddexp(0.,af+sharp/2)-np.logaddexp(0.,af+sharp/2-sharp*rank))/np.maximum(sharp,1e-7)
    integral=np.where(sharp<1e-7,p[0]*rank,integral)
    if p[0]==0:integral=np.zeros_like(integral)
    conditional=np.clip((rank-integral)/max(1e-12,1-p[0]),0.,1.)
    polar=(1-f)/(1+np.exp(-(ar+sharp*(2*abs(conditional-.5)-.5))))
    r=np.where(slope<0,polar,value) if p[2]>0 else np.zeros_like(value)
    c=np.maximum(0.,1-f-r)
    if not can_raise:c=c+r;r=np.zeros_like(r)
    return f,c,r


def warmup():
    likelihoods(np.zeros((2,4)),np.ones((4,3,3)),event_array([(0,0,1,1,.28,1)]),np.array([0.,8.,-8.]))
