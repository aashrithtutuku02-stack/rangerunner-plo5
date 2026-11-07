"""Probability calibration checked by numerical integration, not its formula."""
import numpy as np
import pytest
import calibrated_model as model


@pytest.mark.parametrize('counts',[[0.,9.,1.],[4.,5.,1.],[1.,2.,7.],[.01,9.98,.01]])
@pytest.mark.parametrize('slope',[0.,.01,8.,16.,32.])
def test_uniform_strength_marginals_match_observed_action_frequencies(counts,slope):
    q=(np.arange(20000)+.5)/20000
    counts=np.array(counts)
    p=model.action_prob(q,counts,slope,counts[0]>0,.28)
    np.testing.assert_allclose([v.mean() for v in p],counts/counts.sum(),atol=2e-7)
    np.testing.assert_allclose(p[0]+p[1]+p[2],1.,atol=1e-14)
    assert all(np.all((v>=0)&(v<=1)) for v in p)
    assert np.all(np.diff(p[0])<=1e-14)
    assert np.all(np.diff(p[2])>=-1e-14)


def test_compiled_model_and_python_probability_interface_agree():
    rng=np.random.default_rng(10817)
    q=rng.random((101,4));q[0]=0.;q[1]=1.
    counts=rng.uniform(.01,10,size=(4,3,3));counts[:,0,0]=0.
    slopes=np.array([0.,8.,16.])
    events=[(i,i%4,i%3,a,.01+.035*i) for i,a in enumerate([1,2,3,1,0,2,1,3])]
    events=[(i,s,1 if f==0 and a==0 else f,a,p) for i,s,f,a,p in events]
    expected=np.ones((3,len(q)))
    for i,s,f,a,p in events:
        expected*=model.action_prob(q[None,:,s],counts[s,f],slopes[:,None],f,p)[min(a,2)]
    actual=model.likelihoods(q,counts,model.event_array(events),slopes)
    np.testing.assert_allclose(actual,expected,rtol=1e-11,atol=1e-15)
