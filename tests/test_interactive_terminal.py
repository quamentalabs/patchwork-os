# SPDX-License-Identifier: Apache-2.0
import json
import sys
import time
from pathlib import Path
import pytest
from patchwork_os.runtime_backend import LocalRuntimeBackend, RuntimeErrorDetail, initialize_workspace, process_birth, terminal_capability


def test_interactive_two_inputs_and_identity_guards(tmp_path):
    if terminal_capability()[0] != 'available': pytest.skip('PTY unavailable')
    root = tmp_path / 'workspace'; initialize_workspace(root)
    fixture = tmp_path / 'interactive.py'
    fixture.write_text('import sys\nprint("READY",flush=True)\nfor line in sys.stdin:\n print("REPLY:"+line.strip(),flush=True)\n')
    cfgpath = root / '.patchwork/config.json'; cfg = json.loads(cfgpath.read_text())
    cfg['runtimes']['muse'] = {'executable':sys.executable,'args':['-u',str(fixture)],'delivery':'stdin','model':None,'effort':None}
    cfgpath.write_text(json.dumps(cfg)); backend = LocalRuntimeBackend(root)
    enter = '\r' if sys.platform == 'win32' else '\n'
    job = backend.launch('muse',enter,mode='terminal'); rid = job['run_id']
    def waitfor(text):
        for _ in range(300):
            result = backend.collect(rid)
            if text in result['output']: return result
            if result['status'] in ('blocked','failed','closed'): raise AssertionError(result)
            time.sleep(.03)
        raise AssertionError(result)
    try:
        result = waitfor('READY'); assert result['process']['birth'] == process_birth(result['process']['pid'])
        backend.terminal_input(rid,'alpha'+enter); waitfor('REPLY:alpha')
        backend.terminal_input(rid,'beta'+enter); result = waitfor('REPLY:beta')
        assert result['native_acceptance']=='not_run'
        path = backend.run_path(rid) / 'run.json'; row = json.loads(path.read_text()); original = row['process']['birth']
        row['process']['birth']='reused'; path.write_text(json.dumps(row))
        with pytest.raises(RuntimeErrorDetail,match='PROCESS_IDENTITY_MISMATCH'): backend.close(rid)
        with pytest.raises(RuntimeErrorDetail,match='PROCESS_IDENTITY_MISMATCH'): backend.terminal_input(rid,'x')
        row['process']['birth']=original; row['owner_id']='foreign'; path.write_text(json.dumps(row))
        with pytest.raises(RuntimeErrorDetail,match='FOREIGN_RUN'): backend.close(rid)
        row['owner_id']=backend.owner_id; path.write_text(json.dumps(row))
    finally:
        backend.close(rid)
    assert backend.observe(rid)['lease']['released'] is True
