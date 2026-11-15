# SPDX-License-Identifier: Apache-2.0
"""State behaviour of the terminal messaging protocol.

Two kinds of test live here and they prove different things. Tests named
`test_simulated_*` drive `SimTerminal`, an in-process stand-in: they establish
what the state machine does, not that any real terminal behaves this way. The
stand-in wraps rows with the package's own function, so it cannot expose a
disagreement about wrapping. Tests named `test_live_*` start a real child
process whose rendering is written independently; they establish the
`owned-pipe` route on the machine that runs them and nothing about an IDE.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from patchwork_os.runtime_backend import process_birth
from patchwork_os.terminal_messaging import (
    ACKNOWLEDGED,
    BACKEND_IDE_BRIDGE,
    BACKEND_MANAGED_PTY,
    BACKEND_OWNED_PIPE,
    BACKEND_TMUX,
    BACKEND_UNKNOWN,
    BACKEND_WINDOWS_CONSOLE,
    COMPLETED,
    OBSERVED,
    PREPARED,
    REFUSED,
    SUBMIT_ATTEMPTED,
    UNCERTAIN,
    AcknowledgementAdapter,
    CaptureAdapter,
    DiscoveryAdapter,
    FileLock,
    FileTranscript,
    InputAdapter,
    LatencyBook,
    Messenger,
    ObservationPolicy,
    OwnedPipeAdapter,
    Refusal,
    ScreenObservation,
    TargetIdentity,
    TargetObservation,
    backend_status,
    composer_evidence,
    composer_is_empty,
    create_envelope,
    display_cells,
    remove_payload,
    screen_shows_exactly,
    start_owned_pipe_child,
    tmux_capture_argv,
    tmux_submit_argv,
    tmux_type_argv,
    wrap_cells,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONSUMER = REPO_ROOT / "examples" / "terminal_messaging_consumer.py"


class FakeClock:
    def __init__(self) -> None:
        self.t = 1000.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


class SimTerminal:
    """A simulated recipient. Nothing here is a real terminal or a real process."""

    supported_backends = frozenset({BACKEND_MANAGED_PTY})

    def __init__(self, directory: Path, *, session: str = "target-session", width: int = 40) -> None:
        self.session = session
        self.width = width
        self.prompt = "> "
        self.composer = ""
        self.pending = ""
        self.captures_before_render = 0
        self.modal = False
        self.known = True
        self.evidence = "buffer"
        self.cursor_override: int | None = None
        self.alive = True
        self.declared_backend = BACKEND_MANAGED_PTY
        self.observed_backend = BACKEND_MANAGED_PTY
        self.pid = 4242
        self.generation = "generation-1"
        self.readers = frozenset({"sender"})
        self.path = directory / "target-transcript.jsonl"
        self.path.write_bytes(b"")
        self.transcript = FileTranscript(self.path)
        self.type_calls: list[str] = []
        self.submit_calls = 0
        self.capture_count = 0
        self.consume_on_submit = True
        self.ack_mode = "exact"
        self.type_error: Exception | None = None
        self.before_type = None
        self.after_type = None
        self.before_submit = None
        self.on_capture = None
        self.envelope = None

    def identity(self) -> TargetIdentity:
        return TargetIdentity(session_id=self.session, backend=self.declared_backend, host="linux",
                              pid=self.pid, generation=self.generation)

    def observe_target(self, target: TargetIdentity) -> TargetObservation:
        if not self.alive:
            return TargetObservation(False, None, self.observed_backend)
        return TargetObservation(True, self.identity(), self.observed_backend, self.readers)

    def capture(self, target: TargetIdentity) -> ScreenObservation:
        self.capture_count += 1
        if self.on_capture:
            self.on_capture(self.capture_count)
        if self.pending:
            if self.captures_before_render > 0:
                self.captures_before_render -= 1
            else:
                self.composer += self.pending
                self.pending = ""
        if not self.known:
            return ScreenObservation(False)
        rows = tuple(wrap_cells(self.prompt + self.composer, self.width))
        buffer = self.composer if self.evidence == "buffer" else None
        cursor = (len(rows) - 1) * self.width + display_cells(rows[-1]) if self.evidence == "cursor" else None
        if cursor is not None and self.cursor_override is not None:
            cursor = self.cursor_override
        return ScreenObservation(True, rows, self.width, self.prompt, self.modal, buffer, cursor)

    def type_text(self, target: TargetIdentity, text: str) -> None:
        if self.before_type:
            self.before_type()
        self.type_calls.append(text)
        if self.type_error:
            self.composer += text[: len(text) // 2]
            raise self.type_error
        self.pending += text
        if self.after_type:
            self.after_type()

    def submit(self, target: TargetIdentity) -> None:
        if self.before_submit:
            self.before_submit()
        self.submit_calls += 1
        if self.consume_on_submit:
            self.consume()

    def consume(self) -> None:
        """The recipient takes the line. Also used to stand for a person pressing Enter later."""
        line, self.composer = self.composer, ""
        self.write("input", line)
        wanted = self.envelope.ack_text()
        if self.ack_mode == "exact":
            self.write("recipient", wanted)
        elif self.ack_mode == "duplicate":
            self.write("recipient", wanted)
            self.write("recipient", wanted)
        elif self.ack_mode == "wrong_session":
            self.write("recipient", wanted, session="another-session")
        elif self.ack_mode == "wrong_digest":
            self.write("recipient", wanted[:-1] + ("0" if wanted[-1] != "0" else "1"))

    def write(self, role: str, text: str, session: str | None = None) -> None:
        with open(self.path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"role": role, "session": session or self.session, "text": text},
                                    ensure_ascii=False) + "\n")

    def pin(self):
        return self.transcript.pin()

    def read_after(self, cursor):
        return self.transcript.read_after(cursor)


def controller(tmp_path: Path, sim: SimTerminal, clock: FakeClock) -> Messenger:
    """One controller. Two of them built on one directory share journals and locks."""
    return Messenger(discovery=sim, capture=sim, input=sim, acknowledgement=sim,
                     journal_dir=tmp_path / "journal", policy=ObservationPolicy(0.05, 1.0, 1.0),
                     clock=clock.now, sleep=clock.sleep, wall_clock=clock.now, latency=LatencyBook(),
                     adapter_name="sim")


def once(action):
    """A hook that runs its action the first time only, so an interleaved call cannot recurse."""
    ran = []

    def hook() -> None:
        if not ran:
            ran.append(True)
            action()
    return hook


def build(tmp_path: Path, *, payload_dir: str = "payloads", body: str = "do the thing", **terminal):
    clock = FakeClock()
    sim = SimTerminal(tmp_path, **terminal)
    messenger = controller(tmp_path, sim, clock)
    envelope = create_envelope(source_session="sender-session", target=sim.identity(), body=body,
                               payload_dir=tmp_path / payload_dir, ttl_seconds=600.0, now=clock.now)
    sim.envelope = envelope
    return sim, clock, messenger, envelope


def events(messenger: Messenger, envelope) -> list[str]:
    return [row["event"] for row in messenger.journal(envelope).events()]


# ---------------------------------------------------------------------------
# the route itself


def test_simulated_delivery_promotes_only_through_the_target_transcript(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    for leg in (DiscoveryAdapter, CaptureAdapter, InputAdapter, AcknowledgementAdapter):
        assert isinstance(sim, leg)

    result = messenger.deliver(envelope)

    assert result["status"] == ACKNOWLEDGED and result["state"] == ACKNOWLEDGED
    assert sim.type_calls == [envelope.pointer_line()]
    assert sim.submit_calls == 1
    assert envelope.ack_token not in envelope.pointer_line()
    assert events(messenger, envelope) == [
        "prepared", "intent_type", "typed", "intent_submit", "observed", "acknowledged"]
    assert messenger.release(envelope)["state"] == COMPLETED
    assert messenger.release(envelope)["state"] == COMPLETED
    assert messenger.resume(envelope)["status"] == COMPLETED
    assert messenger.deliver(envelope)["status"] == COMPLETED
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)
    assert remove_payload(envelope.payload) and not Path(envelope.payload.path).exists()
    assert remove_payload(envelope.payload)


def test_simulated_intent_is_journaled_before_each_side_effect(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    seen: dict[str, str] = {}
    sim.before_type = lambda: seen.__setitem__("type", events(messenger, envelope)[-1])
    sim.before_submit = lambda: seen.__setitem__("submit", events(messenger, envelope)[-1])

    messenger.deliver(envelope)

    assert seen == {"type": "intent_type", "submit": "intent_submit"}


@pytest.mark.parametrize(
    ("arrange", "code"),
    [
        (lambda sim: setattr(sim, "composer", "someone else's draft"), "COMPOSER_NOT_EMPTY"),
        (lambda sim: setattr(sim, "composer", "x"), "COMPOSER_NOT_EMPTY"),
        (lambda sim: setattr(sim, "modal", True), "MODAL_PRESENT"),
        (lambda sim: setattr(sim, "known", False), "SCREEN_UNKNOWN"),
        (lambda sim: setattr(sim, "alive", False), "TARGET_NOT_ALIVE"),
        (lambda sim: setattr(sim, "generation", "generation-2"), "TARGET_GENERATION_CHANGED"),
        (lambda sim: setattr(sim, "observed_backend", BACKEND_UNKNOWN), "BACKEND_UNKNOWN"),
        (lambda sim: setattr(sim, "observed_backend", "kiro"), "BACKEND_UNKNOWN"),
        (lambda sim: setattr(sim, "observed_backend", BACKEND_TMUX), "BACKEND_UNSUPPORTED"),
    ],
)
def test_simulated_refusal_before_typing_touches_nothing(tmp_path: Path, arrange, code: str) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    arrange(sim)

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"]) == ("refused", code)
    assert sim.type_calls == [] and sim.submit_calls == 0
    assert result["state"] == PREPARED
    assert "intent_type" not in events(messenger, envelope)


def test_simulated_same_pid_in_a_new_generation_is_a_different_target(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    assert envelope.target.pid == sim.pid
    sim.generation = "generation-after-pid-reuse"

    assert messenger.deliver(envelope)["code"] == "TARGET_GENERATION_CHANGED"
    assert sim.type_calls == []


def test_simulated_refusal_for_a_busy_composer_is_not_final(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.composer = "draft"
    assert messenger.deliver(envelope)["code"] == "COMPOSER_NOT_EMPTY"
    assert sim.composer == "draft"

    sim.composer = ""
    assert messenger.deliver(envelope)["status"] == ACKNOWLEDGED
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)


# ---------------------------------------------------------------------------
# typed, submitted, observed and acknowledged are four different things


def test_simulated_enter_not_consumed_is_not_delivery_and_resume_never_resends(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.consume_on_submit = False

    first = messenger.deliver(envelope)

    assert (first["status"], first["code"], first["state"]) == ("awaiting_ack", "ACK_NOT_OBSERVED", SUBMIT_ATTEMPTED)
    assert sim.composer == envelope.pointer_line()
    assert messenger.resume(envelope)["status"] == "awaiting_ack"
    assert messenger.deliver(envelope)["status"] == "awaiting_ack"
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)
    with pytest.raises(Refusal) as refused:
        messenger.release(envelope)
    assert refused.value.code == "RELEASE_BEFORE_ACK"

    sim.consume()
    late = messenger.resume(envelope)
    assert (late["status"], late["state"]) == (ACKNOWLEDGED, ACKNOWLEDGED)
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)


def test_simulated_cleared_composer_without_a_transcript_record_proves_nothing(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.consume_on_submit = False
    sim.before_submit = lambda: setattr(sim, "composer", "")

    result = messenger.deliver(envelope)

    assert sim.composer == ""
    assert (result["status"], result["state"]) == ("awaiting_ack", SUBMIT_ATTEMPTED)


def test_simulated_failed_type_call_is_uncertain_and_reentry_only_observes(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.type_error = OSError("pipe closed halfway")

    first = messenger.deliver(envelope)

    assert (first["status"], first["code"], first["state"]) == ("uncertain", "TYPE_CALL_FAILED", UNCERTAIN)
    assert sim.submit_calls == 0
    sim.type_error = None
    assert messenger.deliver(envelope)["status"] == "awaiting_ack"
    assert messenger.resume(envelope)["status"] == "awaiting_ack"
    assert (len(sim.type_calls), sim.submit_calls) == (1, 0)
    assert "typed" not in events(messenger, envelope)


def test_simulated_text_that_never_renders_stops_before_submit_and_only_suggests(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.captures_before_render = 10 ** 9
    policy_before = messenger.policy

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"]) == ("uncertain", "TYPED_TEXT_NOT_OBSERVED")
    assert sim.submit_calls == 0 and "intent_submit" not in events(messenger, envelope)
    assert result["suggestion"]["timeouts"] == 1
    assert result["suggestion"]["suggested_wait"] is None and result["suggestion"]["applied"] is False
    assert messenger.policy is policy_before


def test_simulated_delayed_rendering_is_waited_for_within_the_bound(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.captures_before_render = 3

    result = messenger.deliver(envelope)

    assert result["status"] == ACKNOWLEDGED
    typed = [row for row in messenger.latency.samples if row["phase"] == "typed"]
    assert typed == [{"adapter": "sim", "phase": "typed", "seconds": pytest.approx(0.15), "outcome": "seen"}]
    suggestion = messenger.latency.suggest("sim", "typed")
    assert suggestion["suggested_wait"] == pytest.approx(0.30) and suggestion["applied"] is False


# ---------------------------------------------------------------------------
# what changes between typing and submitting


def test_simulated_reader_set_change_after_typing_blocks_submit(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.after_type = lambda: setattr(sim, "readers", frozenset({"sender", "second-reader"}))

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"], result["state"]) == ("uncertain", "READER_SET_CHANGED", UNCERTAIN)
    assert sim.submit_calls == 0
    assert events(messenger, envelope)[-2:] == ["typed", "uncertain"]


def test_simulated_generation_change_after_typing_blocks_submit(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.after_type = lambda: setattr(sim, "generation", "generation-2")

    result = messenger.deliver(envelope)

    assert result["code"] == "TARGET_GENERATION_CHANGED" and sim.submit_calls == 0


def test_simulated_foreign_text_joining_the_line_blocks_submit(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    # capture 1 is the preflight, 2 sights the typed line, 3 is the recheck before submit
    sim.on_capture = lambda count: setattr(sim, "composer", sim.composer + " and more") if count == 3 else None

    result = messenger.deliver(envelope)

    assert result["code"] == "COMPOSER_CHANGED_BEFORE_SUBMIT" and sim.submit_calls == 0


# ---------------------------------------------------------------------------
# acknowledgements that must not promote


@pytest.mark.parametrize(("mode", "reason"), [
    ("wrong_session", "ACK_WRONG_SESSION"), ("wrong_digest", "ACK_TEXT_NOT_EXACT")])
def test_simulated_near_miss_acknowledgement_is_reported_and_not_promoted(tmp_path: Path, mode, reason) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.ack_mode = mode

    result = messenger.deliver(envelope)

    assert (result["status"], result["state"]) == ("awaiting_ack", OBSERVED)
    assert [item[1] for item in result["rejected"]] == [reason]
    with pytest.raises(Refusal):
        messenger.release(envelope)


def test_simulated_stale_acknowledgement_before_the_pinned_position_is_never_read(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.write("input", envelope.pointer_line())
    sim.write("recipient", envelope.ack_text())
    sim.ack_mode = "none"

    result = messenger.deliver(envelope)

    assert (result["status"], result["state"]) == ("awaiting_ack", OBSERVED)
    assert result["rejected"] == []


def test_simulated_acknowledgement_without_a_prompt_record_is_rejected(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.consume_on_submit = False
    messenger.deliver(envelope)
    sim.write("recipient", envelope.ack_text())

    result = messenger.resume(envelope)

    assert result["status"] == "awaiting_ack"
    assert [item[1] for item in result["rejected"]] == ["ACK_BEFORE_PROMPT"]


def test_simulated_duplicate_acknowledgement_closes_the_message(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.ack_mode = "duplicate"

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"], result["state"]) == ("refused", "DUPLICATE_ACK", REFUSED)
    assert messenger.resume(envelope)["status"] == REFUSED
    with pytest.raises(Refusal):
        messenger.release(envelope)


def pending_message_with_history(tmp_path: Path):
    sim, clock, messenger, envelope = build(tmp_path)
    sim.write("input", "an earlier, unrelated line that the cursor sits after")
    sim.consume_on_submit = False
    assert messenger.deliver(envelope)["status"] == "awaiting_ack"
    return sim, messenger, envelope


def exact_records(sim: SimTerminal, envelope) -> bytes:
    rows = [{"role": "input", "session": sim.session, "text": envelope.pointer_line()},
            {"role": "recipient", "session": sim.session, "text": envelope.ack_text()}]
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode("utf-8")


def test_simulated_truncated_transcript_invalidates_the_cursor(tmp_path: Path) -> None:
    sim, messenger, envelope = pending_message_with_history(tmp_path)
    with open(sim.path, "r+b") as handle:
        handle.truncate(5)

    result = messenger.resume(envelope)

    assert (result["status"], result["code"], result["state"]) == ("uncertain", "TRANSCRIPT_TRUNCATED", UNCERTAIN)


def test_simulated_prefix_drift_blocks_an_otherwise_exact_acknowledgement(tmp_path: Path) -> None:
    sim, messenger, envelope = pending_message_with_history(tmp_path)
    with open(sim.path, "r+b") as handle:
        handle.write(b"X" * 12)
    with open(sim.path, "ab") as handle:
        handle.write(exact_records(sim, envelope))

    result = messenger.resume(envelope)

    assert (result["status"], result["code"]) == ("uncertain", "TRANSCRIPT_PREFIX_DRIFT")
    again = messenger.resume(envelope)
    assert (again["status"], again["code"], again["state"]) == ("uncertain", "CURSOR_INVALID", UNCERTAIN)
    with pytest.raises(Refusal):
        messenger.release(envelope)


def test_simulated_rotated_transcript_with_the_same_prefix_is_still_a_different_file(tmp_path: Path) -> None:
    sim, messenger, envelope = pending_message_with_history(tmp_path)
    if not os.stat(sim.path).st_ino:
        pytest.skip("this filesystem reports no file identity, so same-prefix rotation cannot be seen")
    replacement = tmp_path / "rotated.jsonl"
    replacement.write_bytes(sim.path.read_bytes() + exact_records(sim, envelope))
    os.replace(replacement, sim.path)

    result = messenger.resume(envelope)

    assert (result["status"], result["code"]) == ("uncertain", "TRANSCRIPT_ROTATED")


# ---------------------------------------------------------------------------
# text: wrapping, Unicode, metacharacters


def test_wrapping_is_by_cells_and_wide_characters_never_straddle_a_row() -> None:
    # a Hangul syllable takes two cells, an ASCII letter one
    assert wrap_cells("> 한글가나다 abc", 8) == ["> 한글가", "나다 abc"]
    assert wrap_cells("> 한글", 5) == ["> 한", "글"]
    assert wrap_cells("éx", 2) == ["éx"]
    assert wrap_cells("", 4) == [""]
    assert wrap_cells("abcd", 4) == ["abcd"]


def test_wrapped_text_is_recognised_only_as_an_exact_whole() -> None:
    text = "한글 payload 본문"

    def screen(rows, buffer=text, cursor=None) -> ScreenObservation:
        return ScreenObservation(True, tuple(rows), 8, "> ", False, buffer, cursor)

    exact = wrap_cells("> " + text, 8)
    end = (len(exact) - 1) * 8 + display_cells(exact[-1])
    assert len(exact) > 2
    assert screen_shows_exactly(screen(exact), text)
    assert screen_shows_exactly(screen(exact, cursor=end), text)
    # a cursor at exactly the right place, with exactly the right rows, is still not the buffer
    assert not screen_shows_exactly(screen(exact, buffer=None, cursor=end), text)
    # right-edge padding is the terminal's; a cell past the edge, or a buffer that differs, is not
    assert screen_shows_exactly(screen(["> ab    "], buffer="ab"), "ab")
    assert not screen_shows_exactly(screen(["> ab     "], buffer="ab"), "ab")
    assert not screen_shows_exactly(screen(["> ab"], buffer="ab"), "a")
    # geometry and the authoritative fact must both agree
    assert not screen_shows_exactly(screen(wrap_cells("> x" + text, 8)), text)
    assert not screen_shows_exactly(screen(exact, buffer=text.replace(" ", "  ", 1)), text)
    assert not screen_shows_exactly(screen(exact, buffer=text + " "), text)
    assert not screen_shows_exactly(screen(exact, buffer=None, cursor=end + 1), text)
    assert not screen_shows_exactly(screen(wrap_cells("> " + text.replace(" ", ""), 8)), text)
    assert not screen_shows_exactly(screen(exact[:-1]), text)
    assert not screen_shows_exactly(screen(exact + ["tail"]), text)
    # rows alone prove nothing, however exact they look
    assert not screen_shows_exactly(screen(exact, buffer=None), text)
    assert not screen_shows_exactly(ScreenObservation(False), text)
    assert not screen_shows_exactly(ScreenObservation(True, tuple(exact), 8, "> ", True, text), text)


def test_rows_padded_with_blanks_never_prove_an_empty_input_area() -> None:
    padded = ScreenObservation(True, (">   ",), 80, "> ", False)
    assert composer_evidence(padded) == "none"
    assert not composer_is_empty(padded)
    assert not composer_is_empty(ScreenObservation(True, (">   ",), 80, "> ", False, "  "))
    assert not composer_is_empty(ScreenObservation(True, (">   ",), 80, "> ", False, None, 4))
    assert composer_is_empty(ScreenObservation(True, ("> ",), 80, "> ", False, ""))
    assert composer_is_empty(ScreenObservation(True, ("> ",), 80, "> ", False, "", 2))
    assert not composer_is_empty(ScreenObservation(True, ("> x",), 80, "> ", False, ""))
    # spaces typed, caret moved back to Home: rows and cursor both look empty, the buffer is not
    home = ScreenObservation(True, (">   ",), 80, "> ", False, None, 2)
    assert composer_evidence(home) == "cursor"
    assert not composer_is_empty(home)
    assert not composer_is_empty(ScreenObservation(True, ("> ",), 80, "> ", False, None, 2))
    assert not composer_is_empty(ScreenObservation(True, (">   ",), 80, "> ", False, "  ", 2))


def test_simulated_unicode_line_that_wraps_is_delivered_byte_for_byte(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path, payload_dir="페이로드 폴더", body="본문 내용", width=12)

    result = messenger.deliver(envelope)

    assert "페이로드 폴더" in envelope.pointer_line()
    assert len(wrap_cells("> " + envelope.pointer_line(), 12)) > 3
    assert result["status"] == ACKNOWLEDGED
    assert sim.type_calls == [envelope.pointer_line()]


def test_metacharacters_are_data_for_every_input_route(tmp_path: Path) -> None:
    hostile = "$(reboot); rm -rf / && echo \"x\" | tee `id` > /dev/null #"
    assert tmux_type_argv("%3", hostile, socket="/tmp/sock") == [
        "tmux", "-S", "/tmp/sock", "send-keys", "-t", "%3", "-l", "--", hostile]
    assert tmux_type_argv("%3", "-l --help")[-2:] == ["--", "-l --help"]
    assert tmux_submit_argv("%3") == ["tmux", "send-keys", "-t", "%3", "Enter"]
    assert tmux_capture_argv("%3") == ["tmux", "capture-pane", "-p", "-t", "%3"]

    sim, _, messenger, envelope = build(tmp_path, payload_dir="pay;load $(id) & `x` 'q'", width=200)
    assert messenger.deliver(envelope)["status"] == ACKNOWLEDGED
    assert sim.type_calls == [envelope.pointer_line()]
    assert "$(id)" in sim.type_calls[0]


# ---------------------------------------------------------------------------
# envelope and journal guards


def test_simulated_expired_envelope_and_changed_payload_are_final_refusals(tmp_path: Path) -> None:
    sim, clock, messenger, envelope = build(tmp_path)
    clock.t += 601.0
    assert messenger.deliver(envelope)["code"] == "ENVELOPE_EXPIRED"
    assert messenger.deliver(envelope)["state"] == REFUSED and sim.type_calls == []

    other = tmp_path / "second"
    other.mkdir()
    sim2, _, messenger2, envelope2 = build(other)
    os.chmod(envelope2.payload.path, 0o666)
    with open(envelope2.payload.path, "ab") as handle:
        handle.write(b" ")
    assert messenger2.deliver(envelope2)["code"] == "PAYLOAD_DIGEST_MISMATCH"
    assert sim2.type_calls == []


def test_a_journal_belongs_to_one_envelope_and_a_message_cannot_target_its_sender(tmp_path: Path) -> None:
    sim, clock, messenger, envelope = build(tmp_path)
    messenger.deliver(envelope)
    impostor = create_envelope(source_session="sender-session", target=sim.identity(), body="different",
                               payload_dir=tmp_path / "other-payloads", ttl_seconds=600.0, now=clock.now,
                               message_id=envelope.message_id)
    with pytest.raises(Refusal) as mismatch:
        messenger.resume(impostor)
    assert mismatch.value.code == "ENVELOPE_MISMATCH"
    with pytest.raises(Refusal) as self_target:
        create_envelope(source_session=sim.session, target=sim.identity(), body="x",
                        payload_dir=tmp_path / "third", ttl_seconds=1.0)
    assert self_target.value.code == "SELF_TARGET"
    with pytest.raises(Refusal):
        TargetIdentity(session_id="s", backend=BACKEND_TMUX, host="linux", pid=1).validate()


def test_unmeasured_backends_are_marked_not_run_and_labels_grant_nothing() -> None:
    assert backend_status(BACKEND_OWNED_PIPE) == "live-local"
    for backend in (BACKEND_TMUX, BACKEND_MANAGED_PTY, BACKEND_WINDOWS_CONSOLE, BACKEND_IDE_BRIDGE):
        assert backend_status(backend) == "not_run"
    for label in (BACKEND_UNKNOWN, "kiro", "vscode", "cc", "codex"):
        assert backend_status(label) == "unsupported"


# ---------------------------------------------------------------------------
# what rows cannot show: space-only and trailing drafts, and an input area nobody can vouch for


@pytest.mark.parametrize(("evidence", "code"), [
    ("buffer", "COMPOSER_NOT_EMPTY"), ("cursor", "COMPOSER_UNVERIFIABLE"), ("none", "COMPOSER_UNVERIFIABLE")])
def test_simulated_space_only_draft_is_refused_under_every_kind_of_evidence(tmp_path: Path, evidence, code) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.evidence = evidence
    sim.composer = "   "

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"]) == ("refused", code)
    assert sim.type_calls == [] and sim.composer == "   "


def test_simulated_empty_looking_rows_without_buffer_or_cursor_are_refused(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.evidence = "none"
    assert sim.capture(sim.identity()).composer_rows == ("> ",)

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"], result["state"]) == ("refused", "COMPOSER_UNVERIFIABLE", PREPARED)
    assert sim.type_calls == []


def test_simulated_trailing_space_added_by_someone_else_blocks_submit(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    # the drawn rows stay identical after this: only the buffer can tell
    sim.on_capture = lambda count: setattr(sim, "composer", sim.composer + " ") if count == 3 else None

    result = messenger.deliver(envelope)

    assert result["code"] == "COMPOSER_CHANGED_BEFORE_SUBMIT" and sim.submit_calls == 0
    assert sim.composer == envelope.pointer_line() + " "


def test_simulated_cursor_evidence_alone_never_carries_a_delivery(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path, width=17)
    sim.evidence = "cursor"

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"], result["state"]) == ("refused", "COMPOSER_UNVERIFIABLE", PREPARED)
    assert (len(sim.type_calls), sim.submit_calls) == (0, 0)


def test_simulated_spaces_typed_then_caret_sent_home_is_not_an_empty_input_area(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    sim.evidence = "cursor"
    sim.composer = "   "
    sim.cursor_override = 2
    seen = sim.capture(sim.identity())
    assert (seen.cursor_cells, seen.composer_text) == (2, None)

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"]) == ("refused", "COMPOSER_UNVERIFIABLE")
    assert sim.type_calls == [] and sim.composer == "   "


# ---------------------------------------------------------------------------
# two controllers


def test_file_lock_waits_within_its_bound_and_is_released_only_by_its_holder(tmp_path: Path) -> None:
    clock = FakeClock()
    holder = FileLock(tmp_path / "one.lock", wait=0.5, poll=0.25, clock=clock.now, sleep=clock.sleep)
    waiter = FileLock(tmp_path / "one.lock", wait=0.5, poll=0.25, clock=clock.now, sleep=clock.sleep)
    assert holder.acquire()
    started = clock.t

    assert not waiter.acquire()

    assert clock.t - started == 0.5
    assert waiter.owner()["pid"] == os.getpid()
    waiter.release()
    assert (tmp_path / "one.lock").is_file()
    holder.release()
    assert waiter.acquire()


def test_simulated_two_controllers_on_one_message_type_and_submit_once(tmp_path: Path) -> None:
    sim, clock, first, envelope = build(tmp_path)
    second = controller(tmp_path, sim, clock)
    seen: dict = {}
    # the second controller arrives after the first passed its checks and before it typed
    sim.before_type = once(lambda: seen.update(inner=second.deliver(envelope)))

    outer = first.deliver(envelope)

    assert outer["status"] == ACKNOWLEDGED
    assert (seen["inner"]["status"], seen["inner"]["code"]) == ("refused", "MESSAGE_LOCK_BUSY")
    assert seen["inner"]["lock_owner"]["pid"] == os.getpid()
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)
    assert second.deliver(envelope)["status"] == ACKNOWLEDGED
    assert (len(sim.type_calls), sim.submit_calls) == (1, 1)
    assert [row["seq"] for row in first.journal(envelope).events()] == list(range(1, 7))


def test_simulated_two_messages_for_one_target_do_not_interleave(tmp_path: Path) -> None:
    sim, clock, first, envelope = build(tmp_path)
    second = controller(tmp_path, sim, clock)
    other = create_envelope(source_session="second-sender", target=sim.identity(), body="another message",
                            payload_dir=tmp_path / "payloads-b", ttl_seconds=600.0, now=clock.now)
    seen: dict = {}
    sim.before_type = once(lambda: seen.update(inner=second.deliver(other)))

    assert first.deliver(envelope)["status"] == ACKNOWLEDGED

    assert (seen["inner"]["status"], seen["inner"]["code"], seen["inner"]["state"]) == (
        "refused", "TARGET_LOCK_BUSY", PREPARED)
    assert sim.type_calls == [envelope.pointer_line()]
    sim.envelope = other
    assert second.deliver(other)["status"] == ACKNOWLEDGED
    assert sim.type_calls == [envelope.pointer_line(), other.pointer_line()]


def test_simulated_lock_left_behind_refuses_and_is_never_broken_automatically(tmp_path: Path) -> None:
    sim, _, messenger, envelope = build(tmp_path)
    abandoned = messenger.target_lock(envelope)
    assert abandoned.acquire()

    result = messenger.deliver(envelope)

    assert (result["status"], result["code"]) == ("refused", "TARGET_LOCK_BUSY")
    assert messenger.deliver(envelope)["code"] == "TARGET_LOCK_BUSY"
    assert sim.type_calls == [] and abandoned.path.is_file()
    os.unlink(abandoned.path)
    assert messenger.deliver(envelope)["status"] == ACKNOWLEDGED


# ---------------------------------------------------------------------------
# a real child process


def live_child(directory: Path, session: str, declared: str):
    child = start_owned_pipe_child(
        [sys.executable, "-B", str(CONSUMER), "--session", session, "--dir", str(directory), "--width", "50"],
        cwd=directory.parent)
    adapter = OwnedPipeAdapter(child, session_id=declared, workdir=directory)
    assert adapter.wait_ready(20.0), "the child did not publish its input area"
    messenger = Messenger(discovery=adapter, capture=adapter, input=adapter, acknowledgement=adapter,
                          journal_dir=directory.parent / "journal",
                          policy=ObservationPolicy(0.02, 10.0, 10.0), adapter_name="owned-pipe")
    return child, adapter, messenger


@pytest.mark.skipif(process_birth(os.getpid()) is None, reason="no OS process identity on this platform")
def test_live_local_child_acknowledges_from_its_own_transcript(tmp_path: Path) -> None:
    workspace = tmp_path / "live $(echo) & child 한글"
    workspace.mkdir()
    child, adapter, messenger = live_child(workspace / "recipient", "recipient-session", "recipient-session")
    try:
        idle = adapter.capture(adapter.identity())
        assert composer_evidence(idle) == "buffer" and idle.composer_text == "" and idle.cursor_cells == 2
        envelope = create_envelope(source_session="sender-session", target=adapter.identity(),
                                   body="live body", payload_dir=workspace / "payloads", ttl_seconds=60.0)

        result = messenger.deliver(envelope)

        assert (result["status"], result["state"]) == (ACKNOWLEDGED, ACKNOWLEDGED)
        rows = [json.loads(line) for line in adapter.transcript.path.read_text(encoding="utf-8").splitlines()]
        assert rows == [
            {"role": "input", "session": "recipient-session", "text": envelope.pointer_line()},
            {"role": "recipient", "session": "recipient-session", "text": envelope.ack_text()}]
        assert messenger.release(envelope)["state"] == COMPLETED
    finally:
        child.stdin.close()
        assert child.wait(timeout=20) == 0

    gone = create_envelope(source_session="sender-session", target=adapter.identity(), body="too late",
                           payload_dir=workspace / "payloads", ttl_seconds=60.0)
    assert messenger.deliver(gone)["code"] == "TARGET_NOT_ALIVE"


@pytest.mark.skipif(process_birth(os.getpid()) is None, reason="no OS process identity on this platform")
def test_live_child_under_another_session_cannot_acknowledge_for_the_named_one(tmp_path: Path) -> None:
    workspace = tmp_path / "wrong-target"
    workspace.mkdir()
    child, adapter, messenger = live_child(workspace / "recipient", "actual-session", "named-session")
    messenger.policy = ObservationPolicy(0.02, 10.0, 1.0)
    try:
        envelope = create_envelope(source_session="sender-session", target=adapter.identity(), body="x",
                                   payload_dir=workspace / "payloads", ttl_seconds=60.0)

        result = messenger.deliver(envelope)

        assert (result["status"], result["state"]) == ("awaiting_ack", SUBMIT_ATTEMPTED)
        assert [item[1] for item in result["rejected"]] == ["PROMPT_WRONG_SESSION", "ACK_WRONG_SESSION"]
    finally:
        child.stdin.close()
        assert child.wait(timeout=20) == 0
