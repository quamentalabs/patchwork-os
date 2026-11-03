# Third-Party Notices

**Patchwork-OS** (`quamentalabs/patchwork-os`) is licensed under the [Apache License, Version 2.0](LICENSE). See also [`NOTICE`](NOTICE). Commits made before the change to Apache-2.0 carry the MIT License.

## Design references

The projects below informed the design of Patchwork-OS. Patchwork-OS does not include their code or text, except where the last section says so.

On 2026-11-03 this repository was compared with the default branch of each upstream listed with an observed license. No file shared a run of five or more non-trivial lines with any of them, apart from the standard MIT license text and the helper named below. The comparison ignored differences in whitespace and letter case. It checked only those default branches, and it cannot detect paraphrase.

| Repository | License, as observed on 2026-11-03 | Use in Patchwork-OS |
| :--- | :--- | :--- |
| [`morluto/rea`](https://github.com/morluto/rea) | MIT (GitHub license API) | Design concept: event-sourced agent execution and append-only state replay |
| [`trailhq/Trail-Code`](https://github.com/trailhq/Trail-Code) | MIT (GitHub license API) | Design concept: CLI-first workflow hooks and isolated git worktree execution; also the source of the included helper code below |
| [`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent) | MIT (GitHub license API) | Design concept: self-evolving skill synthesis and closed-loop agent memory |
| [`buildermethods/agent-os`](https://github.com/buildermethods/agent-os) | MIT as previously declared; not checked on 2026-11-03 | Design concept: Builder Methods' original open-source Agent OS for spec-driven development. Patchwork-OS is a separate project. |
| [`mattpocock/skills`](https://github.com/mattpocock/skills) | MIT (GitHub license API) | Design concept: deterministic CLI skill scripts and task decomposition |
| [`johnfkoo951/cmds-share`](https://github.com/johnfkoo951/cmds-share) | MIT (GitHub license API) | Design concept: selective, hygiene-gated knowledge sharing |
| [`johnfkoo951/cmds-llm-wiki`](https://github.com/johnfkoo951/cmds-llm-wiki) | No license file published | Design concept only: the three-layer `raw/`, `wiki/`, `rules/` Markdown layout. No code or text is copied. |
| [`nateherkai/AIS-OS`](https://github.com/nateherkai/AIS-OS) | MIT (LICENSE file text; the GitHub API reports NOASSERTION) | Design concept: role-separated prompt-flow routing |
| [`Leonxlnx/unlazy`](https://github.com/Leonxlnx/unlazy) | MIT (GitHub license API) | Design concept: placeholder-first lazy context hydration |

## Included third-party code

`.claude/helpers/graft-statusline.cjs` contains portions derived from `@nanonets/graft` (npm package, MIT; source repository <https://github.com/trailhq/Trail-Code>). That file stays under the MIT License below. The other two helpers in `.claude/helpers/`, `statusline.js` and `patchwork-statusline-hybrid.cjs`, are also marked `SPDX-License-Identifier: Apache-2.0` and stay under the MIT License.

```text
MIT License

Copyright (c) 2026 Context Graph Engine contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

These notices are attribution. They do not amount to company approval or export-control clearance.
