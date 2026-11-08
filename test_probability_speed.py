"""Speed changes must preserve the released probability and value bits."""
import numpy as np
import pytest
import range_model
import bet_ev
from opponents import model_451b as old_model
from opponents import bet_ev_451b as old_bet


@pytest.mark.parametrize('samples',[192,384,640,768,1280,4096])
def test_likelihoods_are_bit_identical_across_sizes_and_opportunity_masks(samples):
    rng=np.random.default_rng(801+samples);q=rng.random((samples,4))
    q[0]=0.;q[1]=1.
    counts=rng.uniform(.1,100,(4,3,3));counts[:,0,0]=0
    slopes=np.array([0.,8.,16.,-8.,-16.])
    events=range_model.event_array([(0,0,1,2,.25,1),(1,1,0,1,0.,1),
        (2,1,1,3,.33,1),(3,2,0,1,0.,1),(4,2,2,1,.2,0),(5,3,0,2,0.,1),(6,3,1,0,.3,1)])
    np.testing.assert_array_equal(range_model.likelihoods(q,counts,events,slopes),old_model.likelihoods(q,counts,events,slopes))


@pytest.mark.parametrize('raises,stack',[(0,60),(3,60),(0,10)])
def test_raise_values_preserve_the_exact_accumulation_result(raises,stack):
    rng=np.random.default_rng(955)
    for _ in range(30):
        n=97;q=rng.random(n);models=rng.dirichlet(np.ones(5));rows=rng.dirichlet(np.ones(n),5)
        outcomes=rng.choice([0.,.5,1.],n);equity=float((models@rows)@outcomes)
        args=(q,rows,models,outcomes,np.array([0.,8.,16.,-8.,-16.]),rng.uniform(.1,100,3),
              20,stack,60,0,0,raises,4,np.array([10,min(20,stack)]),equity)
        np.testing.assert_array_equal(bet_ev.raise_values(*args),old_bet.raise_values(*args))
