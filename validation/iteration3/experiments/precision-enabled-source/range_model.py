"""Ordered action likelihoods calibrated over uniform strength percentiles."""
import math
import numpy as np
from numba import njit

def event_array(events):
    result=np.ones((len(events),6),dtype=np.float64)
    for i,event in enumerate(events):
        result[i,:len(event)]=event
    return result


@njit
def intercept(probability,sharpness):
    """Logit intercept whose integral over uniform rank equals probability."""
    p=min(1-1e-12,max(1e-12,probability))
    if sharpness<1e-7:return math.log(p/(1-p))
    return (math.log(math.expm1(sharpness*p))
            - math.log(-math.expm1(sharpness*(p-1))) - sharpness/2)


@njit
def sigmoid(x):
    if x>=0:return 1/(1+math.exp(-x))
    e=math.exp(x);return e/(1+e)


@njit
def likelihoods(q,counts,events,slopes):
    out=np.ones((len(slopes),len(q)))
    for ev in events:
        s=int(ev[1]);facing=int(ev[2]);action=min(2,int(ev[3]));price=ev[4]
        f=counts[s,facing,0] if facing else 0.0
        c=counts[s,facing,1];r=counts[s,facing,2]
        if facing:f*=math.exp(3*(price-.28));c*=math.exp(-1.5*(price-.28))
        total=f+c+r;f/=total;c/=total;r/=total
        flatten=min(1.,4*(1-max(f,c,r)))
        for m in range(len(slopes)):
            sharp=slopes[m]*flatten
            af=intercept(f,sharp);ar=intercept(r,sharp)
            for j in range(len(q)):
                x=min(1.,max(0.,q[j,s]))-.5
                pf=sigmoid(af-sharp*x) if facing and f>0 else 0.
                pr=sigmoid(ar+sharp*x) if r>0 else 0.
                pc=max(0.,1-pf-pr)
                if len(ev)>5 and ev[5]==0:
                    pc+=pr;pr=0.
                out[m,j]*=pf if action==0 else pc if action==1 else pr
    return out


def action_prob(q,frequencies,slope,facing,price=.25,can_raise=True):
    p=np.asarray(frequencies,dtype=float).copy()
    if not facing:p[0]=0
    else:
        p[0]*=math.exp(3*(price-.28));p[1]*=math.exp(-1.5*(price-.28))
    p/=p.sum()
    sharp=np.asarray(slope)*min(1.,4*(1-float(p.max())))
    flat=sharp.ravel()
    af=np.array([intercept(p[0],v) for v in flat]).reshape(sharp.shape)
    ar=np.array([intercept(p[2],v) for v in flat]).reshape(sharp.shape)
    x=np.clip(q,0.,1.)-.5
    f=1/(1+np.exp(-(af-sharp*x))) if facing and p[0]>0 else np.zeros_like(q)
    r=1/(1+np.exp(-(ar+sharp*x))) if p[2]>0 else np.zeros_like(q)
    c=np.maximum(0.,1-f-r)
    if not can_raise:c=c+r;r=np.zeros_like(r)
    return f,c,r


def warmup():
    likelihoods(np.zeros((2,4)),np.ones((4,3,3)),np.array([[0.,0.,1.,1.,.28]]),np.array([0.,8.,16.]))
