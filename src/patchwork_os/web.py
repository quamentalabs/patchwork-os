# SPDX-License-Identifier: MIT
"""Loopback-only cockpit, with origin and per-workspace token checks."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlsplit
from .runtime_backend import LocalRuntimeBackend, RUNTIMES


def serve(root, port=8765):
    backend = LocalRuntimeBackend(Path(root))
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass
        def send_json(self, value, status=200):
            raw = json.dumps(value, ensure_ascii=False).encode()
            self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw)
        def authorized(self):
            host = self.headers.get('Host','')
            expected = f'127.0.0.1:{self.server.server_port}'
            origin = self.headers.get('Origin')
            return host == expected and (origin is None or origin == 'http://' + expected) and self.headers.get('X-PWOS-Token') == backend.owner['api_token']
        def do_GET(self):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                self.send_error(403); return
            path = urlsplit(self.path).path
            if path == '/':
                raw = files('patchwork_os').joinpath('assets/index.html').read_bytes().replace(b'__TOKEN__', backend.owner['api_token'].encode())
                self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            if not self.authorized(): self.send_error(403); return
            try:
                if path == '/api/config': result = {name: backend.probe(name) for name in RUNTIMES}
                elif path == '/api/runs': result = backend.list_runs()
                elif path.startswith('/api/collect/'): result = backend.collect(path.removeprefix('/api/collect/'))
                else: self.send_error(404); return
                self.send_json(result)
            except (OSError, ValueError, KeyError) as exc: self.send_json({'error':str(exc)},400)
        def do_POST(self):
            if not self.authorized(): self.send_error(403); return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if length < 1 or length > 1048576: raise ValueError('INVALID_BODY_SIZE')
                body = json.loads(self.rfile.read(length))
                if not isinstance(body,dict): raise ValueError('JSON_OBJECT_REQUIRED')
                if self.path == '/api/attach-external':
                    if body: raise ValueError('INVALID_FIELDS')
                    result = backend.attach_external()
                elif self.path == '/api/run':
                    allowed = {'runtime','prompt','model','effort','mode','submission_id'}
                    if set(body) - allowed: raise ValueError('UNKNOWN_FIELD')
                    result = backend.launch(**body)
                elif self.path == '/api/input':
                    if set(body) != {'run_id', 'text'}: raise ValueError('INVALID_FIELDS')
                    result = backend.terminal_input(body['run_id'], body['text'])
                elif self.path == '/api/close':
                    if set(body) != {'run_id'}: raise ValueError('INVALID_FIELDS')
                    result = backend.close(body['run_id'])
                else: self.send_error(404); return
                self.send_json(result)
            except (OSError, ValueError, KeyError, TypeError) as exc: self.send_json({'error':str(exc)},400)
    with ThreadingHTTPServer(('127.0.0.1',port),Handler) as server:
        print(f'http://127.0.0.1:{server.server_port}',flush=True)
        server.serve_forever()
