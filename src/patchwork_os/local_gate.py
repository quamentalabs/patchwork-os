# SPDX-License-Identifier: MIT
"""Bounded local review; no verdict grants native task completion."""
import hashlib
import json
import os
import uuid
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from .hub_spoke_gate import GateVerdictResult, evaluate_zero_thinking_gate
from .runtime_backend import LocalRuntimeBackend, digest, read_json, atomic_json


def invoke_hook(root, input_path):
    backend = LocalRuntimeBackend(Path(root))
    input_path = Path(input_path).resolve(strict=True)
    raw_input = input_path.read_bytes()
    event = json.loads(raw_input)
    if not isinstance(event,dict): raise ValueError('EVENT_OBJECT_REQUIRED')
    config = backend._config()
    binding = config.get('binding')
    if not isinstance(binding,str) or not binding or event.get('binding') != binding:
        return {'verdict':'ambiguous','reason':'BINDING_MISSING_OR_FOREIGN','completion_allowed':False}
    source = Path(event['raw_path']).resolve(strict=True)
    raw = source.read_bytes()
    state = backend.state_root / 'hooks'
    state.mkdir(exist_ok=True)
    key = hashlib.sha256(raw_input + b"\0" + raw).hexdigest()
    record = state / (key + '.json')
    if record.exists(): return read_json(record)
    raw_store = state / (key + '.raw')
    raw_store.write_bytes(raw)
    limit = 3500
    processed = raw[:limit].decode('utf-8', errors='replace')
    payload = {'raw_diff_excerpt':processed,'processed_ast_delta':[],'processed_lint_errors':[], 'truncated':len(raw)>limit}
    judge = config.get('local_judge')
    def classify(data):
        if not isinstance(judge,dict) or judge.get('supports_no_thinking') is not True: raise ValueError('JUDGE_UNAVAILABLE')
        url = urlsplit(judge.get('url',''))
        if url.scheme != 'http' or url.hostname not in ('127.0.0.1','localhost','::1') or url.username or url.password: raise ValueError('LOCAL_HTTP_REQUIRED')
        body = json.dumps({'binding':binding,'payload':data,'thinking':False}).encode()
        request = Request(judge['url'], data=body, headers={'Content-Type':'application/json'},method='POST')
        with urlopen(request, timeout=float(judge.get('timeout_seconds',10))) as response:
            response_raw = response.read(65537)
        if len(response_raw)>65536: raise ValueError('JUDGE_RESPONSE_TRUNCATED')
        response_data=json.loads(response_raw)
        if not isinstance(response_data,dict) or response_data.get('binding') != binding or response_data.get('thinking') is not False: raise ValueError('JUDGE_BINDING_INVALID')
        verdict=response_data.get('verdict')
        if verdict not in ('pass','fail','adjust','halt','ambiguous'): raise ValueError('JUDGE_VERDICT_INVALID')
        return GateVerdictResult(verdict={'pass':'PASS','fail':'FAIL'}.get(verdict,'AMBIGUOUS'),confidence=0.0,escalate_to='PLANNER_VALIDATOR' if verdict not in ('pass','fail') else 'NONE',escalation_reason=verdict)
    verdict = evaluate_zero_thinking_gate(payload,local_classifier_fn=classify)
    result = {'binding':binding,'verdict':verdict.verdict.lower(),'reason':verdict.escalation_reason,'raw':{'source':str(source),'stored':str(raw_store),'sha256':digest(raw),'bytes':len(raw)},'processed':{'scope':'first 3500 bytes','sha256':digest(processed.encode()),'truncated':payload['truncated']},'input_sha256':digest(raw_input),'completion_allowed':False}
    atomic_json(record,result)
    return result
