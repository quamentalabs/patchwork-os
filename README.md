# Patchwork-OS (preview)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Patchwork-OS** is a local Python workflow library and CLI. The `pwos` command initializes a workspace, launches an explicitly configured process, collects its transcript, and closes the run. An optional loopback web cockpit displays local runs. The package also contains workflow contracts and reference procedures.

## Quickstart: install and run a local process

Python 3.11 or newer and Git are required. After receiving repository access, clone and install into a virtual environment outside the checkout. Installation resolves the declared dependencies, including `pywinpty` on Windows. No vendor AI CLI or account is needed for this example.

Windows (PowerShell):

~~~powershell
git clone https://github.com/quamentalabs/patchwork-os.git
cd patchwork-os
python -m venv ../patchwork-venv
../patchwork-venv/Scripts/python.exe -m pip install .
../patchwork-venv/Scripts/python.exe examples/local_echo.py --workspace ../patchwork-demo
~~~

Linux / macOS:

~~~sh
git clone https://github.com/quamentalabs/patchwork-os.git
cd patchwork-os
python3 -m venv ../patchwork-venv
../patchwork-venv/bin/python -m pip install .
../patchwork-venv/bin/python examples/local_echo.py --workspace ../patchwork-demo
~~~

Use a new `patchwork-demo` directory for each run. The [example](examples/local_echo.py) refuses an existing workspace or one inside the checkout. It initializes the workspace, configures a plain Python echo process, and calls the installed `pwos` entry point through `init → doctor → run → status → collect → close`. It checks the exact echoed text, successful process exit, transcript hash, packaged procedure index, and released run lease. Success prints a JSON object with `"status": "passed"` and the run ID. Its `muse` configuration slot selects the local echo process; it does not launch a vendor agent.

The workspace retains the task, process configuration, transcript and run records under `.patchwork/`. Keep that directory private: its owner record contains a local API token. It is excluded by this repository's `.gitignore`. The optional [CI template](ci/quickstart.yml) defines this same installed-package example on Windows and Linux with Python 3.11. To enable GitHub Actions, copy it to `.github/workflows/quickstart.yml` using an account with workflow-management permission. The template is inactive in this repository; local results do not establish a GitHub Actions pass.

## Configure your own executable

`pwos --root /path/to/workspace init` creates `.patchwork/config.json` without overwriting existing configuration. Each `runtimes` entry uses an absolute `executable` path, an `args` array, `delivery` (`stdin` or `task_file`), and optional `model` and `effort`. Argument placeholders are `{model}`, `{effort}`, `{home}` and `{task_file}`. [examples/echo_backend.py](examples/echo_backend.py) is the executable payload used by the quickstart.

Using your environment's `pwos` executable:

~~~text
pwos --help
pwos --root /path/to/workspace doctor
pwos --root /path/to/workspace run muse --task-file /path/to/task.txt
pwos --root /path/to/workspace status RUN_ID
pwos --root /path/to/workspace collect RUN_ID
pwos --root /path/to/workspace close RUN_ID
pwos --root /path/to/workspace serve
~~~

`serve` starts the loopback-only web cockpit. Terminal mode uses a persistent PTY; `pwos input RUN_ID` reads input from stdin, and `collect` returns the transcript. The web display preserves terminal text and ANSI sequences without emulating a full terminal. The quickstart exercises task mode, not the browser or interactive terminal.

Vendor CLIs must be installed, authenticated and configured separately. The `cc`, `codex`, `agy` and `muse` labels do not establish successful native integration. A process exit or transcript does not prove native Edit, observed model/effort or independent review; the local echo run keeps native and review acceptance at `not_run`. [External native result attachment](docs/external-native.md) documents the optional, explicitly configured collector boundary. The package does not supply that external collector or establish its evidence by itself.

## Python planning API

This separate example returns a nonexecuting plan dictionary:

```python
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from patchwork_os import plan_inter_cli_dispatch

with TemporaryDirectory() as directory:
    workspace = Path(directory)
    task = workspace / "task.md"
    task.write_bytes(b"Review a local nonsensitive sample.\n")
    plan = plan_inter_cli_dispatch(
        owner_session="local-evaluation",
        run_id="sample",
        target_runtime="codex",
        task_path=task,
        workspace_root=workspace,
        model_override="example-model",
    )
    assert plan["kind"] == "deploy2-cli-plan"
    assert plan["execution_supported"] is False
    assert plan["task"]["sha256"] == sha256(task.read_bytes()).hexdigest()
    assert plan["runtime_acceptance"] == "not_run"
    assert not Path(plan["run_dir"]).exists()
    assert not Path(plan["result_dir"]).exists()
    print(plan["kind"])
```

The API returns a plan dictionary. It does not launch an agent or create run/result directories. `launch_argv` is a descriptive compatibility template, not a supported command. `dry_run=False` raises `NotImplementedError`; a missing task raises `FileNotFoundError`, and a directory or other non-regular task raises `ValueError`. A real empty file is valid. `python -m patchwork_os.deploy_cli --help` is not a supported CLI; the observed baseline exited zero with no help output.

The quickstart covers the local process lifecycle, and the planning sample above covers only plan construction. Other APIs remain outside these examples: `bootstrap_agnostic_hub` writes project resources and can reach a Windows junction fallback; `safe_bind_spoke(..., allow_junction=True)` can invoke `cmd.exe /c mklink /J` when the directory symlink path fails on Windows; `build_deterministic_payload` can invoke `git diff` and `git status` when overrides are absent. `allow_junction=False` disables that junction branch, not every possible side effect, and does not bring these APIs into the evaluation scope. The existing default is unchanged. Runtime routing and setup/profile APIs also remain outside the sample and expose unverified example data, not assessed provider/compliance/model/cost guarantees.

Remove the package with the same environment's `python -m pip uninstall patchwork-os`. Delete only the dedicated environment and sample workspace you created when no longer needed. Uninstalling the package does not remove workspace data.

The repository's `.claude/settings.json` is intentionally empty. Existing statusline commands and permission allow entries are preserved in the inactive `.claude/settings.example.json`. Reading that example does not enable it. Any later manual configuration requires separate review of the commands, helpers, permissions, and local policy; it is not part of this evaluation. Do not overwrite user/global settings or enable external AI, hooks, or permission bypass for the sample.

ITAR status, company authorization, upstream license clearance, complete isolation and authenticated/signed dispatch are unverified. Task/prompt hashes are integrity descriptors, not signatures or authorization.

## 1. Repository Document Topology

```mermaid
flowchart TD
  H["Hub Index (knowledge/index.md)"] --> R["Raw Layer (raw/source-manifest.md)"]
  H --> W["Wiki Layer (wiki/patchwork-os-architecture.md)"]
  H --> L["Rules Layer (rules/patchwork-os-contract.md)"]
  R --> G["AST Graph Design References"]
  W --> P["Prompt-Flow Design References"]
  L --> T["Escalation Contract References"]
```

## 2. Five Pillars and Design References

This table preserves design references and intended counterpart coverage. Upstream license/version provenance has not been independently verified here. Background hooks, live dispatch, model routing and graph services are not installed or proven by this table.

| Pillar | Design References | License Review | Intended Assimilation | Intended Counterpart Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **1. Workflow Engine** | `morluto/rea`, `trailhq/Trail-Code` | Unverified | Event ledgers and workflow hooks | Bounded retries and dependency gates |
| **2. Meta-Prompting** | `NousResearch/hermes-agent`, `buildermethods/agent-os`, `mattpocock/skills` | Unverified | Skill/spec procedures | Explicit knowledge and mutation contracts |
| **3. Graph-Prompting** | `graft`, `johnfkoo951/cmds-llm-wiki`, `johnfkoo951/cmds-share` | Unverified | AST graph and three-layer wiki references | Pointer routing and local validation |
| **4. Prompt-Flow** | `nateherkai/AIS-OS` | Unverified | Role-separated pipeline procedures | Explicit capability and routing boundaries |
| **5. Lazy Hydration** | `Leonxlnx/unlazy` | Unverified | On-demand source reading | Index-first bounded context |

## 3. Repository Layout

- [`LICENSE`](LICENSE) — Standard **MIT License** (`SPDX-License-Identifier: MIT`)
- [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) — Attribution records requiring separate provenance review
- [`pyproject.toml`](pyproject.toml) — Package version, Python requirement and license-file reference
- `docs/architecture/patchwork-os-blueprint.md` — Full architectural blueprint
- `knowledge/` — CMDS 3-layer knowledge hub (`index.md`, `raw/`, `wiki/`, `rules/`)
- `src/patchwork_os/` — Python configuration, binding, contract and dispatch-planning APIs; external runtime effects need separate evidence
- `.claude/` — Empty local-evaluation defaults, inactive opt-in settings example, and preserved optional helpers (`statusline.js`, `patchwork-statusline-hybrid.cjs`, `graft-statusline.cjs`)
- `tests/` — Unit and contract tests; passing tests do not establish live runtime acceptance

## 4. License

The project declares the MIT License in [`LICENSE`](LICENSE) and its package metadata. [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) preserves attribution records. This declaration does not establish upstream provenance, company approval or export-control clearance.

## Generalized Skill Skeleton Procedures (`skills/pwos-*`)

The repository contains 18 Markdown procedure skeletons under the `pwos-*` namespace. [`skills/INDEX.md`](skills/INDEX.md) is the canonical complete inventory; `patchwork_os.skills_registry.resolve_skill_id` resolves aliases. The package declares copies under `patchwork_os/resources/skills/`; the quickstart reads their packaged index. These resources are not registered automatically as vendor-native skills. Procedure descriptions are design/runbook instructions, not proof that a launcher, hook or integration is implemented. Selected existing pointers are retained below; use the index for all 18:

- [`skills/pwos-grilling/SKILL.md`](skills/pwos-grilling/SKILL.md) - Relentless one-question-at-a-time decision-tree interview
- [`skills/pwos-quarry/SKILL.md`](skills/pwos-quarry/SKILL.md) - Durable write-before-next-question requirement extraction
- [`skills/pwos-deconstruct/SKILL.md`](skills/pwos-deconstruct/SKILL.md) - 7-stage `KK/KU/UK/UU` + `FRR` epistemic deconstruction and option scoring
- [`skills/pwos-crucible/SKILL.md`](skills/pwos-crucible/SKILL.md) - Multi-round construction-blind design smelting with seeded-flaw dryness assay
- [`skills/pwos-systematic-debugging/SKILL.md`](skills/pwos-systematic-debugging/SKILL.md) - 7-phase ledger-first read-only root-cause analysis and mutation debugging
- [`skills/pwos-tdd/SKILL.md`](skills/pwos-tdd/SKILL.md) - 9-step hand-compose, register-early, scriptify, and run-x3 byte-parity build order
- [`skills/pwos-stdd/SKILL.md`](skills/pwos-stdd/SKILL.md) - 3-tier role-disjoint subagent-driven development + TDD lifecycle
- [`skills/pwos-fable-mode/SKILL.md`](skills/pwos-fable-mode/SKILL.md) - 6-gate `3xPR + FRR + KK/KU/UK/UU + no-tradeoff` execution wrapper
- [`skills/pwos-wfc/SKILL.md`](skills/pwos-wfc/SKILL.md) - 5-wave `MPT:N` Multi-Persona Triage DAG orchestration
- [`skills/pwos-rea/SKILL.md`](skills/pwos-rea/SKILL.md) - 4-stage Forward-Reverse-Roundtrip (`FRR`) reverse-engineering verification
