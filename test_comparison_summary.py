import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('comparison_summary',Path(__file__).with_name('tools')/'summarize_comparison.py')
summary=importlib.util.module_from_spec(spec);spec.loader.exec_module(summary)


def test_shared_deals_are_clustered_instead_of_pretending_opponents_are_independent():
    rows=[dict(opponent=p,seed='s',delta=[1.,-1.],candidate=dict(paired=[1.,-1.]),
               baseline=dict(paired=[0.,0.]),sample_mode='fixed-default-counts',source_sha256={'strategy':'x'})
          for p in ['a','b']]
    result=summary.summarize(rows)
    assert result['independent_deal_clusters']==2
    assert result['paired_policy_observations']==4
    assert result['ci']==[-1.96,1.96]
    rows[1]['source_sha256']={'strategy':'different'}
    with pytest.raises(AssertionError):summary.summarize(rows)
