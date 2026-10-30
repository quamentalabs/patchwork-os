# External native result attachment

`pwos attach-external` and the web **Attach verified result** button invoke an
explicitly configured, trusted deploy2 collector. They do not submit a task,
reconstruct a previous submission, or independently verify a vendor transcript.
The collector is the authority for native evidence and independent review.

Add `external_collector` to the workspace `.patchwork/config.json`. Supply an
absolute `argv` array and `cwd`, with SHA-256 `source_pins` for the executable
and the collector code on which the operator relies. Configure `run_id`,
`owner_session`, `runtime`, and `model` to match the existing run; configure an
absolute `artifact_root` and relative `answer_path`. Paths and identifiers are
local operator configuration, not package defaults. The command runs without a
shell, has a 30-second deadline and a 4 MiB output limit. Source pins must be
maintained whenever collector code changes; they cannot attest unpinned imports
or the operating system.

The collector must return a `deploy2-collect` result with either current
completion or authenticated historical completion, an independently reviewed answer contract, bound requested,
resolved and observed model, native edit observation, and a verified artifact.
The answer is read from the allowlisted root and checked against the collector's
hash and byte count. Held, missing, mismatched, malformed and changed results
are refused. Local process runs retain their existing separate behavior.
Historical results expose `recorded_completion_allowed` and the archive proof;
`completion_allowed` stays false and current live acceptance stays `not_run`.
