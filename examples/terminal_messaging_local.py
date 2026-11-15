# SPDX-License-Identifier: Apache-2.0
"""Send one message to a real local child and accept only its own exact acknowledgement.

    python examples/terminal_messaging_local.py --workspace ../patchwork-messaging-demo

The child is `terminal_messaging_consumer.py`, started from an argv list with a
stdin pipe. This exercises the `owned-pipe` backend on this machine and nothing
else: no vendor runtime and no IDE terminal is started or claimed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from patchwork_os.terminal_messaging import (
    COMPLETED,
    Messenger,
    ObservationPolicy,
    OwnedPipeAdapter,
    create_envelope,
    remove_payload,
    start_owned_pipe_child,
)


def run(workspace: Path) -> dict:
    if workspace.exists():
        raise SystemExit(f"Refusing an existing workspace: {workspace}")
    child_dir = workspace / "recipient"
    child_dir.mkdir(parents=True)
    consumer = Path(__file__).resolve().with_name("terminal_messaging_consumer.py")
    child = start_owned_pipe_child(
        [sys.executable, "-B", str(consumer), "--session", "recipient-session", "--dir", str(child_dir),
         "--width", "60"], cwd=workspace)
    adapter = OwnedPipeAdapter(child, session_id="recipient-session", workdir=child_dir)
    try:
        if not adapter.wait_ready(10.0):
            raise SystemExit("The child did not publish its input area.")
        envelope = create_envelope(
            source_session="sender-session", target=adapter.identity(),
            body="Reply with the acknowledgement named inside this payload.",
            payload_dir=workspace / "payloads", ttl_seconds=60.0)
        messenger = Messenger(
            discovery=adapter, capture=adapter, input=adapter, acknowledgement=adapter,
            journal_dir=workspace / "journal", policy=ObservationPolicy(typed_wait=5.0, ack_wait=10.0),
            adapter_name="owned-pipe")
        delivered = messenger.deliver(envelope)
        released = messenger.release(envelope) if delivered["status"] == "acknowledged" else delivered
        events = [row["event"] for row in messenger.journal(envelope).events()]
        remove_payload(envelope.payload)
    finally:
        child.stdin.close()
        child.wait(timeout=10)
    passed = released["state"] == COMPLETED and events.index("intent_submit") < events.index("acknowledged")
    return {
        "status": "passed" if passed else "failed",
        "backend": "owned-pipe", "live_local_child": True, "child_exit": child.returncode,
        "message_id": envelope.message_id, "state": released["state"], "journal_events": events,
        "acknowledgement": envelope.ack_text() if passed else None,
        "vendor_runtimes_exercised": [], "ide_terminals_exercised": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--workspace", required=True)
    args = parser.parse_args(argv)
    result = run(Path(args.workspace).resolve())
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
