# SPDX-License-Identifier: Apache-2.0
"""A harmless recipient for the terminal messaging example: one input area, one transcript.

It reads UTF-8 from stdin, shows what was typed in `screen.json` (drawn rows,
plus the exact input buffer and the cursor position), and on a newline
consumes the line into `transcript.jsonl`. When the line is a message
pointer for this session it opens the payload, checks the digest, and records
the exact acknowledgement found by reading that payload. It imports nothing
from the package, so its rendering is independent of the sender's.

It runs no command from its input and touches only its own working directory.
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
import time
import unicodedata
import uuid
from pathlib import Path

PROMPT = "> "


def cell_width(character: str) -> int:
    if unicodedata.category(character) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(character) in ("W", "F") else 1


def rows_for(text: str, width: int) -> list[str]:
    rows, current, used = [], [], 0
    for character in text:
        cells = cell_width(character)
        if used + cells > width:
            rows.append("".join(current))
            current, used = [], 0
        current.append(character)
        used += cells
    rows.append("".join(current))
    return rows


def replace_file(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    for attempt in range(50):
        try:
            os.replace(temporary, path)
            return
        except PermissionError:
            if attempt == 49:
                raise
            time.sleep(0.01)


def answer(line: str, session: str) -> str:
    """The recipient's reply to one consumed line. Every refusal names its reason."""
    parts = line.split(" ", 3)
    if len(parts) != 4 or parts[0] != "PWTM1" or not parts[2].startswith("sha256:"):
        return "IGNORED not a message pointer"
    message_id, digest, payload_path = parts[1], parts[2][len("sha256:"):], parts[3]
    try:
        data = Path(payload_path).read_bytes()
    except OSError:
        return f"REFUSED id={message_id} payload unreadable"
    if hashlib.sha256(data).hexdigest() != digest:
        return f"REFUSED id={message_id} payload digest mismatch"
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return f"REFUSED id={message_id} payload not a UTF-8 JSON document"
    if document.get("target_session") != session or document.get("message_id") != message_id:
        return f"REFUSED id={message_id} not addressed to this session"
    return f"ACK {document.get('ack_token')} id={message_id} sha256={digest}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--session", required=True)
    parser.add_argument("--dir", required=True)
    parser.add_argument("--width", type=int, default=80)
    parser.add_argument("--render-delay", type=float, default=0.0)
    args = parser.parse_args(argv)
    workdir = Path(args.dir)
    workdir.mkdir(parents=True, exist_ok=True)
    screen, transcript = workdir / "screen.json", workdir / "transcript.jsonl"
    composer = ""
    sequence = 0

    def render() -> None:
        nonlocal sequence
        sequence += 1
        if args.render_delay:
            time.sleep(args.render_delay)
        rows = rows_for(PROMPT + composer, args.width)
        cursor = (len(rows) - 1) * args.width + sum(cell_width(character) for character in rows[-1])
        # The rows are what is drawn. The buffer is published separately because padding makes a
        # draft of spaces look the same as an empty input area. The cursor is extra information.
        replace_file(screen, json.dumps({
            "seq": sequence, "width": args.width, "prompt": PROMPT, "modal": False,
            "composer": composer, "cursor_cells": cursor, "composer_rows": rows}, ensure_ascii=False))

    def record(role: str, text: str) -> None:
        with open(transcript, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({"role": role, "session": args.session, "text": text},
                                    ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    render()
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    if os.name == "nt":
        import msvcrt
        msvcrt.setmode(0, os.O_BINARY)
    while True:
        chunk = os.read(0, 4096)
        if not chunk:
            return 0
        for character in decoder.decode(chunk):
            if character == "\n":
                line, composer = composer, ""
                record("input", line)
                record("recipient", answer(line, args.session))
            elif character != "\r":
                composer += character
        render()


if __name__ == "__main__":
    raise SystemExit(main())
