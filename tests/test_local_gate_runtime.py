# SPDX-License-Identifier: MIT
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from patchwork_os.local_gate import invoke_hook
from patchwork_os.runtime_backend import initialize_workspace


def test_binding_truncation_and_persistent_dedup(tmp_path):
    root=tmp_path/'root'; initialize_workspace(root)
    config=root/'.patchwork/config.json'; cfg=json.loads(config.read_text()); cfg['binding']='scope-a'; config.write_text(json.dumps(cfg))
    source=tmp_path/'diff'; source.write_bytes(b'x'*3501)
    event=tmp_path/'event.json'; event.write_text(json.dumps({'binding':'foreign','raw_path':str(source)}))
    assert invoke_hook(root,event)['verdict']=='ambiguous'
    event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
    first=invoke_hook(root,event)
    assert first['verdict']=='ambiguous' and first['processed']['truncated'] and first['completion_allowed'] is False
    assert invoke_hook(root,event)==first
    assert len(list((root/'.patchwork/hooks').glob('*.json')))==1
    source.write_bytes(b'changed')
    assert invoke_hook(root,event)['raw']['sha256'] != first['raw']['sha256']


def test_local_http_structured_verdict_and_wrong_binding(tmp_path):
    class Judge(BaseHTTPRequestHandler):
        foreign=False
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            assert request['thinking'] is False
            body=json.dumps({'binding':'wrong' if self.foreign else 'scope-a','thinking':False,'verdict':'pass'}).encode()
            self.send_response(200); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args): pass
    server=HTTPServer(('127.0.0.1',0),Judge); thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        root=tmp_path/'root'; initialize_workspace(root)
        config=root/'.patchwork/config.json'; cfg=json.loads(config.read_text()); cfg['binding']='scope-a'; cfg['local_judge']={'url':f'http://127.0.0.1:{server.server_port}/','supports_no_thinking':True}; config.write_text(json.dumps(cfg))
        source=tmp_path/'diff'; source.write_text('short')
        event=tmp_path/'event.json'; event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
        result=invoke_hook(root,event); assert result['verdict']=='pass' and result['completion_allowed'] is False
        Judge.foreign=True; source.write_text('different')
        assert invoke_hook(root,event)['verdict']=='ambiguous'
    finally:
        server.shutdown(); thread.join(); server.server_close()
