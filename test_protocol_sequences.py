"""Authentication, startup, malformed packets, retries and result batches."""
from dataclasses import replace
import importlib.util
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from game import Action,AgentConfig,Game,make_deal

AUTH={'X-Agent-Token':'scenario-token'}


@pytest.fixture
def endpoint():
    spec=importlib.util.spec_from_file_location('scenario_http_agent',Path(__file__).with_name('agent.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.TOKEN='scenario-token'
    with TestClient(module.app) as client:yield module,client


def start(client):
    result=client.post('/new-half',headers=AUTH,json={'config':AgentConfig(time_bank_seconds=80.).to_dict()})
    assert result.status_code==200


@pytest.mark.parametrize('path',['/new-half','/act','/hand-end'])
@pytest.mark.parametrize('started',[False,True])
@pytest.mark.parametrize('token',['missing','wrong','valid'])
@pytest.mark.parametrize('body',['valid','malformed','array','null'])
def test_protocol_state_authentication_and_body_cross_product(endpoint,path,started,token,body):
    module,client=endpoint
    if started:start(client)
    headers=AUTH if token=='valid' else {} if token=='missing' else {'X-Agent-Token':'wrong'}
    valid={'/new-half':{'config':AgentConfig(time_bank_seconds=80.).to_dict()},
           '/act':{'observation':Game(make_deal('protocol-matrix',0),0).observation(0).to_dict()},
           '/hand-end':{'results':[]}}[path]
    if body=='malformed':response=client.post(path,headers=headers,content=b'{broken-json')
    else:response=client.post(path,headers=headers,json=valid if body=='valid' else [] if body=='array' else None)
    expected=401 if token!='valid' else 409 if not started and path!='/new-half' else 400 if body!='valid' else 200
    assert response.status_code==expected,response.text
    if expected==200 and path=='/act':assert response.json()['hand_end_errors']==[]
    if expected in (400,401,409):assert module.STATUS['started']==started


def test_invalid_observation_reports_error_then_valid_retry_is_clean(endpoint):
    module,client=endpoint;start(client)
    game=Game(make_deal('protocol-recovery',1),1,1);game.apply(Action.RAISE_HALF)
    obs=game.observation(0);bad=replace(obs,hole_cards=(obs.hole_cards[0],)*5)
    counts=module.MEMORY['counts'].copy();rng=module.MEMORY['rng']
    response=client.post('/act',headers=AUTH,json={'observation':bad.to_dict()})
    assert response.status_code==500 and 'ValueError' in response.json()['error']
    np.testing.assert_array_equal(module.MEMORY['counts'],counts)
    assert module.MEMORY['rng']==rng and module.MEMORY['last'] is None
    response=client.post('/act',headers=AUTH,json={'observation':obs.to_dict()})
    assert response.status_code==200 and Action[response.json()['action']] in obs.legal_actions


def test_reordered_duplicate_result_batch_and_stale_act_preserve_current_hand(endpoint):
    module,client=endpoint;start(client)
    results=[]
    for i in (0,1):
        game=Game(make_deal('batch-results',i),i%2,i);game.apply(Action.FOLD)
        results.append(game.hand_result(0).to_dict())
    obs=Game(make_deal('batch-results',2),0,2).observation(0)
    response=client.post('/act',headers=AUTH,json={'observation':obs.to_dict(),
                'hand_results':[results[1],results[0],results[1],results[0]]})
    assert response.status_code==200 and response.json()['hand_end_errors']==[]
    assert module.MEMORY['hands_played']==2 and module.MEMORY['completed_hands']=={0,1}
    before=module.MEMORY['counts'].copy();rng=module.MEMORY['rng'];last=module.MEMORY['last']
    old=Game(make_deal('batch-results',0),0,0).observation(0)
    response=client.post('/act',headers=AUTH,json={'observation':old.to_dict(),'hand_results':results})
    assert response.status_code==200 and Action[response.json()['action']] in old.legal_actions
    np.testing.assert_array_equal(module.MEMORY['counts'],before)
    assert module.MEMORY['rng']==rng and module.MEMORY['last'] is last
    assert module.MEMORY['hands_played']==2


def test_restarting_a_half_restores_values_and_team_identity(endpoint):
    module,client=endpoint;start(client)
    module.MEMORY['counts']+=31;module.MEMORY['completed_hands'].update([0,1,2])
    module.MEMORY['unrelated_cache']='old'
    start(client)
    fresh={};module.new_half(AgentConfig(time_bank_seconds=80.),fresh)
    assert module.MEMORY.keys()==fresh.keys()
    for key,value in fresh.items():
        if isinstance(value,np.ndarray):np.testing.assert_array_equal(module.MEMORY[key],value)
        else:assert module.MEMORY[key]==value
    assert client.get('/').json()['participant']=='winner'


def test_failed_finished_hand_reports_error_and_can_be_retried(endpoint):
    module,client=endpoint;start(client)
    game=Game(make_deal('http-result-retry',0),0)
    for _ in range(7):
        if game.to_act==0:
            obs=game.observation(0);module.choose_action(obs,module.MEMORY)
            module.MEMORY['last']=(obs,Action.CHECK_CALL,module.MEMORY['cache'])
        game.apply(Action.CHECK_CALL)
    obs=game.observation(0);module.choose_action(obs,module.MEMORY)
    module.MEMORY['last']=(obs,Action.RAISE_POT,module.MEMORY['cache'])
    game.apply(Action.RAISE_POT);game.apply(Action.CHECK_CALL)
    result=game.hand_result(0);bad=replace(result,opp_hole=(result.opp_hole[0],)*5)
    before=module.MEMORY['counts'].copy()
    response=client.post('/hand-end',headers=AUTH,json={'results':[bad.to_dict()]})
    assert response.status_code==200 and len(response.json()['hand_end_errors'])==1
    np.testing.assert_array_equal(module.MEMORY['counts'],before)
    assert module.MEMORY['hands_played']==0
    response=client.post('/hand-end',headers=AUTH,json={'results':[result.to_dict(),result.to_dict()]})
    assert response.status_code==200 and response.json()['hand_end_errors']==[]
    assert module.MEMORY['hands_played']==1
