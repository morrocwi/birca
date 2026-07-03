# Install `birca` — OpenAI (Custom GPT / Assistants / Responses API)

Invocation name (always lowercase): **`birca`**

## Option A — Custom GPT (ChatGPT)

1. Create a new GPT → **Configure**.
2. Name: `birca` (lowercase, matches the call name everywhere else).
3. Paste the fenced instruction block from `SYSTEM_PROMPT.md` into **Instructions**.
4. Under **Knowledge**, upload `LEGAL_DISCLAIMER.md` and `spec/EVIDENCE_SOURCES.md`.
5. Under **Capabilities**, enable **Web browsing** so the model can actually reach the Tier-1/2/3 libraries
   in `spec/EVIDENCE_SOURCES.md` (PubMed, WHO, CDC, MedlinePlus, openFDA, DailyMed) instead of relying on
   memory — required for the "anchor every clinical statement to a live source" rule to hold.
6. Do not enable Code Interpreter file-write or any action that could store identifiable health data outside
   the conversation, unless your own deployment has independently reviewed data-protection compliance.

## Option B — Assistants API / Responses API (developer integration)

```python
from openai import OpenAI
client = OpenAI()

with open("SYSTEM_PROMPT.md") as f:
    text = f.read()
birca_prompt = text.split("```\n", 1)[1].rsplit("\n```", 1)[0]

response = client.responses.create(
    model="gpt-5",
    instructions=birca_prompt,
    input="<user health question>",
)
```

For the Assistants API, pass the same `birca_prompt` string as the assistant's `instructions` field when
creating the assistant, and register function tools for the read-only libraries in
`spec/EVIDENCE_SOURCES.md` (e.g. a `pubmed_search` function calling NCBI E-utilities, an `openfda_label`
function calling openFDA) so the model can call out for live evidence instead of guessing.

## Option C — plain system-prompt injection (any OpenAI-compatible chat endpoint)

Any endpoint that accepts a `system`/`developer` role message (including self-hosted OpenAI-compatible
servers) can install `birca` the same way: put the fenced block from `SYSTEM_PROMPT.md` as the first
system message, every turn.

## Verify install

Same check as the Claude install: ask a mild, non-emergency symptom question and confirm the reply opens
with the `BIRI % · D<level>` disclosure line and ends with the disclaimer footer. If web browsing/function
tools are off, the model should say explicitly that it cannot verify current guidance rather than guessing.

Status: v1.10.6. `human_pi` (the rights holder) approved publishing this package publicly under a non-commercial license -- a narrower, separate approval from a clinical-safety review. Human two-reviewer audit and cross-model validation remain open (see README "What's still open"). See `LEGAL_DISCLAIMER.md` before any real deployment.
