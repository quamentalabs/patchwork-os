# Ollama local judge

The local judge is advisory and cannot authorize native task completion or review acceptance.

Initialize with `pwos --root WORKSPACE init`, then explicitly edit `WORKSPACE/.patchwork/config.json`:

```json
{"schema_version":1,"binding":"example-scope","runtimes":{},"local_judge":{"protocol":"ollama","url":"http://127.0.0.1:11434","model":"YOUR-EXPLICIT-LOCAL-MODEL","admission":"resident_gpu_only","timeout_seconds":30}}
```

Preserve existing runtime entries. Prepare an event JSON file: `{"binding":"example-scope","raw_path":"ABSOLUTE-PATH"}`. Invoke `pwos --root WORKSPACE hook run --input EVENT.json`.

Before generation `/api/ps` must report exactly the configured model resident with a nonempty digest, size_vram >= size, and context length at least 8192. `/api/show` must advertise boolean false as a supported thinking value. Generation requests `think:false`, JSON format, non-streaming, temperature 0, 8192 context and 999 GPU layers. Postflight must show the same digest and GPU/context conditions. The adapter never requests model downloads or deliberate loading. An absent model, insufficient or unmeasured residency, unsupported thinking control, HTTP failure, invalid or foreign result, changed model, or incomplete generation produces an ambiguous verdict. An operator may separately load a local model after checking resources.

Preflight, generation and postflight are not atomic: another client may unload or change the model between them, and GPU placement reports are observations rather than proof that CPU fallback was impossible. An empty thinking output demonstrates the requested protocol behavior, not the absence of internal reasoning.

Artifacts are under `WORKSPACE/.patchwork/hooks/`. The result JSON contains input location and hash, processed scope and hash, and judge evidence paths and hashes. The `.raw` file preserves full input bytes; `*.preflight.response.json`, `*.show.request.json`, `*.show.response.json`, `*.generate.request.json`, `*.generate.response.json`, and `*.postflight.response.json` capture corresponding HTTP bytes when available. A response over 65536 bytes is retained through the bounded read, marked truncated and cannot pass. A validated structured verdict, including ambiguous, is deduplicated for identical input and configuration. Ambiguous results caused by transport, admission, malformed or incomplete responses are re-evaluated on the next invocation. Artifacts contain task content.

API references: [Ollama generate](https://docs.ollama.com/api/generate), [running models](https://docs.ollama.com/api/ps), [thinking controls](https://docs.ollama.com/capabilities/thinking).
