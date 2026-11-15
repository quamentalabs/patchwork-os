# SPDX-License-Identifier: Apache-2.0
"""Cross-terminal messaging: one protocol entry, four adapter legs, a journaled state machine.

A sender types one short pointer line into another live terminal session and
treats nothing as delivered until the recipient's own transcript says so. The
four legs are separate interfaces because they fail separately:

- discovery and binding: is this the exact process or pane, in the same generation?
- capture: what does the input area show right now? Read-only.
- input: write text, and separately, submit it.
- acknowledgement: what did the recipient record after a pinned transcript position?

Runtime and IDE names are labels. Only an observed terminal backend selects a
route, and an unknown backend is unsupported. A content hash here is an
integrity check, not authorization: the caller owns the authority to send.

The journal records an intent before each side effect. A reentry after an
uncertain submit observes and never types or submits again, so this protocol
prefers a missed delivery to a duplicate one. It does not provide exactly-once
delivery.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import time
import unicodedata
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

from .runtime_backend import process_birth

PROTOCOL_VERSION = "pwtm/1"
POINTER_PREFIX = "PWTM1"

BACKEND_WINDOWS_CONSOLE = "windows-console"
BACKEND_MANAGED_PTY = "managed-pty"
BACKEND_TMUX = "tmux"
BACKEND_IDE_BRIDGE = "ide-bridge"
BACKEND_OWNED_PIPE = "owned-pipe"
BACKEND_UNKNOWN = "unknown"

HOST_WINDOWS = "windows"
HOST_LINUX = "linux"
HOST_WSL_LINUX = "wsl-linux"
HOST_WSL_WINDOWS_EXECUTABLE = "wsl-windows-executable"

PREPARED = "prepared"
TYPED = "typed"
SUBMIT_ATTEMPTED = "submit_attempted"
OBSERVED = "observed"
ACKNOWLEDGED = "acknowledged"
COMPLETED = "completed"
REFUSED = "refused"
UNCERTAIN = "uncertain"

#: What this package has actually exercised. "not_run" is a measurement gap, not a verdict.
BACKEND_MATRIX: tuple[dict[str, str], ...] = (
    {"backend": BACKEND_OWNED_PIPE, "hosts": "windows, linux", "identity": "pid and OS creation time",
     "adapter": "OwnedPipeAdapter", "status": "live-local"},
    {"backend": BACKEND_TMUX, "hosts": "linux, wsl-linux", "identity": "server socket and pane id",
     "adapter": "argv builders only", "status": "not_run"},
    {"backend": BACKEND_MANAGED_PTY, "hosts": "windows, linux", "identity": "pid and OS creation time",
     "adapter": "none", "status": "not_run"},
    {"backend": BACKEND_WINDOWS_CONSOLE, "hosts": "windows", "identity": "pid and OS creation time",
     "adapter": "none", "status": "not_run"},
    {"backend": BACKEND_IDE_BRIDGE, "hosts": "any", "identity": "bridge-defined terminal id",
     "adapter": "none", "status": "not_run"},
)

_TOKEN = re.compile(r"[A-Za-z0-9_-]{8,64}\Z")
_SESSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class Refusal(Exception):
    """A named reason for not acting. Carrying a code keeps a refusal from reading as a crash."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(code if not detail else f"{code}: {detail}")
        self.code = code
        self.detail = detail


def backend_status(backend: str) -> str:
    """The measured status of a backend, or "unsupported" for anything not listed."""
    for row in BACKEND_MATRIX:
        if row["backend"] == backend:
            return row["status"]
    return "unsupported"


def current_host() -> str:
    """The host this process runs on. A Windows executable started from WSL reports windows."""
    if os.name == "nt":
        return HOST_WINDOWS
    return HOST_WSL_LINUX if "microsoft" in platform.release().lower() else HOST_LINUX


# ---------------------------------------------------------------------------
# identity, payload, envelope


@dataclass(frozen=True)
class TargetIdentity:
    """Either a process in one generation, or a pane on one multiplexer server."""

    session_id: str
    backend: str
    host: str
    pid: int | None = None
    generation: str | None = None
    server: str | None = None
    pane: str | None = None

    def validate(self) -> None:
        if not _SESSION.match(self.session_id or ""):
            raise Refusal("TARGET_SESSION_INVALID")
        by_process = self.pid is not None and bool(self.generation)
        by_pane = bool(self.server) and bool(self.pane)
        if by_process == by_pane:
            raise Refusal("TARGET_IDENTITY_INCOMPLETE", "need pid and generation, or server and pane")


@dataclass(frozen=True)
class PayloadRef:
    """An immutable UTF-8 payload on disk, named by path and digest."""

    path: str
    sha256: str
    size: int

    def read_verified(self) -> bytes:
        try:
            data = Path(self.path).read_bytes()
        except OSError as error:
            raise Refusal("PAYLOAD_UNREADABLE", type(error).__name__) from error
        if len(data) != self.size or hashlib.sha256(data).hexdigest() != self.sha256:
            raise Refusal("PAYLOAD_DIGEST_MISMATCH")
        try:
            data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise Refusal("PAYLOAD_NOT_UTF8") from error
        return data


@dataclass(frozen=True)
class Envelope:
    protocol: str
    message_id: str
    source_session: str
    target_session: str
    target: TargetIdentity
    payload: PayloadRef
    ack_token: str
    expires_at: float

    def pointer_line(self) -> str:
        """The only text typed into the target. The acknowledgement token is not in it."""
        return f"{POINTER_PREFIX} {self.message_id} sha256:{self.payload.sha256} {self.payload.path}"

    def ack_text(self) -> str:
        """The exact text the recipient must record. It binds token, message id and payload digest."""
        return f"ACK {self.ack_token} id={self.message_id} sha256={self.payload.sha256}"

    def fingerprint(self) -> str:
        body = json.dumps(asdict(self), sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(body).hexdigest()


def create_envelope(
    *,
    source_session: str,
    target: TargetIdentity,
    body: str,
    payload_dir: Path | str,
    ttl_seconds: float,
    now: Callable[[], float] = time.time,
    message_id: str | None = None,
    ack_token: str | None = None,
) -> Envelope:
    """Write the payload file once and return the envelope that names it.

    The acknowledgement token lives inside the payload. A recipient can produce
    the exact acknowledgement only by reading the payload, so a correct
    acknowledgement is also evidence that the content was opened.
    """
    target.validate()
    if not _SESSION.match(source_session or ""):
        raise Refusal("SOURCE_SESSION_INVALID")
    if source_session == target.session_id:
        raise Refusal("SELF_TARGET")
    if ttl_seconds <= 0:
        raise Refusal("TTL_INVALID")
    message_id = message_id or uuid.uuid4().hex
    ack_token = ack_token or uuid.uuid4().hex
    if not _TOKEN.match(message_id) or not _TOKEN.match(ack_token):
        raise Refusal("IDENTIFIER_INVALID")
    document = json.dumps(
        {"protocol": PROTOCOL_VERSION, "message_id": message_id, "source_session": source_session,
         "target_session": target.session_id, "ack_token": ack_token, "body": body},
        sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")
    directory = Path(payload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{message_id}.payload.json"
    try:
        with open(path, "xb") as handle:
            handle.write(document)
    except FileExistsError as error:
        raise Refusal("PAYLOAD_PATH_OCCUPIED") from error
    try:
        os.chmod(path, 0o444)
    except OSError:
        pass
    line_path = path.resolve().as_posix()
    if any(unicodedata.category(ch) == "Cc" for ch in line_path) or line_path != line_path.strip():
        raise Refusal("PAYLOAD_PATH_NOT_TYPEABLE")
    return Envelope(
        protocol=PROTOCOL_VERSION, message_id=message_id, source_session=source_session,
        target_session=target.session_id, target=target,
        payload=PayloadRef(path=line_path, sha256=hashlib.sha256(document).hexdigest(), size=len(document)),
        ack_token=ack_token, expires_at=now() + ttl_seconds,
    )


def remove_payload(payload: PayloadRef) -> bool:
    """Delete a payload file its creator no longer needs. True when the file is gone.

    Payload files are marked read-only, which on Windows also blocks deleting
    the directory that holds them. This clears the mark first.
    """
    path = Path(payload.path)
    try:
        os.chmod(path, 0o666)
        path.unlink()
    except FileNotFoundError:
        return True
    except OSError:
        return False
    return True


# ---------------------------------------------------------------------------
# observations and the four adapter legs


@dataclass(frozen=True)
class TargetObservation:
    alive: bool
    identity: TargetIdentity | None
    backend: str
    readers: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ScreenObservation:
    """The input area. `known` False means the adapter could not tell.

    Rows are what is drawn, and a terminal pads every row with blanks, so rows
    alone cannot show a draft made of spaces or spaces after a draft. The only
    authority for what the input area holds is the exact input buffer,
    `composer_text`. Without it, emptiness and exactness are unknown and nothing
    is typed.

    `cursor_cells` (a cell offset from the start of the prompt, counted across
    wrapped rows) is supplementary. It is never authority: someone can type
    spaces and move the caret back to where an empty input area would put it,
    and rows and cursor then both look empty.
    """

    known: bool
    composer_rows: tuple[str, ...] = ()
    width: int = 0
    prompt: str = ""
    modal: bool = False
    composer_text: str | None = None
    cursor_cells: int | None = None


@dataclass(frozen=True)
class TranscriptCursor:
    source: str
    offset: int
    head_sha256: str
    tail_sha256: str
    window: int
    file_id: str = ""


@dataclass(frozen=True)
class TranscriptRead:
    valid: bool
    reason: str | None = None
    records: tuple[Mapping[str, Any], ...] = ()
    partial_tail: bool = False
    malformed: int = 0


@runtime_checkable
class DiscoveryAdapter(Protocol):
    def observe_target(self, target: TargetIdentity) -> TargetObservation: ...


@runtime_checkable
class CaptureAdapter(Protocol):
    def capture(self, target: TargetIdentity) -> ScreenObservation: ...


@runtime_checkable
class InputAdapter(Protocol):
    supported_backends: frozenset[str]

    def type_text(self, target: TargetIdentity, text: str) -> None: ...

    def submit(self, target: TargetIdentity) -> None: ...


@runtime_checkable
class AcknowledgementAdapter(Protocol):
    def pin(self) -> TranscriptCursor: ...

    def read_after(self, cursor: TranscriptCursor) -> TranscriptRead: ...


# ---------------------------------------------------------------------------
# exact reconstruction of wrapped text


def _cell_width(character: str) -> int:
    if unicodedata.category(character) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1


def wrap_cells(text: str, width: int) -> list[str]:
    """Rows a terminal of `width` cells shows for `text`. A wide character never straddles a row."""
    if width < 2:
        raise ValueError("width must be at least 2 cells")
    rows: list[str] = []
    current: list[str] = []
    used = 0
    for character in text:
        cells = _cell_width(character)
        if used + cells > width:
            rows.append("".join(current))
            current, used = [], 0
        current.append(character)
        used += cells
    rows.append("".join(current))
    return rows


def display_cells(text: str) -> int:
    """How many terminal cells `text` occupies under the width model used here."""
    return sum(_cell_width(character) for character in text)


def _padded(row: str, width: int) -> str | None:
    cells = display_cells(row)
    return None if cells > width else row + " " * (width - cells)


def composer_evidence(screen: ScreenObservation) -> str:
    """What the observation carries: "buffer", "cursor" or "none". Only "buffer" is authority."""
    if not screen.known:
        return "none"
    if screen.composer_text is not None:
        return "buffer"
    if screen.cursor_cells is not None:
        return "cursor"
    return "none"


def screen_shows_exactly(screen: ScreenObservation, text: str) -> bool:
    """True only when the input area is proven to be the prompt followed by exactly `text`.

    Two things must agree. The authority: the input buffer equals `text`. And
    the geometry: every drawn row equals the row `text` should occupy. Rows
    alone are never enough, because right-edge padding hides spaces, and a
    cursor position is not enough either. A substring match or stripped
    comparison is never used, because it would accept a foreign draft that
    merely contains the text.
    """
    if not screen.known or screen.modal or screen.width < 2:
        return False
    if composer_evidence(screen) != "buffer":
        return False
    if screen.composer_text != text:
        return False
    expected = wrap_cells(screen.prompt + text, screen.width)
    observed = list(screen.composer_rows)
    if len(observed) != len(expected):
        return False
    for seen, wanted in zip(observed, expected):
        if _padded(seen, screen.width) != _padded(wanted, screen.width) or _padded(seen, screen.width) is None:
            return False
    return True


def composer_is_empty(screen: ScreenObservation) -> bool:
    return screen_shows_exactly(screen, "")


def typeable(text: str) -> bool:
    """One line, no control characters, no edge whitespace: what a pointer line must be."""
    return bool(text) and text == text.strip() and not any(unicodedata.category(ch) == "Cc" for ch in text)


# ---------------------------------------------------------------------------
# transcript reading with a pinned position


class FileTranscript:
    """A JSON-lines transcript read strictly after a pinned byte position.

    The cursor holds digests of the bytes before it. A shorter file, a changed
    prefix, or a different file under the same name invalidates the cursor;
    nothing read through an invalid cursor can promote a message.
    """

    def __init__(self, path: Path | str, *, window: int = 65536) -> None:
        self.path = Path(path)
        self.window = window

    def _prefix_digests(self, handle: Any, offset: int) -> tuple[str, str]:
        span = min(offset, self.window)
        handle.seek(0)
        head = hashlib.sha256(handle.read(span)).hexdigest()
        handle.seek(offset - span)
        tail = hashlib.sha256(handle.read(span)).hexdigest()
        return head, tail

    @staticmethod
    def _file_id(handle: Any) -> str:
        status = os.fstat(handle.fileno())
        return f"{status.st_dev}:{status.st_ino}" if status.st_ino else ""

    def pin(self) -> TranscriptCursor:
        empty = hashlib.sha256(b"").hexdigest()
        try:
            with open(self.path, "rb") as handle:
                offset = os.fstat(handle.fileno()).st_size
                head, tail = self._prefix_digests(handle, offset)
                return TranscriptCursor(str(self.path), offset, head, tail, self.window, self._file_id(handle))
        except FileNotFoundError:
            return TranscriptCursor(str(self.path), 0, empty, empty, self.window, "")

    def read_after(self, cursor: TranscriptCursor) -> TranscriptRead:
        try:
            handle = open(self.path, "rb")
        except FileNotFoundError:
            if cursor.offset == 0:
                return TranscriptRead(valid=True)
            return TranscriptRead(valid=False, reason="TRANSCRIPT_TRUNCATED")
        with handle:
            if cursor.file_id and self._file_id(handle) and self._file_id(handle) != cursor.file_id:
                return TranscriptRead(valid=False, reason="TRANSCRIPT_ROTATED")
            if os.fstat(handle.fileno()).st_size < cursor.offset:
                return TranscriptRead(valid=False, reason="TRANSCRIPT_TRUNCATED")
            if self._prefix_digests(handle, cursor.offset) != (cursor.head_sha256, cursor.tail_sha256):
                return TranscriptRead(valid=False, reason="TRANSCRIPT_PREFIX_DRIFT")
            handle.seek(cursor.offset)
            data = handle.read()
        records: list[Mapping[str, Any]] = []
        malformed = 0
        position = cursor.offset
        pieces = data.split(b"\n")
        for piece in pieces[:-1]:
            try:
                row = json.loads(piece.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                row = None
            if isinstance(row, dict):
                records.append({**row, "_offset": position})
            else:
                malformed += 1
            position += len(piece) + 1
        return TranscriptRead(valid=True, records=tuple(records), partial_tail=bool(pieces[-1]), malformed=malformed)


@dataclass(frozen=True)
class TranscriptVerdict:
    prompt_offsets: tuple[int, ...]
    ack_offsets: tuple[int, ...]
    rejected: tuple[tuple[int, str], ...]


def judge_transcript(
    envelope: Envelope,
    records: Sequence[Mapping[str, Any]],
    *,
    input_roles: Sequence[str] = ("input", "user"),
    recipient_roles: Sequence[str] = ("recipient", "assistant"),
) -> TranscriptVerdict:
    """Sort records into the prompt, exact acknowledgements, and near misses with a reason each."""
    line, wanted = envelope.pointer_line(), envelope.ack_text()
    prompts: list[int] = []
    acks: list[int] = []
    rejected: list[tuple[int, str]] = []
    for record in records:
        text, role, session = record.get("text"), record.get("role"), record.get("session")
        offset = int(record.get("_offset", -1))
        if not isinstance(text, str):
            continue
        if role in input_roles and text == line:
            if session == envelope.target_session:
                prompts.append(offset)
            else:
                rejected.append((offset, "PROMPT_WRONG_SESSION"))
            continue
        if envelope.message_id not in text and envelope.ack_token not in text:
            continue
        if role not in recipient_roles:
            rejected.append((offset, "NOT_A_RECIPIENT_RECORD"))
        elif session != envelope.target_session:
            rejected.append((offset, "ACK_WRONG_SESSION"))
        elif text != wanted:
            rejected.append((offset, "ACK_TEXT_NOT_EXACT"))
        elif not prompts:
            rejected.append((offset, "ACK_BEFORE_PROMPT"))
        else:
            acks.append(offset)
    return TranscriptVerdict(tuple(prompts), tuple(acks), tuple(rejected))


# ---------------------------------------------------------------------------
# journal


def reduce_state(events: Sequence[Mapping[str, Any]]) -> str:
    """The state a list of journal events amounts to. Order of the checks is the precedence."""
    names = [event.get("event") for event in events]
    if any(event.get("event") == "refused" and event.get("terminal") for event in events):
        return REFUSED
    if "completed" in names:
        return COMPLETED
    if "acknowledged" in names:
        return ACKNOWLEDGED
    if "cursor_invalid" in names:
        return UNCERTAIN
    if "observed" in names:
        return OBSERVED
    if "intent_submit" in names:
        return SUBMIT_ATTEMPTED
    if "uncertain" in names:
        return UNCERTAIN
    if "typed" in names:
        return TYPED
    if "intent_type" in names:
        return UNCERTAIN
    return PREPARED


class Journal:
    """Append-only record of one message. Every side effect is preceded by its intent row."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.is_file()

    def events(self) -> list[dict[str, Any]]:
        if not self.exists():
            return []
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def append(self, event: str, **detail: Any) -> dict[str, Any]:
        row = {"seq": len(self.events()) + 1, "at": time.time(), "event": event, **detail}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return row

    def state(self) -> str:
        return reduce_state(self.events())

    def has(self, event: str) -> bool:
        return any(row.get("event") == event for row in self.events())


# ---------------------------------------------------------------------------
# bounded observation and advisory latency


@dataclass(frozen=True)
class ObservationPolicy:
    """Waits in seconds. These are the caller's choices for one adapter, not universal constants."""

    poll_interval: float = 0.05
    typed_wait: float = 2.0
    ack_wait: float = 5.0
    lock_wait: float = 1.0


@dataclass
class LatencyBook:
    """What each adapter phase actually took. It suggests; it never changes a policy or a permission."""

    samples: list[dict[str, Any]] = field(default_factory=list)

    def record(self, adapter: str, phase: str, seconds: float, outcome: str) -> None:
        self.samples.append({"adapter": adapter, "phase": phase, "seconds": seconds, "outcome": outcome})

    def suggest(self, adapter: str, phase: str, *, margin: float = 2.0) -> dict[str, Any]:
        rows = [row for row in self.samples if row["adapter"] == adapter and row["phase"] == phase]
        seen = [row["seconds"] for row in rows if row["outcome"] == "seen"]
        timeouts = sum(1 for row in rows if row["outcome"] == "timeout")
        return {"adapter": adapter, "phase": phase, "samples": len(rows), "timeouts": timeouts,
                "max_seen": max(seen) if seen else None,
                "suggested_wait": max(seen) * margin if seen else None, "applied": False}


# ---------------------------------------------------------------------------
# mutual exclusion between controllers


class FileLock:
    """An exclusive lock file with a bounded wait. Held by whoever created the file.

    It excludes two live controllers from the same section. It is not atomic
    across a crash: a controller that dies inside the section leaves its file
    behind, and every later attempt is refused until a person looks at the
    recorded owner and removes it. Nothing here breaks a lock on its own.
    """

    def __init__(self, path: Path | str, *, wait: float, poll: float,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> None:
        self.path = Path(path)
        self.wait = wait
        self.poll = poll
        self.clock = clock
        self.sleep = sleep
        self.held = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        owner = json.dumps({"pid": os.getpid(), "generation": process_birth(os.getpid()), "at": time.time()})
        started = self.clock()
        while True:
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                if self.clock() - started >= self.wait:
                    return False
                self.sleep(self.poll)
                continue
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(owner)
            self.held = True
            return True

    def release(self) -> None:
        if self.held:
            self.held = False
            try:
                os.unlink(self.path)
            except FileNotFoundError:
                pass

    def owner(self) -> dict[str, Any] | None:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None


# ---------------------------------------------------------------------------
# the protocol entry


class Messenger:
    """Deliver one envelope through four adapter legs, journaling each step.

    `deliver` types and submits at most once per message. `resume` observes and
    does nothing else. Promotion to `observed` and `acknowledged` comes only
    from the acknowledgement leg; an empty input area or a returned call is
    never read as delivery.
    """

    def __init__(
        self,
        *,
        discovery: DiscoveryAdapter,
        capture: CaptureAdapter,
        input: InputAdapter,
        acknowledgement: AcknowledgementAdapter,
        journal_dir: Path | str,
        policy: ObservationPolicy | None = None,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        wall_clock: Callable[[], float] = time.time,
        latency: LatencyBook | None = None,
        adapter_name: str = "adapter",
        lock_dir: Path | str | None = None,
    ) -> None:
        self.discovery = discovery
        self.capture = capture
        self.input = input
        self.acknowledgement = acknowledgement
        self.journal_dir = Path(journal_dir)
        # Controllers that may address the same target must share this directory.
        self.lock_dir = Path(lock_dir) if lock_dir is not None else self.journal_dir / "locks"
        self.policy = policy or ObservationPolicy()
        self.clock = clock
        self.sleep = sleep
        self.wall_clock = wall_clock
        self.latency = latency if latency is not None else LatencyBook()
        self.adapter_name = adapter_name

    # -- helpers -----------------------------------------------------------

    def journal(self, envelope: Envelope) -> Journal:
        return Journal(self.journal_dir / f"{envelope.message_id}.journal.jsonl")

    def _result(self, envelope: Envelope, status: str, code: str | None = None, **extra: Any) -> dict[str, Any]:
        return {"protocol": PROTOCOL_VERSION, "message_id": envelope.message_id, "status": status,
                "state": self.journal(envelope).state(), "code": code, **extra}

    def _wait(self, predicate: Callable[[], bool], limit: float) -> tuple[bool, float]:
        started = self.clock()
        while True:
            if predicate():
                return True, self.clock() - started
            if self.clock() - started >= limit:
                return False, self.clock() - started
            self.sleep(self.policy.poll_interval)

    def _cursor(self, journal: Journal) -> TranscriptCursor:
        first = journal.events()[0]
        return TranscriptCursor(**first["cursor"])

    def _check_bound(self, envelope: Envelope, journal: Journal) -> None:
        events = journal.events()
        if not events or events[0].get("event") != "prepared":
            raise Refusal("JOURNAL_NOT_PREPARED")
        if events[0].get("fingerprint") != envelope.fingerprint():
            raise Refusal("ENVELOPE_MISMATCH", "the journal belongs to a different envelope")

    def _preflight(self, envelope: Envelope) -> TargetObservation | str:
        """The observation that allows typing, or the code that forbids it."""
        if self.wall_clock() >= envelope.expires_at:
            return "ENVELOPE_EXPIRED"
        if not typeable(envelope.pointer_line()):
            return "TEXT_NOT_TYPEABLE"
        try:
            envelope.payload.read_verified()
        except Refusal as refusal:
            return refusal.code
        seen = self.discovery.observe_target(envelope.target)
        if not seen.alive or seen.identity is None:
            return "TARGET_NOT_ALIVE"
        if seen.identity != envelope.target:
            return "TARGET_GENERATION_CHANGED"
        if seen.backend == BACKEND_UNKNOWN or backend_status(seen.backend) == "unsupported":
            return "BACKEND_UNKNOWN"
        if seen.backend != envelope.target.backend or seen.backend not in self.input.supported_backends:
            return "BACKEND_UNSUPPORTED"
        screen = self.capture.capture(envelope.target)
        if not screen.known:
            return "SCREEN_UNKNOWN"
        if screen.modal:
            return "MODAL_PRESENT"
        if composer_evidence(screen) != "buffer":
            return "COMPOSER_UNVERIFIABLE"
        if not composer_is_empty(screen):
            return "COMPOSER_NOT_EMPTY"
        return seen

    # -- locks -------------------------------------------------------------

    def _lock(self, name: str) -> FileLock:
        return FileLock(self.lock_dir / f"{name}.lock", wait=self.policy.lock_wait,
                        poll=self.policy.poll_interval, clock=self.clock, sleep=self.sleep)

    def message_lock(self, envelope: Envelope) -> FileLock:
        return self._lock("message-" + envelope.message_id)

    def target_lock(self, envelope: Envelope) -> FileLock:
        """Keyed by the process or pane itself, so two session labels for one target still collide."""
        target = envelope.target
        key = json.dumps([target.host, target.pid, target.generation, target.server, target.pane])
        return self._lock("target-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:32])

    def _busy(self, envelope: Envelope, code: str, lock: FileLock) -> dict[str, Any]:
        return {"protocol": PROTOCOL_VERSION, "message_id": envelope.message_id, "status": "refused",
                "state": self.journal(envelope).state(), "code": code, "lock_owner": lock.owner()}

    # -- verbs -------------------------------------------------------------

    def _prepare_locked(self, envelope: Envelope, journal: Journal) -> None:
        if journal.exists():
            self._check_bound(envelope, journal)
            return
        cursor = self.acknowledgement.pin()
        journal.append("prepared", fingerprint=envelope.fingerprint(), cursor=asdict(cursor),
                       target_session=envelope.target_session, payload_sha256=envelope.payload.sha256)

    def prepare(self, envelope: Envelope) -> dict[str, Any]:
        """Pin the transcript position and open the journal. No side effect on the target."""
        envelope.target.validate()
        lock = self.message_lock(envelope)
        if not lock.acquire():
            return self._busy(envelope, "MESSAGE_LOCK_BUSY", lock)
        try:
            journal = self.journal(envelope)
            self._prepare_locked(envelope, journal)
            return self._result(envelope, "prepared" if journal.state() == PREPARED else "resumable")
        finally:
            lock.release()

    def deliver(self, envelope: Envelope) -> dict[str, Any]:
        """Type and submit once, then observe.

        The message lock is held for the whole call, so every journal row of a
        message is written by one controller at a time. The target lock is held
        from the checks before typing until the submit key has been sent, so two
        controllers cannot both pass the checks and type into one target.
        """
        envelope.target.validate()
        message = self.message_lock(envelope)
        if not message.acquire():
            return self._busy(envelope, "MESSAGE_LOCK_BUSY", message)
        try:
            journal = self.journal(envelope)
            self._prepare_locked(envelope, journal)
            if journal.state() != PREPARED:
                return self._resume_locked(envelope, journal)
            target = self.target_lock(envelope)
            if not target.acquire():
                journal.append("refused", code="TARGET_LOCK_BUSY", terminal=False, typed=False)
                return self._result(envelope, "refused", "TARGET_LOCK_BUSY", lock_owner=target.owner())
            try:
                stopped = self._type_and_submit(envelope, journal)
            finally:
                target.release()
            return stopped if stopped is not None else self._observe(envelope, journal)
        finally:
            message.release()

    def _type_and_submit(self, envelope: Envelope, journal: Journal) -> dict[str, Any] | None:
        """The only place that writes to the target. Returns a result when it stopped early."""
        before = self._preflight(envelope)
        if isinstance(before, str):
            terminal = before in ("ENVELOPE_EXPIRED", "PAYLOAD_DIGEST_MISMATCH", "PAYLOAD_NOT_UTF8")
            journal.append("refused", code=before, terminal=terminal, typed=False)
            return self._result(envelope, "refused", before)

        line = envelope.pointer_line()
        journal.append("intent_type", characters=len(line),
                       text_sha256=hashlib.sha256(line.encode("utf-8")).hexdigest())
        try:
            self.input.type_text(envelope.target, line)
        except Exception as error:  # noqa: BLE001 - how much reached the target is unknown
            journal.append("uncertain", code="TYPE_CALL_FAILED", detail=type(error).__name__)
            return self._result(envelope, "uncertain", "TYPE_CALL_FAILED")
        shown, waited = self._wait(
            lambda: screen_shows_exactly(self.capture.capture(envelope.target), line), self.policy.typed_wait)
        self.latency.record(self.adapter_name, "typed", waited, "seen" if shown else "timeout")
        if not shown:
            journal.append("uncertain", code="TYPED_TEXT_NOT_OBSERVED", waited=waited)
            return self._result(envelope, "uncertain", "TYPED_TEXT_NOT_OBSERVED",
                                suggestion=self.latency.suggest(self.adapter_name, "typed"))
        journal.append("typed", waited=waited)

        after = self.discovery.observe_target(envelope.target)
        code = None
        if not after.alive or after.identity != envelope.target:
            code = "TARGET_GENERATION_CHANGED"
        elif after.backend != before.backend:
            code = "BACKEND_CHANGED"
        elif after.readers != before.readers:
            code = "READER_SET_CHANGED"
        elif not screen_shows_exactly(self.capture.capture(envelope.target), line):
            code = "COMPOSER_CHANGED_BEFORE_SUBMIT"
        if code:
            journal.append("uncertain", code=code, submitted=False)
            return self._result(envelope, "uncertain", code)

        journal.append("intent_submit")
        try:
            self.input.submit(envelope.target)
        except Exception as error:  # noqa: BLE001 - the key may or may not have landed
            journal.append("uncertain", code="SUBMIT_CALL_FAILED", detail=type(error).__name__)
        return None

    def _resume_locked(self, envelope: Envelope, journal: Journal) -> dict[str, Any]:
        state = journal.state()
        if state == PREPARED:
            return self._result(envelope, "prepared")
        if state in (REFUSED, COMPLETED, ACKNOWLEDGED):
            return self._result(envelope, state)
        return self._observe(envelope, journal)

    def resume(self, envelope: Envelope) -> dict[str, Any]:
        """Observe an existing message. Never types, never submits."""
        journal = self.journal(envelope)
        if not journal.exists():
            raise Refusal("JOURNAL_ABSENT")
        self._check_bound(envelope, journal)
        lock = self.message_lock(envelope)
        if not lock.acquire():
            return self._busy(envelope, "MESSAGE_LOCK_BUSY", lock)
        try:
            return self._resume_locked(envelope, journal)
        finally:
            lock.release()

    def release(self, envelope: Envelope) -> dict[str, Any]:
        journal = self.journal(envelope)
        if not journal.exists():
            raise Refusal("JOURNAL_ABSENT")
        self._check_bound(envelope, journal)
        lock = self.message_lock(envelope)
        if not lock.acquire():
            return self._busy(envelope, "MESSAGE_LOCK_BUSY", lock)
        try:
            state = journal.state()
            if state == COMPLETED:
                return self._result(envelope, COMPLETED)
            if state != ACKNOWLEDGED:
                raise Refusal("RELEASE_BEFORE_ACK", state)
            journal.append("completed")
            return self._result(envelope, COMPLETED)
        finally:
            lock.release()

    # -- observation -------------------------------------------------------

    def _observe(self, envelope: Envelope, journal: Journal) -> dict[str, Any]:
        if journal.has("cursor_invalid"):
            return self._result(envelope, "uncertain", "CURSOR_INVALID")
        cursor = self._cursor(journal)
        outcome: dict[str, Any] = {}

        def look() -> bool:
            read = self.acknowledgement.read_after(cursor)
            if not read.valid:
                journal.append("cursor_invalid", code=read.reason)
                outcome.update(status="uncertain", code=read.reason)
                return True
            verdict = judge_transcript(envelope, read.records)
            outcome["rejected"] = [list(item) for item in verdict.rejected]
            if len(verdict.prompt_offsets) > 1 or len(verdict.ack_offsets) > 1:
                code = "DUPLICATE_ACK" if len(verdict.ack_offsets) > 1 else "DUPLICATE_PROMPT"
                journal.append("refused", code=code, terminal=True)
                outcome.update(status="refused", code=code)
                return True
            if verdict.prompt_offsets and not journal.has("observed"):
                journal.append("observed", prompt_offset=verdict.prompt_offsets[0])
            if verdict.ack_offsets:
                journal.append("acknowledged", ack_offset=verdict.ack_offsets[0])
                outcome.update(status=ACKNOWLEDGED, code=None)
                return True
            return False

        done, waited = self._wait(look, self.policy.ack_wait)
        self.latency.record(self.adapter_name, "ack", waited,
                            "seen" if outcome.get("status") == ACKNOWLEDGED else "timeout")
        if not done:
            outcome.update(status="awaiting_ack", code="ACK_NOT_OBSERVED")
        return self._result(envelope, outcome.pop("status"), outcome.pop("code", None),
                            suggestion=self.latency.suggest(self.adapter_name, "ack"), **outcome)


# ---------------------------------------------------------------------------
# argv builders for a multiplexer route (descriptive; no live tmux run is claimed)


def _tmux(socket: str | None) -> list[str]:
    return ["tmux", "-S", socket] if socket else ["tmux"]


def tmux_type_argv(pane: str, text: str, *, socket: str | None = None) -> list[str]:
    """One argv element carries the whole text, literally. No shell sees it."""
    return [*_tmux(socket), "send-keys", "-t", pane, "-l", "--", text]


def tmux_submit_argv(pane: str, *, socket: str | None = None) -> list[str]:
    return [*_tmux(socket), "send-keys", "-t", pane, "Enter"]


def tmux_capture_argv(pane: str, *, socket: str | None = None) -> list[str]:
    return [*_tmux(socket), "capture-pane", "-p", "-t", pane]


# ---------------------------------------------------------------------------
# a live local route: a child this process started, with pipes


def start_owned_pipe_child(argv: Sequence[str], *, cwd: Path | str) -> subprocess.Popen:
    """Start a child from an argv list with a stdin pipe. No shell, no console window."""
    return subprocess.Popen(
        list(argv), cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


class OwnedPipeAdapter:
    """All four legs for a child that publishes its input area and transcript as files.

    The child contract is small: it reads UTF-8 from stdin, keeps
    `screen.json` current, and appends JSON lines to `transcript.jsonl`. The
    transcript is the child's own record, which is what makes its
    acknowledgement evidence.
    """

    supported_backends = frozenset({BACKEND_OWNED_PIPE})

    def __init__(self, process: subprocess.Popen, *, session_id: str, workdir: Path | str) -> None:
        self.process = process
        self.session_id = session_id
        self.workdir = Path(workdir)
        self.transcript = FileTranscript(self.workdir / "transcript.jsonl")
        self.generation = process_birth(process.pid)

    def identity(self) -> TargetIdentity:
        if not self.generation:
            raise Refusal("PROCESS_IDENTITY_UNAVAILABLE")
        return TargetIdentity(session_id=self.session_id, backend=BACKEND_OWNED_PIPE, host=current_host(),
                              pid=self.process.pid, generation=self.generation)

    def observe_target(self, target: TargetIdentity) -> TargetObservation:
        if self.process.poll() is not None:
            return TargetObservation(False, None, BACKEND_OWNED_PIPE)
        generation = process_birth(self.process.pid)
        if not generation:
            return TargetObservation(False, None, BACKEND_OWNED_PIPE)
        seen = TargetIdentity(session_id=self.session_id, backend=BACKEND_OWNED_PIPE, host=current_host(),
                              pid=self.process.pid, generation=generation)
        return TargetObservation(True, seen, BACKEND_OWNED_PIPE, frozenset({f"pid:{os.getpid()}"}))

    def capture(self, target: TargetIdentity) -> ScreenObservation:
        try:
            data = json.loads((self.workdir / "screen.json").read_text(encoding="utf-8"))
            buffer = data.get("composer")
            cursor = data.get("cursor_cells")
            return ScreenObservation(True, tuple(data["composer_rows"]), int(data["width"]),
                                     str(data["prompt"]), bool(data["modal"]),
                                     buffer if isinstance(buffer, str) else None,
                                     cursor if isinstance(cursor, int) else None)
        except (OSError, ValueError, KeyError, TypeError):
            return ScreenObservation(False)

    def type_text(self, target: TargetIdentity, text: str) -> None:
        self.process.stdin.write(text.encode("utf-8"))
        self.process.stdin.flush()

    def submit(self, target: TargetIdentity) -> None:
        self.process.stdin.write(b"\n")
        self.process.stdin.flush()

    def pin(self) -> TranscriptCursor:
        return self.transcript.pin()

    def read_after(self, cursor: TranscriptCursor) -> TranscriptRead:
        return self.transcript.read_after(cursor)

    def wait_ready(self, limit: float, *, poll: float = 0.02) -> bool:
        deadline = time.monotonic() + limit
        while time.monotonic() < deadline:
            if self.capture(self.identity()).known:
                return True
            time.sleep(poll)
        return False
