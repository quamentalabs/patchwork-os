# SPDX-License-Identifier: MIT
"""Explicitly configured, owned local processes. Process success is not agent approval."""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import time
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

RUNTIMES = ("cc", "codex", "agy", "muse")
FINAL_STATES = {"completed", "failed", "closed", "blocked"}
SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")


class RuntimeErrorDetail(ValueError):
    """An actionable refusal without converting failure into a success record."""


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeErrorDetail("JSON_OBJECT_REQUIRED")
    return data


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for attempt in range(25):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 24:
                raise
            time.sleep(.02)


def process_birth(pid: int) -> str | None:
    """OS creation identity, not a PID-only liveness claim."""
    if os.name == "nt":
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
            if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time), ctypes.byref(kernel_time), ctypes.byref(user_time)):
                return None
            return str((creation.dwHighDateTime << 32) | creation.dwLowDateTime)
        finally:
            kernel.CloseHandle(handle)
    if sys.platform.startswith("linux"):
        try:
            fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            return fields[19]
        except (OSError, IndexError):
            return None
    # Unsupported identity measurement fails closed rather than using kill(pid, 0).
    return None


def initialize_workspace(root: Path) -> dict[str, Any]:
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    directory = root / ".patchwork"
    if directory.is_symlink():
        raise RuntimeErrorDetail("STATE_SYMLINK_REFUSED")
    directory.mkdir(exist_ok=True)
    (directory / "runs").mkdir(exist_ok=True)
    for name, data in (
        ("owner.json", {"schema_version": 1, "owner_id": uuid.uuid4().hex, "api_token": secrets.token_urlsafe(32)}),
        ("config.json", {"schema_version": 1, "runtimes": {name: {"executable": None, "args": [], "model": None, "effort": None, "delivery": "stdin"} for name in RUNTIMES}, "binding": None, "local_judge": None}),
    ):
        path = directory / name
        try:
            with path.open("x", encoding="utf-8") as stream:
                json.dump(data, stream, indent=2)
                stream.write("\n")
            if os.name != "nt":
                path.chmod(0o600)
        except FileExistsError:
            pass
    return {"root": str(root), "config": str(directory / "config.json"), "status": "initialized"}


class RuntimeBackend(ABC):
    @abstractmethod
    def probe(self, runtime: str) -> dict[str, Any]: ...
    @abstractmethod
    def launch(self, runtime: str, prompt: str, **options: Any) -> dict[str, Any]: ...
    @abstractmethod
    def observe(self, run_id: str) -> dict[str, Any]: ...
    @abstractmethod
    def collect(self, run_id: str) -> dict[str, Any]: ...
    @abstractmethod
    def close(self, run_id: str) -> dict[str, Any]: ...


class LocalRuntimeBackend(RuntimeBackend):
    """Four family adapters share only the explicitly supplied argv contract.

    No vendor flags, models, home directory or native acceptance are inferred.
    Noninteractive vendor commands must be configured by their operator. Terminal
    mode is one bounded native stdin exchange; it is not a PTY or a local shell.
    """

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.state_root = self.root / ".patchwork"
        if self.state_root.is_symlink():
            raise RuntimeErrorDetail("STATE_SYMLINK_REFUSED")
        self.config_path = self.state_root / "config.json"
        self.owner = read_json(self.state_root / "owner.json")
        self.owner_id = self.owner["owner_id"]

    def _config(self) -> dict[str, Any]:
        config = read_json(self.config_path)
        if config.get("schema_version") != 1:
            raise RuntimeErrorDetail("CONFIG_VERSION_UNSUPPORTED")
        return config

    def _runtime(self, runtime: str) -> dict[str, Any]:
        if runtime not in RUNTIMES:
            raise RuntimeErrorDetail("RUNTIME_UNSUPPORTED")
        config = self._config().get("runtimes", {}).get(runtime, {})
        executable = config.get("executable")
        if not executable or not Path(executable).is_absolute() or not Path(executable).is_file():
            raise RuntimeErrorDetail("RUNTIME_NOT_CONFIGURED")
        if not isinstance(config.get("args"), list) or not all(isinstance(arg, str) for arg in config["args"]):
            raise RuntimeErrorDetail("ARGS_ARRAY_REQUIRED")
        if config.get("delivery") not in {"stdin", "task_file"}:
            raise RuntimeErrorDetail("DELIVERY_UNSUPPORTED")
        return config

    def probe(self, runtime: str) -> dict[str, Any]:
        try:
            config = self._runtime(runtime)
            return {"terminal_capability": terminal_capability()[0], "terminal_reason": terminal_capability()[1], "runtime": runtime, "status": "configured", "executable": config["executable"], "model": config.get("model"), "effort": config.get("effort"), "native_acceptance": "not_run", "execution_measured": False}
        except (RuntimeErrorDetail, OSError) as exc:
            return {"terminal_capability": "blocked", "terminal_reason": "INTERACTIVE_TERMINAL_UNAVAILABLE", "runtime": runtime, "status": "blocked", "reason": str(exc), "native_acceptance": "not_run"}

    def run_path(self, run_id: str) -> Path:
        if not isinstance(run_id, str) or not SAFE_ID.fullmatch(run_id):
            raise RuntimeErrorDetail("INVALID_RUN_ID")
        runs = self.state_root / "runs"
        path = runs / run_id
        if runs.is_symlink() or path.is_symlink() or path.resolve().parent != runs.resolve():
            raise RuntimeErrorDetail("RUN_PATH_REFUSED")
        return path

    def _read_run(self, run_id: str) -> dict[str, Any]:
        path = self.run_path(run_id)
        if (path / "run.json").is_symlink():
            raise RuntimeErrorDetail("RUN_PATH_REFUSED")
        row = read_json(path / "run.json")
        if row.get("owner_id") != self.owner_id or row.get("run_id") != run_id or row.get("workspace") != str(self.root):
            raise RuntimeErrorDetail("FOREIGN_RUN")
        return row

    def launch(self, runtime: str, prompt: str, *, model: str | None = None, effort: str | None = None, mode: str = "task", submission_id: str | None = None) -> dict[str, Any]:
        config = self._runtime(runtime)
        if mode == "terminal" and terminal_capability()[0] != "available":
            raise RuntimeErrorDetail("INTERACTIVE_TERMINAL_UNAVAILABLE")
        if mode not in {"task", "terminal"} or not isinstance(prompt, str) or not prompt or len(prompt.encode("utf-8")) > 1024 * 1024:
            raise RuntimeErrorDetail("INVALID_SUBMISSION")
        if model is not None and (not isinstance(model, str) or not model):
            raise RuntimeErrorDetail("INVALID_MODEL")
        if effort is not None and (not isinstance(effort, str) or not effort):
            raise RuntimeErrorDetail("INVALID_EFFORT")
        resolved_model, resolved_effort = model or config.get("model"), effort or config.get("effort")
        joined = "\n".join(config["args"])
        if resolved_model and "{model}" not in joined:
            raise RuntimeErrorDetail("MODEL_NOT_DELIVERED")
        if resolved_effort and "{effort}" not in joined:
            raise RuntimeErrorDetail("EFFORT_NOT_DELIVERED")
        if "{home}" in joined and not config.get("home"):
            raise RuntimeErrorDetail("HOME_NOT_CONFIGURED")
        if config["delivery"] == "task_file" and "{task_file}" not in joined:
            raise RuntimeErrorDetail("TASK_FILE_NOT_DELIVERED")
        submission_id = submission_id or uuid.uuid4().hex
        if not SAFE_ID.fullmatch(submission_id):
            raise RuntimeErrorDetail("INVALID_SUBMISSION_ID")
        fingerprint = digest(json.dumps([runtime, prompt, model, effort, mode], ensure_ascii=False).encode())
        run_id = "run-" + uuid.uuid4().hex
        index = self.state_root / ("submission-" + submission_id + ".json")
        try:
            with index.open("x", encoding="utf-8") as stream:
                json.dump({"run_id": run_id, "fingerprint": fingerprint}, stream)
        except FileExistsError:
            previous = read_json(index)
            if previous.get("fingerprint") != fingerprint:
                raise RuntimeErrorDetail("SUBMISSION_CONFLICT")
            # A concurrent initializing submission is never launched a second time.
            for _ in range(100):
                if (self.run_path(previous["run_id"]) / "run.json").is_file():
                    return self.observe(previous["run_id"])
                time.sleep(.01)
            raise RuntimeErrorDetail("SUBMISSION_INITIALIZING")
        directory = self.run_path(run_id)
        directory.mkdir()
        task_file = directory / "input.txt"
        task_file.write_bytes(prompt.encode("utf-8"))
        values = {"model": resolved_model or "", "effort": resolved_effort or "", "task_file": str(task_file), "home": config.get("home") or ""}
        try:
            args = [arg.format_map(values) for arg in config["args"]]
        except (ValueError, KeyError) as exc:
            raise RuntimeErrorDetail("UNKNOWN_ARG_PLACEHOLDER") from exc
        row = {"schema_version": 1, "owner_id": self.owner_id, "run_id": run_id, "submission_id": submission_id, "workspace": str(self.root), "runtime": runtime, "mode": mode, "status": "starting", "created_at": time.time(), "model": {"requested": model, "resolved": resolved_model, "observed": None}, "effort": {"requested": effort, "resolved": resolved_effort, "observed": None}, "argv": [config["executable"], *args], "cwd": str(self.root), "home": config.get("home"), "delivery": {"method": config["delivery"], "status": "pending", "input_sha256": digest(prompt.encode())}, "lease": {"id": uuid.uuid4().hex, "owner_id": self.owner_id, "released": False}, "process": {"pid": None, "birth": None}, "supervisor": {"pid": None, "birth": None}, "exit_code": None, "native_session_id": None, "artifact_completion": "not_run", "native_acceptance": "not_run", "review_acceptance": "not_run", "completion_allowed": False}
        atomic_json(directory / "run.json", row)
        # Supervisor is an installed public module, never a parent checkout script.
        env = os.environ.copy()
        package_root = str(Path(__file__).resolve().parent.parent)
        env["PYTHONPATH"] = package_root
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        with (directory / "supervisor.log").open("ab") as log:
            supervisor = subprocess.Popen([sys.executable, "-m", "patchwork_os.runtime_backend", "supervise", str(self.root), run_id], cwd=self.root, env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log, creationflags=flags, start_new_session=os.name != "nt")
        for _ in range(100):
            current = self.observe(run_id)
            if current["status"] != "starting" or supervisor.poll() is not None:
                return current
            time.sleep(.01)
        return self.observe(run_id)

    def observe(self, run_id: str) -> dict[str, Any]:
        row = self._read_run(run_id)
        if row["status"] == "running":
            expected = row["process"]
            row["process_identity_current"] = process_birth(expected["pid"]) == expected["birth"]
        return row

    def collect(self, run_id: str) -> dict[str, Any]:
        row = self.observe(run_id)
        path = self.run_path(run_id) / "transcript.bin"
        raw = path.read_bytes() if path.is_file() else b""
        row.update({"output": raw.decode("utf-8", errors="replace"), "transcript": {"path": str(path), "sha256": digest(raw), "bytes": len(raw), "complete": row["status"] in FINAL_STATES}, "execution_success": row.get("exit_code") == 0 and row["status"] == "completed", "collected_at": time.time()})
        atomic_json(self.run_path(run_id) / "collection.json", row)
        return row

    def close(self, run_id: str) -> dict[str, Any]:
        row = self.observe(run_id)
        if row["status"] not in FINAL_STATES:
            identity = row["process"]
            if not identity.get("birth") or process_birth(identity["pid"]) != identity["birth"]:
                raise RuntimeErrorDetail("PROCESS_IDENTITY_MISMATCH")
            (self.run_path(run_id) / "stop.request").touch(exist_ok=True)
            for _ in range(100):
                row = self.observe(run_id)
                if row["status"] in FINAL_STATES:
                    break
                time.sleep(.05)
            if row["status"] not in FINAL_STATES:
                raise RuntimeErrorDetail("CLOSE_PENDING")
        row["lease"]["released"] = True
        row["closed_at"] = time.time()
        atomic_json(self.run_path(run_id) / "run.json", row)
        return row

    def terminal_input(self, run_id: str, text: str) -> dict[str, Any]:
        row = self.observe(run_id)
        if row["mode"] != "terminal" or row["status"] != "running":
            raise RuntimeErrorDetail("TERMINAL_NOT_RUNNING")
        identity = row["process"]
        if not identity.get("birth") or process_birth(identity["pid"]) != identity["birth"]:
            raise RuntimeErrorDetail("PROCESS_IDENTITY_MISMATCH")
        if not isinstance(text, str) or not text or len(text.encode("utf-8")) > 65536:
            raise RuntimeErrorDetail("INVALID_TERMINAL_INPUT")
        queue = self.run_path(run_id) / "input-queue"
        queue.mkdir(exist_ok=True)
        name = f"{time.time_ns():020d}-{uuid.uuid4().hex}"
        temporary = queue / (name + ".tmp")
        temporary.write_bytes(text.encode("utf-8"))
        os.replace(temporary, queue / (name + ".input"))
        return {"run_id": run_id, "status": "queued", "input_id": name}

    def list_runs(self) -> list[dict[str, Any]]:
        return [self.observe(path.name) for path in sorted((self.state_root / "runs").iterdir()) if path.is_dir() and not path.is_symlink()]


def terminal_capability() -> tuple[str, str | None]:
    if os.name == "nt":
        try:
            import winpty
            return "available", None
        except ImportError:
            return "blocked", "PYWINPTY_NOT_INSTALLED"
    if os.name == "posix":
        return "available", None
    return "blocked", "PLATFORM_UNSUPPORTED"


def supervise(root: Path, run_id: str) -> int:
    backend = LocalRuntimeBackend(root)
    row = backend._read_run(run_id)
    if row["mode"] == "terminal":
        from .terminal import supervise_terminal
        return supervise_terminal(backend, row)
    directory = backend.run_path(run_id)
    row["supervisor"] = {"pid": os.getpid(), "birth": process_birth(os.getpid())}
    env = os.environ.copy()
    if row.get("home"):
        # Explicit home is supplied only to this child, never global settings.
        env["HOME"] = row["home"]
        env["USERPROFILE"] = row["home"]
    try:
        with (directory / "transcript.bin").open("wb") as transcript, (directory / "input.txt").open("rb") as input_stream:
            child = subprocess.Popen(row["argv"], cwd=row["cwd"], env=env, stdin=input_stream if row["delivery"]["method"] == "stdin" else subprocess.DEVNULL, stdout=transcript, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            birth = process_birth(child.pid)
            row["process"] = {"pid": child.pid, "birth": birth}
            row["status"] = "running"
            row["delivery"]["status"] = "submitted"
            atomic_json(directory / "run.json", row)
            stopped = False
            while child.poll() is None:
                if (directory / "stop.request").exists():
                    if birth and process_birth(child.pid) == birth:
                        child.terminate()
                        try:
                            child.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            # The owned Popen handle identifies the original process on Windows.
                            if process_birth(child.pid) == birth:
                                child.kill()
                            child.wait(timeout=3)
                        stopped = True
                    else:
                        raise RuntimeErrorDetail("PROCESS_IDENTITY_MISMATCH")
                    break
                time.sleep(.025)
            row["exit_code"] = child.wait()
            row["status"] = "closed" if stopped else "completed" if row["exit_code"] == 0 else "failed"
    except (OSError, RuntimeErrorDetail, subprocess.SubprocessError) as exc:
        row["status"] = "blocked"
        row["reason"] = str(exc)
    row["finished_at"] = time.time()
    atomic_json(directory / "run.json", row)
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "supervise":
        raise SystemExit(supervise(Path(sys.argv[2]), sys.argv[3]))
    raise SystemExit(2)
