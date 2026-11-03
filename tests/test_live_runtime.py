# SPDX-License-Identifier: Apache-2.0
import json
import sys
import time
from pathlib import Path

import pytest

from patchwork_os.runtime_backend import LocalRuntimeBackend, RuntimeErrorDetail, initialize_workspace


def configured(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    script = tmp_path / "sample_cli.py"
    script.write_text("import sys,time\nprint('INPUT:'+sys.stdin.read(),flush=True)\n", encoding="utf-8")
    cfg = json.loads((root / ".patchwork/config.json").read_text())
    cfg["runtimes"]["muse"] = {"executable": sys.executable, "args": [str(script), "{model}"], "model": "sample-model", "delivery": "stdin"}
    (root / ".patchwork/config.json").write_text(json.dumps(cfg))
    return LocalRuntimeBackend(root)


def finished(backend, run_id):
    for _ in range(160):
        row = backend.observe(run_id)
        if row["status"] in {"completed", "failed", "closed", "blocked"}:
            return row
        time.sleep(.025)
    raise AssertionError("bounded fixture did not finish")


def test_real_process_roundtrip_does_not_fabricate_acceptance(tmp_path):
    backend = configured(tmp_path)
    job = backend.launch("muse", "hello; this is input, not shell", submission_id="sample")
    row = finished(backend, job["run_id"])
    assert row["status"] == "completed"
    result = backend.collect(job["run_id"])
    assert "INPUT:hello; this is input, not shell" in result["output"]
    assert result["execution_success"] is True
    assert result["model"] == {"requested": None, "resolved": "sample-model", "observed": None}
    assert result["native_acceptance"] == "not_run"
    assert result["review_acceptance"] == "not_run"
    assert result["completion_allowed"] is False
    assert result["process"]["pid"] > 0 and result["process"]["birth"]
    assert backend.launch("muse", "hello; this is input, not shell", submission_id="sample")["run_id"] == job["run_id"]
    with pytest.raises(RuntimeErrorDetail, match="SUBMISSION_CONFLICT"):
        backend.launch("muse", "different", submission_id="sample")
    closed = backend.close(job["run_id"])
    assert closed["lease"]["released"] is True


def test_missing_cli_unknown_model_and_foreign_owner_fail_closed(tmp_path):
    backend = configured(tmp_path)
    assert backend.probe("cc")["status"] == "blocked"
    with pytest.raises(RuntimeErrorDetail, match="RUNTIME_NOT_CONFIGURED"):
        backend.launch("cc", "task")
    with pytest.raises(RuntimeErrorDetail, match="MODEL_NOT_DELIVERED"):
        cfg = json.loads(backend.config_path.read_text())
        cfg["runtimes"]["muse"]["args"] = ["sample.py"]
        backend.config_path.write_text(json.dumps(cfg))
        backend.launch("muse", "task", model="unexpected-model")
    with pytest.raises(RuntimeErrorDetail, match="INVALID_RUN_ID"):
        backend.observe("../other")
    backend = configured(tmp_path / "second")
    job = backend.launch("muse", "sample")
    finished(backend, job["run_id"])
    path = backend.run_path(job["run_id"]) / "run.json"
    data = json.loads(path.read_text())
    data["owner_id"] = "foreign"
    path.write_text(json.dumps(data))
    with pytest.raises(RuntimeErrorDetail, match="FOREIGN_RUN"):
        backend.close(job["run_id"])


def test_failed_process_terminal_mode_and_pid_reuse(tmp_path):
    backend = configured(tmp_path)
    cfg = json.loads(backend.config_path.read_text())
    cfg["runtimes"]["muse"]["args"] = ["-c", "import sys; print(sys.stdin.read()); sys.exit(7)", "{model}"]
    backend.config_path.write_text(json.dumps(cfg))
    job = backend.launch("muse", "plain input")
    row = finished(backend, job["run_id"])
    assert row["status"] == "failed"
    assert backend.collect(job["run_id"])["execution_success"] is False
    path = backend.run_path(job["run_id"]) / "run.json"
    row["status"] = "running"
    row["process"]["birth"] = "reused-pid"
    path.write_text(json.dumps(row))
    with pytest.raises(RuntimeErrorDetail, match="PROCESS_IDENTITY_MISMATCH"):
        backend.close(job["run_id"])


def test_initializer_never_overwrites_configuration(tmp_path):
    root = tmp_path / "sample"
    initialize_workspace(root)
    path = root / ".patchwork/config.json"
    path.write_text('{"schema_version":1,"runtimes":{"custom":{}}}')
    initialize_workspace(root)
    assert "custom" in path.read_text()
