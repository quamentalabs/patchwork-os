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

Every pinned path and `cwd` must be a plain file or directory: a symbolic link
or junction anywhere in the path is refused with `EXTERNAL_LINK_REFUSED`. A
virtual environment's `bin/python` is normally a link, so configure the
canonical interpreter file instead, for example the output of
`python -c "import pathlib, sys; print(pathlib.Path(sys.executable).resolve())"`,
and pin that same path. The resolved file is the base interpreter and does not
load the environment's packages; a collector that needs them can run from an
environment created with `python -m venv --copies` on a path without links.

The collector must return a `deploy2-collect` result with either current
completion or authenticated historical completion, an independently reviewed answer contract, bound requested,
resolved and observed model, native edit observation, and a verified artifact.
The answer is read from the allowlisted root and checked against the collector's
hash and byte count. Held, missing, mismatched, malformed and changed results
are refused. Local process runs retain their existing separate behavior.
Historical results expose `recorded_completion_allowed` and the archive proof;
`completion_allowed` stays false and current live acceptance stays `not_run`.
