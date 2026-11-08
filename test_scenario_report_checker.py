import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('scenario_report_checker',Path(__file__).with_name('tools')/'check_scenarios.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)


def complete():
    return [dict(case=c,button=b,mode='full_policy',totals=checker.EXPECTED.copy(),
                 response_read_checks=checker.EXPECTED['learning_checks'],
                 unique_numeric_states=678,sequence_sha256=checker.DIGEST,
                 sample_counts={'768':10000,'1280':5952},max_decision_seconds=.01,
                 source_sha256={'strategy.py':'one-version'}) for c in checker.CASES for b in (0,1)]


def test_complete_report_grid_has_exact_scope_and_missing_case_is_rejected():
    reports=complete();summary=checker.summarize(reports)
    assert summary['totals']['terminal_histories']==408608
    with pytest.raises(AssertionError):checker.summarize(reports[:-1])


def test_accounting_only_or_mixed_versions_cannot_pass_full_policy_validation():
    reports=complete();reports[0]['mode']='accounting_only'
    with pytest.raises(AssertionError):checker.summarize(reports)
    reports=complete();reports[0]['source_sha256']={'strategy.py':'other-version'}
    with pytest.raises(AssertionError):checker.summarize(reports)


def test_missing_calling_read_coverage_cannot_pass_validation():
    reports=complete();reports[0]['response_read_checks']=0
    with pytest.raises(AssertionError):checker.summarize(reports)
