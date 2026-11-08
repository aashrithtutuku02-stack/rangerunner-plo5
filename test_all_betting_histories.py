import pytest
from scenario_sweep import sweep,cases


@pytest.mark.parametrize('button',[0,1])
def test_every_legal_action_history_has_correct_public_accounting(button):
    report=sweep('random',cases()['random'],button,full_policy=False)
    assert report['totals']['terminal_histories']==25538
    assert report['totals']['terminal_inference_checks']==51076
