import hashlib
import json
import sys
from pathlib import Path

import pytest
from patchwork_os.runtime_backend import LocalRuntimeBackend, RuntimeErrorDetail, initialize_workspace


def test_external_collector_roundtrip_and_refusals(tmp_path):
    root = tmp_path / 'workspace'
    initialize_workspace(root)
    answer = tmp_path / 'answer.md'
    answer.write_text('native answer', encoding='utf8')
    digest = hashlib.sha256(answer.read_bytes()).hexdigest()
    model = {'requested': 'example-model', 'resolved': 'example-model', 'observed': 'example-model', 'status': 'bound', 'source': 'native'}
    result = {'kind': 'deploy2-collect', 'run_id': 'example-run', 'owner_session': 'example-owner', 'target': 'muse', 'state': 'closed', 'current_completion_allowed': True,
              'done': {'ok': True, 'status': 'completed', 'answer_contract': {'ok': True, 'required': True, 'completion_allowed': True, 'answer_sha256': digest, 'semantic_authority': 'controller_bound_external_review', 'edit': {'model_observation': model, 'actual_diff': True, 'session_id': 'native-session'}}},
              'native_observation': {'run_id': 'example-run', 'session_id': 'native-session', 'runtime': 'muse', 'status': 'observed', 'transcript_replay': 'verified', 'qualifies_authentic_edits': True, 'existing_verifier': {'status': 'accepted'}, 'answer_sha256': digest},
              'artifacts': {'ok': True, 'artifacts': [{'path': 'answer.md', 'sha256': 'sha256:'+digest, 'size_bytes': len(answer.read_bytes()), 'verified': True}]}}
    fixture = tmp_path / 'fixture.json'
    fixture.write_text(json.dumps(result))
    script = tmp_path / 'collector.py'
    script.write_text('import pathlib,sys\nprint(pathlib.Path(sys.argv[1]).read_text())\n')
    cfg = json.loads((root / '.patchwork/config.json').read_text())
    cfg['external_collector'] = {'argv': [sys.executable, str(script), str(fixture)], 'cwd': str(tmp_path), 'source_pins': {sys.executable: hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(), str(script): hashlib.sha256(script.read_bytes()).hexdigest()}, 'artifact_root': str(tmp_path), 'answer_path': 'answer.md', 'run_id': 'example-run', 'owner_session': 'example-owner', 'runtime': 'muse', 'model': 'example-model'}
    (root / '.patchwork/config.json').write_text(json.dumps(cfg))
    backend = LocalRuntimeBackend(root)
    attached = backend.attach_external()
    assert attached['output'] == 'native answer'
    assert attached['origin'] == 'external_attachment'
    assert attached['completion_allowed'] is True
    history = json.loads(json.dumps(result))
    recorded = history['done']['answer_contract']
    recorded['native_observation'] = history['native_observation']
    history.update({'state': 'archived_completed', 'completion_basis': 'authenticated_historical', 'current_completion_allowed': False, 'recorded_completion_allowed': True, 'done': {'ok': False, 'reason': 'ANSWER_LEASE_NOT_LIVE'}, 'lifecycle': {'state': 'historical', 'current_live_acceptance': 'not_run', 'capacity_returned': True, 'lease': {'stored': True}, 'recorded_answer_contract': recorded, 'proof': {k: 'a'*64 for k in ('run_json_sha256', 'done_json_sha256', 'archive_sha256', 'closeout_sha256', 'close_receipt_sha256')}}})
    fixture.write_text(json.dumps(history))
    archived = backend.attach_external()
    assert archived['output'] == 'native answer' and archived['recorded_completion_allowed'] is True
    assert archived['completion_allowed'] is False and archived['current_reason'] == 'ANSWER_LEASE_NOT_LIVE'
    del history['lifecycle']['proof']['archive_sha256']
    fixture.write_text(json.dumps(history))
    with pytest.raises(RuntimeErrorDetail): backend.attach_external()
    fixture.write_text(json.dumps(result))
    if sys.platform == 'win32':
        cfg['external_collector']['answer_path'] = r'\foreign\answer.md'
        (root / '.patchwork/config.json').write_text(json.dumps(cfg))
        with pytest.raises(RuntimeErrorDetail): backend.attach_external()
        cfg['external_collector']['answer_path'] = 'answer.md'
        (root / '.patchwork/config.json').write_text(json.dumps(cfg))
    for key, value in [('state', 'held'), ('owner_session', 'foreign'), ('current_completion_allowed', False)]:
        changed = dict(result, **{key: value})
        fixture.write_text(json.dumps(changed))
        with pytest.raises(RuntimeErrorDetail): backend.attach_external()
    result['done']['answer_contract']['edit']['model_observation']['observed'] = 'foreign'
    fixture.write_text(json.dumps(result))
    with pytest.raises(RuntimeErrorDetail): backend.attach_external()
    result['done']['answer_contract']['edit']['model_observation']['observed'] = 'example-model'
    result['done']['answer_contract']['semantic_authority'] = 'not_run'
    fixture.write_text(json.dumps(result))
    with pytest.raises(RuntimeErrorDetail): backend.attach_external()
    result['done']['answer_contract']['semantic_authority'] = 'controller_bound_external_review'
    fixture.write_text('{broken')
    with pytest.raises(RuntimeErrorDetail): backend.attach_external()
    fixture.write_text(json.dumps(result))
    answer.write_text('changed')
    with pytest.raises(RuntimeErrorDetail): backend.attach_external()


def test_actual_post_close_refusal_stays_blocked(tmp_path):
    from patchwork_os.external_native import attach
    response = {'kind': 'deploy2-collect', 'state': 'refused', 'current_completion_allowed': False, 'completion_basis': 'current_observation', 'done': {'ok': False, 'status': 'contract_refused', 'reason': 'ANSWER_LEASE_NOT_LIVE', 'answer_contract': {'ok': False, 'required': True, 'completion_allowed': False, 'reason': 'ANSWER_LEASE_NOT_LIVE', 'status': 'refused', 'main_escalation': True}}}
    source = tmp_path / 'collector.py'
    source.write_text('print('+repr(json.dumps(response))+')')
    config = {'argv': [sys.executable, str(source)], 'cwd': str(tmp_path), 'source_pins': {sys.executable: hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(), str(source): hashlib.sha256(source.read_bytes()).hexdigest()}}
    with pytest.raises(RuntimeErrorDetail):
        attach(config)
