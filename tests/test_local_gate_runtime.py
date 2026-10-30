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


def test_ollama_resident_gpu_and_evidence(tmp_path):
    from pathlib import Path
    class Ollama(BaseHTTPRequestHandler):
        calls=[]
        def log_message(self,*a): pass
        def do_GET(self):
            self.calls.append((self.path,None))
            self.reply({'models':[{'name':'sample:local','model':'sample:local','size':100,'size_vram':100,'context_length':8192,'digest':'sample-sha'}]})
        def do_POST(self):
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            self.calls.append((self.path,data))
            if self.path=='/api/show': self.reply({'thinking':{'values':[False,True],'default':True}})
            elif self.path=='/api/generate': self.reply({'model':'sample:local','done':True,'done_reason':'stop','response':json.dumps({'binding':'scope-a','verdict':'pass'})})
            else: self.send_error(404)
        def reply(self, obj):
            body=json.dumps(obj).encode(); self.send_response(200); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    server=HTTPServer(('127.0.0.1',0),Ollama); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        root=tmp_path/'root';initialize_workspace(root); p=root/'.patchwork/config.json'; cfg=json.loads(p.read_text());cfg['binding']='scope-a'
        cfg['local_judge']={'protocol':'ollama','url':f'http://127.0.0.1:{server.server_port}','model':'sample:local','admission':'resident_gpu_only'};p.write_text(json.dumps(cfg))
        source=tmp_path/'diff';source.write_text('safe sample'); event=tmp_path/'event';event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
        result=invoke_hook(root,event);assert result['verdict']=='pass' and result['completion_allowed'] is False
        assert result['judge']['observed_model']=='sample:local'
        assert Path(result['judge']['request']['path']).read_bytes() and Path(result['judge']['response']['path']).read_bytes()
        generate=[x[1] for x in Ollama.calls if x[0]=='/api/generate'];assert len(generate)==1
        assert generate[0]['think'] is False and generate[0]['stream'] is False and generate[0]['format']=='json'
        assert generate[0]['options']=={'temperature':0,'num_ctx':8192,'num_gpu':999}
    finally: server.shutdown();thread.join();server.server_close()


def test_ollama_unavailable_foreign_and_truncated_never_pass(tmp_path):
    class Ollama(BaseHTTPRequestHandler):
        mode='not_resident'; calls=[]
        def log_message(self,*a): pass
        def reply(self,obj):
            data=json.dumps(obj).encode();self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_GET(self):
            self.calls.append(self.path); self.reply({'models':[] if self.mode=='not_resident' else [{'name':'sample:local','model':'sample:local','size':100,'size_vram':100,'context_length':8192,'digest':'sample-sha'}]})
        def do_POST(self):
            self.calls.append(self.path);self.rfile.read(int(self.headers['Content-Length']))
            if self.path=='/api/show':self.reply({'thinking':{'values':[False]}})
            else:self.reply({'model':'other' if self.mode=='model' else 'sample:local','done':self.mode!='truncated','done_reason':'length' if self.mode=='truncated' else 'stop','response':json.dumps({'binding':'foreign' if self.mode=='binding' else 'scope-a','verdict':'pass'})})
    server=HTTPServer(('127.0.0.1',0),Ollama);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        root=tmp_path/'root';initialize_workspace(root);p=root/'.patchwork/config.json';cfg=json.loads(p.read_text());cfg['binding']='scope-a';cfg['local_judge']={'protocol':'ollama','url':f'http://127.0.0.1:{server.server_port}','model':'sample:local','admission':'resident_gpu_only'};p.write_text(json.dumps(cfg)); source=tmp_path/'diff'; event=tmp_path/'event'
        for mode in ('not_resident','model','binding','truncated'):
            Ollama.mode=mode;source.write_text(mode);event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
            result=invoke_hook(root,event);assert result['verdict']=='ambiguous' and result['completion_allowed'] is False
        assert Ollama.calls[0]=='/api/ps'
    finally: server.shutdown();thread.join();server.server_close()


def test_ollama_malformed_and_timeout_are_ambiguous(tmp_path):
    import time
    class Ollama(BaseHTTPRequestHandler):
        mode='malformed'
        def log_message(self,*a): pass
        def emit(self,data):
            self.send_response(200);self.send_header('Content-Length',str(len(data)));self.end_headers()
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
        def do_GET(self):self.emit(json.dumps({'models':[{'name':'sample:local','model':'sample:local','size':100,'size_vram':100,'context_length':8192,'digest':'abc'}]}).encode())
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            if self.path=='/api/show':self.emit(json.dumps({'thinking':{'values':[False]}}).encode())
            elif self.mode=='timeout':time.sleep(.2);self.emit(b'{}')
            else:self.emit(b'{bad json')
    server=HTTPServer(('127.0.0.1',0),Ollama);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        root=tmp_path/'root';initialize_workspace(root);p=root/'.patchwork/config.json';cfg=json.loads(p.read_text());cfg['binding']='scope-a';cfg['local_judge']={'protocol':'ollama','url':f'http://127.0.0.1:{server.server_port}','model':'sample:local','admission':'resident_gpu_only','timeout_seconds':.05};p.write_text(json.dumps(cfg));source=tmp_path/'diff';event=tmp_path/'event'
        for mode in ('malformed','timeout'):
            Ollama.mode=mode;source.write_text(mode);event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
            result=invoke_hook(root,event);assert result['verdict']=='ambiguous' and result['completion_allowed'] is False
            if mode=='malformed':assert result['judge']['response']['bytes'] > 0
    finally:server.shutdown();thread.join();server.server_close()


def test_loopback_ignores_environment_proxy(tmp_path, monkeypatch):
    class Judge(BaseHTTPRequestHandler):
        def log_message(self,*a): pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']))
            body=json.dumps({'binding':'scope-a','thinking':False,'verdict':'pass'}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=HTTPServer(('127.0.0.1',0),Judge);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        monkeypatch.setenv('http_proxy','http://127.0.0.1:1');monkeypatch.setenv('HTTP_PROXY','http://127.0.0.1:1');monkeypatch.setenv('no_proxy','');monkeypatch.setenv('NO_PROXY','')
        root=tmp_path/'root';initialize_workspace(root);p=root/'.patchwork/config.json';cfg=json.loads(p.read_text());cfg['binding']='scope-a';cfg['local_judge']={'url':f'http://127.0.0.1:{server.server_port}','supports_no_thinking':True};p.write_text(json.dumps(cfg))
        source=tmp_path/'diff';source.write_text('sample');event=tmp_path/'event';event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
        assert invoke_hook(root,event)['verdict']=='pass'
    finally:server.shutdown();thread.join();server.server_close()


def test_valid_ambiguous_dedupes_but_invalid_response_retries(tmp_path):
    class Judge(BaseHTTPRequestHandler):
        calls=0; malformed=False
        def log_message(self,*a):pass
        def do_POST(self):
            type(self).calls+=1;self.rfile.read(int(self.headers['Content-Length']))
            body=b'{bad' if self.malformed else json.dumps({'binding':'scope-a','thinking':False,'verdict':'ambiguous'}).encode()
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=HTTPServer(('127.0.0.1',0),Judge);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        root=tmp_path/'root';initialize_workspace(root);p=root/'.patchwork/config.json';cfg=json.loads(p.read_text());cfg['binding']='scope-a';cfg['local_judge']={'url':f'http://127.0.0.1:{server.server_port}','supports_no_thinking':True};p.write_text(json.dumps(cfg))
        source=tmp_path/'diff';source.write_text('sample');event=tmp_path/'event';event.write_text(json.dumps({'binding':'scope-a','raw_path':str(source)}))
        first=invoke_hook(root,event);second=invoke_hook(root,event)
        assert first==second and Judge.calls==1
        assert first['verdict']=='ambiguous' and first['advisory'] is True and first['main_escalation'] is True
        assert first['dedupe']['eligible'] is True and first['completion_allowed'] is False
        source.write_text('malformed input');Judge.malformed=True
        first=invoke_hook(root,event);second=invoke_hook(root,event)
        assert first['dedupe']['eligible'] is False and second['dedupe']['eligible'] is False and Judge.calls==3
    finally:server.shutdown();thread.join();server.server_close()
