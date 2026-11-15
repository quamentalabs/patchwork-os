---
name: pwos-terminal-messaging
alias: terminal-messaging
description: "Use when one live terminal session must hand another a message and learn from the recipient's own transcript whether it was consumed: choosing a route by observed terminal backend, typing a pointer line, separating typed from submitted from acknowledged, or resuming after an uncertain submit without sending twice."
category: cross-terminal-messaging
tier: tier-1-execution-gate
paradigms:
  - workflow
  - prompt-flow
license: Apache-2.0
---

# Terminal Messaging Skeleton Procedure

## Overview

Generalizes cross-session messaging for terminals into `terminal_messaging.py`: one protocol entry (`Messenger`) with four separate adapter legs for discovery and binding, capture, input and acknowledgement. The sender types one short pointer line, and the message counts as delivered only when the recipient's own transcript records the exact acknowledgement after a pinned position. The reference text is `docs/terminal-messaging.md` in the repository.

Only the `owned-pipe` backend ships with a live adapter. Routes for a multiplexer, a managed pseudo terminal, a Windows console and an editor bridge are interfaces marked `not_run` until someone measures them.

## Invariants

1. Backend by Observation: a runtime or editor name is a label. Route only by the terminal backend actually observed; `unknown` is unsupported.
2. Four Separate Facts: `typed`, `submit_attempted`, `observed` and `acknowledged` are distinct states. An emptied input area or exit code 0 is none of them.
3. Intent Before Effect: the journal row for typing or submitting is written before the side effect.
4. One Submit: a message is typed and submitted at most once. Reentry observes and never sends a second key.
5. Recipient Transcript Only: promotion comes from the recipient's own record, after the pinned position, with matching session, message id, payload digest and exact text.
6. Integrity Is Not Authority: the payload digest detects change. The caller owns the authority to send.
7. Rows Are Not Proof: padded rows cannot show a draft of spaces, and neither can a cursor that was moved back. Emptiness and exactness need the input buffer itself, with the rows as a cross-check; an observation without the buffer is refused.
8. One Controller at a Time: a message lock covers every journal write and a target lock covers the checks through the submit key. A lock left by a crash is cleared by a person, never automatically.

## Skeleton Procedure (Ordered Stages)

### Stage 1: Identify the Backend and the Target

Find what owns the terminal's input: your own pipe, your own pseudo terminal, a multiplexer pane, or an editor. Record the target as a pid with its OS creation time, or as a server with a pane id, together with the host. A Windows program started from WSL has a Windows identity. If the owner is an editor and no bridge exposes capture, input and a transcript, stop: the route is unsupported.

### Stage 2: Build the Envelope

Call `create_envelope` with distinct source and target sessions, the body, a payload directory and a time to live. The payload file is written once; the acknowledgement token lives inside it and not in the typed line.

### Stage 3: Prepare and Check

`Messenger.prepare` pins the recipient's transcript position and opens the journal. `deliver` takes the message lock and the target lock, then requires a live target in the same generation, a supported backend, a known screen, no dialog, the input buffer, and an input area proven to be exactly the prompt. A refusal here, including a busy lock, has touched nothing and may be retried later.

### Stage 4: Type, Recheck, Submit Once

The pointer line is typed and then looked for as an exact whole across wrapped rows, within a bounded wait. Before the submit key the target, backend, reader set and input area are observed again. Any change ends in `uncertain` with no key sent.

### Stage 5: Observe the Recipient's Transcript

Read only after the pinned position. One prompt record followed by one exact acknowledgement promotes the message. Near misses are reported with a reason. A truncated, changed or replaced transcript invalidates the cursor.

### Stage 6: Release or Resume

Call `release` only from `acknowledged`. For anything else call `resume`, which observes and does nothing more. A message that stays in `submit_attempted` is settled by the recipient's transcript or by a person, never by a second submit.

## Artifacts and Verification Gates

- Payload file named by path, SHA-256 and size; journal file per message with ordered events.
- `tests/test_terminal_messaging.py`: tests named `test_simulated_*` cover the state machine against an in-process stand-in; tests named `test_live_*` start a real child process.
- `examples/terminal_messaging_local.py` prints a JSON result with the journal events and the exact acknowledgement.
- A new backend adapter is accepted for one backend, host and version only, after the adversarial tests pass against it.

## Hard Boundaries

- Never route by window focus or a global keyboard path.
- Never treat a typed line, a cleared input area or a returned call as delivery.
- Never send a second submit key for the same message.
- Never type into an input area that holds text the sender did not put there.
- Never pass message text through a shell; input adapters take it as data.
- Never claim an editor terminal or a vendor runtime works from the local tests alone.
