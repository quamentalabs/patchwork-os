# SPDX-License-Identifier: MIT
"""Explicit external deploy2 collector attachment; authority remains with the collector."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

from .runtime_backend import RuntimeErrorDetail

LIMIT = 4 * 1024 * 1024


def _plain(path):
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise RuntimeErrorDetail('EXTERNAL_PATH_REFUSED')
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise RuntimeErrorDetail('EXTERNAL_LINK_REFUSED')
    return path


def attach(config):
    if not isinstance(config, dict):
        raise RuntimeErrorDetail('EXTERNAL_COLLECTOR_NOT_CONFIGURED')
    argv, pins = config.get('argv'), config.get('source_pins')
    if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv) or not isinstance(pins, dict) or argv[0] not in pins:
        raise RuntimeErrorDetail('EXTERNAL_BINDING_INVALID')
    cwd = _plain(config['cwd'])
    for name, expected in pins.items():
        path = _plain(name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeErrorDetail('EXTERNAL_SOURCE_CHANGED')
    proc = subprocess.Popen(argv, cwd=cwd, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    chunks, overflow = [], []
    def read():
        total = 0
        while True:
            chunk = proc.stdout.read(65536)
            if not chunk: break
            total += len(chunk)
            if total > LIMIT:
                overflow.append(True)
                proc.kill()
                break
            chunks.append(chunk)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill(); proc.wait(); reader.join(timeout=2)
        raise RuntimeErrorDetail('EXTERNAL_COLLECTOR_TIMEOUT')
    reader.join(timeout=2)
    if reader.is_alive() or overflow or proc.returncode != 0:
        raise RuntimeErrorDetail('EXTERNAL_COLLECTOR_FAILED')
    try:
        data = json.loads(b''.join(chunks))
        done = data['done']
        historical = data.get('state') == 'archived_completed'
        if historical:
            lifecycle = data['lifecycle']; proof = lifecycle['proof']
            proof_keys = ('run_json_sha256', 'done_json_sha256', 'archive_sha256', 'closeout_sha256', 'close_receipt_sha256')
            if (data['completion_basis'] != 'authenticated_historical' or data['current_completion_allowed'] is not False or data['recorded_completion_allowed'] is not True or lifecycle['state'] != 'historical' or lifecycle['current_live_acceptance'] != 'not_run' or lifecycle['capacity_returned'] is not True or lifecycle['lease']['stored'] is not True or any(not isinstance(proof[k], str) or len(proof[k]) != 64 or any(ch not in '0123456789abcdef' for ch in proof[k]) for k in proof_keys)):
                raise RuntimeErrorDetail('EXTERNAL_HISTORY_REFUSED')
            contract = lifecycle['recorded_answer_contract']; native = contract['native_observation']
        else:
            if data['state'] != 'closed' or data['current_completion_allowed'] is not True or done['ok'] is not True or done['status'] != 'completed':
                raise RuntimeErrorDetail('EXTERNAL_EVIDENCE_REFUSED')
            contract = done['answer_contract']; native = data['native_observation']
        edit = contract['edit']; model = edit['model_observation']
        if (data['kind'] != 'deploy2-collect' or data['run_id'] != config['run_id'] or data['owner_session'] != config['owner_session'] or data['target'] != config['runtime'] or contract['ok'] is not True or contract['required'] is not True or contract['completion_allowed'] is not True or contract['semantic_authority'] != 'controller_bound_external_review' or model['status'] != 'bound' or not model['source'] or any(model[k] != config['model'] for k in ('requested','resolved','observed')) or data['artifacts']['ok'] is not True):
            raise RuntimeErrorDetail('EXTERNAL_EVIDENCE_REFUSED')
        if (edit['actual_diff'] is not True or native['run_id'] != data['run_id'] or native['session_id'] != edit['session_id'] or native['runtime'] != data['target'] or native['status'] != 'observed' or native['transcript_replay'] != 'verified' or native['qualifies_authentic_edits'] is not True or native['existing_verifier']['status'] != 'accepted' or native['answer_sha256'] != contract['answer_sha256']):
            raise RuntimeErrorDetail('EXTERNAL_NATIVE_REFUSED')
        relative = Path(config['answer_path'])
        if relative.anchor or '..' in relative.parts or not relative.parts:
            raise RuntimeErrorDetail('EXTERNAL_PATH_REFUSED')
        root = _plain(config['artifact_root'])
        answer = _plain(root / relative)
        if not answer.is_relative_to(root):
            raise RuntimeErrorDetail('EXTERNAL_PATH_REFUSED')
        if not answer.is_file() or answer.stat().st_size > LIMIT:
            raise RuntimeErrorDetail('EXTERNAL_ARTIFACT_REFUSED')
        matches = [x for x in data['artifacts']['artifacts'] if x.get('path') == config['answer_path']]
        if len(matches) != 1: raise RuntimeErrorDetail('EXTERNAL_ARTIFACT_REFUSED')
        artifact = matches[0]; raw = answer.read_bytes(); sha = hashlib.sha256(raw).hexdigest()
        if artifact.get('verified') is not True or artifact.get('size_bytes') != len(raw) or artifact.get('sha256') != 'sha256:' + sha or contract['answer_sha256'] != sha:
            raise RuntimeErrorDetail('EXTERNAL_ARTIFACT_CHANGED')
        output = raw.decode('utf-8', errors='strict')
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        if isinstance(exc, RuntimeErrorDetail): raise
        raise RuntimeErrorDetail('EXTERNAL_RESPONSE_INVALID') from exc
    result = {'origin': 'external_attachment', 'authority': 'configured_external_collector', 'run_id': data['run_id'], 'owner_session': data['owner_session'], 'runtime': data['target'], 'status': 'historical' if historical else 'closed', 'model': {k: model[k] for k in ('requested','resolved','observed')}, 'native_acceptance': 'collector_verified_historical' if historical else 'collector_verified', 'review_acceptance': 'collector_verified_historical' if historical else 'collector_verified', 'completion_allowed': not historical, 'output': output, 'answer': {'sha256': 'sha256:'+sha, 'bytes': len(raw)}, 'submission': 'not_observed'}
    if historical:
        result.update({'recorded_completion_allowed': True, 'current_live_acceptance': 'not_run', 'completion_basis': 'authenticated_historical', 'archive_proof': proof, 'current_reason': done.get('reason')})
    return result
