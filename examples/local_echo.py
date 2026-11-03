# SPDX-License-Identifier: Apache-2.0
"""Run the installed pwos CLI against a local Python echo process."""

from __future__ import annotations

import argparse
import hashlib
from importlib import resources
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import time

import patchwork_os


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True,
                        help="New sample directory outside the checkout.")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    checkout = Path(__file__).resolve().parents[1]
    if workspace.is_relative_to(checkout):
        parser.error("Choose a workspace outside the checkout.")
    if workspace.exists():
        parser.error("Workspace already exists; choose a new sample directory.")

    installed = Path(patchwork_os.__file__).resolve()
    require(not installed.is_relative_to(checkout),
            "Install with 'python -m pip install .' in a virtual environment first.")
    cli = Path(sysconfig.get_path("scripts")) / ("pwos.exe" if os.name == "nt" else "pwos")
    require(cli.is_file(), "Installed pwos entry point was not found.")
    skill_root = resources.files("patchwork_os").joinpath("resources", "skills")
    index = skill_root.joinpath("INDEX.md").read_bytes()
    skill_count = sum(item.is_dir() and item.joinpath("SKILL.md").is_file()
                      for item in skill_root.iterdir())
    require(skill_count == 18, "Expected all 18 packaged procedure resources.")

    workspace.mkdir(parents=True)
    operations: list[str] = []

    def command(*arguments: str) -> dict:
        result = subprocess.run(
            [str(cli), "--root", str(workspace), *arguments],
            cwd=workspace, capture_output=True, text=True, encoding="utf-8",
            timeout=20, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if result.returncode:
            raise RuntimeError(f"pwos {arguments[0]} failed: {result.stderr.strip()}")
        operations.append(arguments[0])
        return json.loads(result.stdout)

    command("init")
    payload = workspace / "echo_backend.py"
    shutil.copyfile(Path(__file__).with_name("echo_backend.py"), payload)
    config_path = workspace / ".patchwork" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    # "muse" is only a configuration slot here, not a native vendor session.
    config["runtimes"]["muse"] = {
        "executable": str(Path(sys.executable).resolve()),
        "args": ["-u", str(payload)],
        "delivery": "stdin", "model": None, "effort": None,
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    require(command("doctor")["muse"]["status"] == "configured", "Echo backend is blocked.")
    task = workspace / "task.txt"
    task.write_text("Hello from Patchwork-OS.\n", encoding="utf-8")
    expected = "PATCHWORK_ECHO: " + task.read_text(encoding="utf-8")
    launched = command("run", "muse", "--task-file", str(task))
    run_id = launched["run_id"]
    try:
        deadline = time.monotonic() + 20
        while True:
            state = command("status", run_id)
            if state["status"] in {"completed", "failed", "closed", "blocked"}:
                break
            require(time.monotonic() < deadline, "Echo process did not finish within 20 seconds.")
            time.sleep(0.1)
        collected = command("collect", run_id)
        require(collected["execution_success"] is True, "Echo process did not exit successfully.")
        require(collected["output"] == expected, "Collected echo text differs from the task.")
        output_hash = "sha256:" + hashlib.sha256(expected.encode("utf-8")).hexdigest()
        require(collected["transcript"]["sha256"] == output_hash, "Transcript hash differs.")
        require(collected["transcript"]["complete"] is True, "Transcript is incomplete.")
        require(collected["native_acceptance"] == "not_run", "Unexpected native acceptance.")
        require(collected["review_acceptance"] == "not_run", "Unexpected review acceptance.")
        require(collected["completion_allowed"] is False, "Unexpected native completion claim.")
    finally:
        closed = command("close", run_id)
        require(closed["lease"]["released"] is True, "Run lease was not released.")
    print(json.dumps({
        "status": "passed", "workspace": str(workspace),
        "installed_module": str(installed), "run_id": run_id,
        "operations": operations, "transcript_sha256": output_hash,
        "packaged_skill_count": skill_count,
        "resource_index_sha256": hashlib.sha256(index).hexdigest(),
        "lease_released": closed["lease"]["released"],
        "native_acceptance": collected["native_acceptance"],
        "review_acceptance": collected["review_acceptance"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
