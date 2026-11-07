"""Compile small Bayesian likelihood loops once, before the server starts."""
import math
import numpy as np
from numba import njit


@njit
def likelihoods(q,counts,events,slopes):
    out=np.ones((len(slopes),len(q)),dtype=np.float64)
    for e in range(len(events)):
        street=int(events[e,1]);facing=int(events[e,2]);action=min(2,int(events[e,3]))
        price=events[e,4]
        p0=counts[street,facing,0];p1=counts[street,facing,1];p2=counts[street,facing,2]
        total=p0+p1+p2;p0/=total;p1/=total;p2/=total
        if facing:
            p0*=math.exp(3.0*(price-.28));p1*=math.exp(-1.5*(price-.28))
            total=p0+p1+p2;p0/=total;p1/=total;p2/=total
        flatten=min(1.0,4.0*(1.0-max(p0,p1,p2)))
        for model in range(len(slopes)):
            sharp=slopes[model]*flatten
            if sharp==0:
                prob=(p0 if facing else 0.0) if action==0 else p1 if action==1 else p2
                prob/=p0+p1+p2 if facing else p1+p2
                for j in range(len(q)):out[model,j]*=prob
                continue
            for j in range(len(q)):
                x=min(.99,max(.01,q[j,street]))-.5
                r=p2*math.exp(sharp*x)
                f=p0*math.exp(-sharp*x) if facing else 0.0
                total=f+p1+r
                prob=f if action==0 else p1 if action==1 else r
                out[model,j]*=prob/total
    return out


def event_array(events):
    return np.asarray(events,dtype=np.float64).reshape((-1,5))


def warmup():
    likelihoods(np.zeros((2,4)),np.ones((4,2,3)),
                np.array([[0.,0.,0.,1.,0.]]),np.array([0.,8.,16.]))
