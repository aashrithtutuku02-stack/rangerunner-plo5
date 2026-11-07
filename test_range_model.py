import numpy as np
import range_model
import strategy


def test_compiled_likelihood_matches_python_formula_for_all_action_classes():
    rng=np.random.default_rng(711)
    q=rng.random((97,4))
    q[0]=0;q[1]=1
    counts=rng.uniform(.1,20,size=(4,2,3))
    counts[:,0,0]=0
    slopes=np.array([0.,4.,8.,16.,32.])
    events=[(i,i%4,int(i%3!=0),a,.03+.03*i) for i,a in enumerate([1,2,0,3,1,2,1,0,3])]
    # Folds only occur facing a bet.
    events=[(i,s,int(f or a==0),a,p) for i,s,f,a,p in events]
    expected=np.ones((len(slopes),len(q)))
    for i,s,f,a,p in events:
        expected*=strategy.action_prob(q[None,:,s],counts[s,f],slopes[:,None],f,p)[min(a,2)]
    actual=range_model.likelihoods(q,counts,range_model.event_array(events),slopes)
    np.testing.assert_allclose(actual,expected,rtol=1e-12,atol=1e-15)


def test_empty_history_is_uniform_for_every_model():
    q=np.zeros((8,4));counts=np.ones((4,2,3));slopes=np.array([0.,8.,16.])
    np.testing.assert_array_equal(range_model.likelihoods(q,counts,range_model.event_array([]),slopes),np.ones((3,8)))
