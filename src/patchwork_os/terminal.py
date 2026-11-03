# SPDX-License-Identifier: Apache-2.0
"""Supervisor-owned PTY. No shell is inserted into the configured argv."""
import os
import subprocess
import threading
import time
from .runtime_backend import atomic_json, process_birth


def supervise_terminal(backend, row):
    directory = backend.run_path(row['run_id'])
    row['supervisor'] = {'pid': os.getpid(), 'birth': process_birth(os.getpid())}
    env = os.environ.copy()
    if row.get('home'):
        env['HOME'] = env['USERPROFILE'] = row['home']
    child = None
    master = None
    reader = None
    stopped = False
    pid = None
    birth = None
    try:
        if os.name == 'nt':
            from winpty import PtyProcess
            os.environ['PYWINPTY_BACKEND'] = '0'
            child = PtyProcess.spawn(row['argv'], cwd=row['cwd'], env=env)
            pid = child.pid
            def alive(): return child.isalive()
            def write(data): child.write(data.decode('utf-8'))
            def read(): return child.read(4096).encode('utf-8')
            def finish(): child.close(force=True)
            def status(): return child.exitstatus
        else:
            import pty
            master, slave = pty.openpty()
            try:
                child = subprocess.Popen(row['argv'], cwd=row['cwd'], env=env, stdin=slave, stdout=slave, stderr=slave, start_new_session=True)
            finally: os.close(slave)
            pid = child.pid
            def alive(): return child.poll() is None
            def write(data): os.write(master, data)
            def read(): return os.read(master, 4096)
            def finish():
                child.terminate()
                try: child.wait(timeout=3)
                except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=3)
            def status(): return child.poll()
        birth = process_birth(pid)
        if not birth: raise RuntimeError('PROCESS_IDENTITY_UNAVAILABLE')
        row['process'] = {'pid': pid, 'birth': birth}
        row['status'] = 'running'
        row['delivery']['status'] = 'submitted'
        queue = directory / 'input-queue'; queue.mkdir(exist_ok=True)
        atomic_json(directory / 'run.json', row)
        with (directory / 'transcript.bin').open('ab', buffering=0) as transcript:
            def consume():
                try:
                    while True:
                        data = read()
                        if not data: break
                        transcript.write(data)
                except (EOFError, OSError, ValueError): pass
            reader = threading.Thread(target=consume, daemon=True); reader.start()
            initial = (directory / 'input.txt').read_bytes()
            if initial: write(initial)
            while alive():
                if (directory / 'stop.request').exists():
                    if process_birth(pid) != birth: raise RuntimeError('PROCESS_IDENTITY_MISMATCH')
                    finish(); stopped = True; break
                for entry in sorted(queue.glob('*.input')):
                    if process_birth(pid) != birth: raise RuntimeError('PROCESS_IDENTITY_MISMATCH')
                    data = entry.read_bytes(); write(data); entry.unlink()
                time.sleep(.025)
            if reader: reader.join(timeout=2)
        row['exit_code'] = status()
        row['status'] = 'closed' if stopped else 'completed' if row['exit_code'] == 0 else 'failed'
    except (OSError, ValueError, RuntimeError, ImportError, EOFError, subprocess.SubprocessError) as exc:
        row['status'] = 'blocked'; row['reason'] = str(exc)
        if pid and birth and process_birth(pid) == birth:
            try: finish()
            except (OSError, RuntimeError, subprocess.SubprocessError): pass
    finally:
        if master is not None:
            try: os.close(master)
            except OSError: pass
        row['finished_at'] = time.time(); atomic_json(directory / 'run.json', row)
    return 0
