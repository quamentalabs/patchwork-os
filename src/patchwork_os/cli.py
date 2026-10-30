# SPDX-License-Identifier: MIT
"""Local command line entry point for explicitly configured processes."""
import argparse
import json
import sys
from pathlib import Path
from .runtime_backend import LocalRuntimeBackend, RuntimeErrorDetail, RUNTIMES, initialize_workspace


def main(argv=None):
    parser = argparse.ArgumentParser(prog='pwos')
    parser.add_argument('--root', type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('init')
    commands.add_parser('doctor')
    commands.add_parser('attach-external')
    server = commands.add_parser('serve')
    server.add_argument('--port', type=int, default=8765)
    run = commands.add_parser('run')
    run.add_argument('runtime', choices=RUNTIMES)
    run.add_argument('--task-file', type=Path)
    run.add_argument('--model')
    run.add_argument('--effort')
    run.add_argument('--mode', choices=['task','terminal'], default='task')
    run.add_argument('--submission-id')
    status = commands.add_parser('status')
    status.add_argument('run_id', nargs='?')
    for name in ('collect','close'):
        commands.add_parser(name).add_argument('run_id')
    terminal_input = commands.add_parser('input')
    terminal_input.add_argument('run_id')
    hook = commands.add_parser('hook')
    hook.add_argument('action', choices=['run'])
    hook.add_argument('--input', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            result = initialize_workspace(args.root)
        elif args.command == 'serve':
            from .web import serve
            serve(args.root, args.port)
            return 0
        else:
            backend = LocalRuntimeBackend(args.root)
            if args.command == 'doctor':
                result = {name: backend.probe(name) for name in RUNTIMES}
            elif args.command == 'attach-external':
                result = backend.attach_external()
            elif args.command == 'run':
                prompt = args.task_file.read_text(encoding='utf-8') if args.task_file else sys.stdin.read()
                result = backend.launch(args.runtime, prompt, model=args.model, effort=args.effort, mode=args.mode, submission_id=args.submission_id)
            elif args.command == 'status':
                result = backend.observe(args.run_id) if args.run_id else backend.list_runs()
            elif args.command == 'input':
                result = backend.terminal_input(args.run_id, sys.stdin.buffer.read().decode('utf-8'))
            elif args.command == 'collect':
                result = backend.collect(args.run_id)
            elif args.command == 'close':
                result = backend.close(args.run_id)
            else:
                from .local_gate import invoke_hook
                result = invoke_hook(args.root, args.input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(json.dumps({'status':'blocked','reason':str(exc)}), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
