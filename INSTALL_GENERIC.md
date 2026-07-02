# Install `birca` — any other LLM / assistant framework (Gemini, local models, LangChain, etc.)

Invocation name (always lowercase): **`birca`**

`birca` has no platform-specific syntax. It is one portable instruction block
(`SYSTEM_PROMPT.md`) plus a machine-readable spec (`spec/birca_universal_skill.yaml`) plus a required
disclaimer (`LEGAL_DISCLAIMER.md`). To install on any system that accepts a system/developer prompt:

1. `git clone http://192.168.1.120:3000/anse/cpg.git --branch <tag> --single-branch` (see **Release policy**
   below — do not point at a moving branch).
2. Load the fenced block inside `products/birca-global-health/universal_skill/SYSTEM_PROMPT.md` as that
   system's system-level instruction / persona / character prompt.
3. Surface `LEGAL_DISCLAIMER.md`'s emergency notice and required footer somewhere the end user will actually
   see it (not just buried in the system prompt) — most platforms need this repeated as a UI banner too.
4. Wire read-only calls to the libraries in `spec/EVIDENCE_SOURCES.md` if your framework supports tool/
   function calling (LangChain tools, Gemini function calling, local-model agent frameworks, etc.).

## Google Gemini (example)

```python
import google.generativeai as genai
with open("SYSTEM_PROMPT.md") as f:
    text = f.read()
birca_prompt = text.split("```\n", 1)[1].rsplit("\n```", 1)[0]
model = genai.GenerativeModel("gemini-2.5-pro", system_instruction=birca_prompt)
```

## Self-hosted / local models (Ollama, vLLM, etc.)

Prepend the same fenced block as the system message on every request. Local models with weaker instruction-
following may need the block repeated at the start of each turn, not just once at session start — test with
the emergency-triage adversarial prompts in `spec/BIRCA_STRESS_TEST_AND_FAILURE_MODES.md` (in this repo) before
trusting a local-model deployment.

## Release policy — pin a tag, never a moving branch

**Only install a tagged release** (e.g. `birca-v1.0.0`), never the `main` or `feat/*` development branch, in
any deployment beyond your own local testing. Reasons: (1) development branches change without notice — a
production install could silently drift from the audited disclaimer text or safety rules; (2) this package
is `DRAFT_NOT_YET_HUMAN_APPROVED` until a tagged, reviewed release exists; (3) pinning a tag makes the
install auditable — you can always answer "which exact version is running" from the tag alone. `install.sh`
enforces this: it refuses to run against an unreleased/untagged checkout unless you pass `--allow-draft`
explicitly, and prints a loud warning when it does.

## Verify install

Ask a mild, non-emergency symptom question. The response must open with the `BIRI % · D<level> ·
Missing:[...] · Next questions(<=7)` line, must run the safety screen before anything else, and must close
with the disclaimer footer. If your model skips either, the instruction block was likely truncated or
diluted by a longer competing system prompt — give `birca`'s block priority/precedence in your prompt stack.

Status: v1.2.0, human-approved public release. Human two-reviewer audit and cross-model validation remain open (see README "What's still open"). See `LEGAL_DISCLAIMER.md` before any real deployment.
