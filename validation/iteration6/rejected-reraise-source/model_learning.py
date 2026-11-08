"""Forget opponent-model evidence within families and between families.

Adding more polarized components must not silently change the family's long-run
forgetting target from its chosen 20% prior to a uniform model-count fraction.
"""
import numpy as np


def regularize(posterior,polarized,forget=.015,polar_prior=.2):
    p=np.array(posterior,dtype=float,copy=True)
    mask=np.asarray(polarized,dtype=bool)
    p/=p.sum()
    if not mask.any() or mask.all():return (1-forget)*p+forget/len(p)
    mass=float(p[mask].sum())
    updated_mass=(1-forget)*mass+forget*polar_prior
    result=np.empty_like(p)
    for family,total in ((mask,updated_mass),(~mask,1-updated_mass)):
        n=int(family.sum());part=p[family];denom=float(part.sum())
        conditional=part/denom if denom>0 else np.ones(n)/n
        result[family]=total*((1-forget)*conditional+forget/n)
    return result
