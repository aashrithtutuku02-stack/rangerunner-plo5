import numpy as np
import pytest
from model_learning import regularize


@pytest.mark.parametrize('posterior',[[.08,.24,.48,.1,.1],[1.,0.,0.,0.,0.],[0.,0.,0.,.4,.6],[.001,.002,.003,.004,.99]])
def test_family_forgetting_preserves_probability_mass_and_nonzero_recovery(posterior):
    p=np.array(posterior);before=p.copy();mask=np.array([False,False,False,True,True])
    result=regularize(p,mask)
    assert np.isfinite(result).all() and (result>0).all()
    assert result.sum()==pytest.approx(1.,abs=1e-14)
    assert result[mask].sum()==pytest.approx(.985*(p[mask].sum()/p.sum())+.015*.2,abs=1e-14)
    np.testing.assert_array_equal(p,before)


def test_splitting_a_polarized_component_does_not_change_family_mass_or_value_models():
    one=regularize([.1,.3,.4,.2],[False,False,False,True])
    two=regularize([.1,.3,.4,.1,.1],[False,False,False,True,True])
    np.testing.assert_allclose(one[:3],two[:3],rtol=1e-14,atol=1e-16)
    assert one[3]==pytest.approx(two[3:].sum(),abs=1e-15)


def test_value_family_keeps_its_original_three_model_forgetting_rule():
    p=np.array([.08,.24,.48,.1,.1]);r=regularize(p,[False,False,False,True,True])
    np.testing.assert_allclose(r[:3]/r[:3].sum(),.985*np.array([.1,.3,.6])+.015/3,atol=1e-15)
    assert r[3:].sum()==pytest.approx(.2,abs=1e-15)
