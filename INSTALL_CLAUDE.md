# Install `birca` — Claude (Claude Code / Claude API / Claude Projects)

Invocation name (always lowercase): **`birca`**

## Option A — Claude Code project skill (recommended for this repo style)

```bash
git clone https://github.com/morrocwi/birca.git
cd birca
./install.sh claude-code /path/to/your/project
```

This copies `SYSTEM_PROMPT.md` to `<target>/.claude/commands/birca.md` so it becomes available as the
slash command `/birca` in that project, and appends a pointer to it in `<target>/CLAUDE.md` if one exists.

Manual equivalent:
```bash
mkdir -p /path/to/your/project/.claude/commands
cp SYSTEM_PROMPT.md /path/to/your/project/.claude/commands/birca.md
cp LEGAL_DISCLAIMER.md /path/to/your/project/.claude/commands/birca-disclaimer.md
```
Then in that project, type `/birca <health question or context to organize>`.

## Option B — Claude API (Messages API), any language

Load `SYSTEM_PROMPT.md`'s fenced block as the `system` parameter:

```python
import anthropic
client = anthropic.Anthropic()

with open("SYSTEM_PROMPT.md") as f:
    text = f.read()
birca_prompt = text.split("```\n", 1)[1].rsplit("\n```", 1)[0]  # extract the fenced instruction block

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=2000,
    system=birca_prompt,
    messages=[{"role": "user", "content": "<user health question>"}],
)
```

## Option C — Claude Projects (claude.ai)

1. Create a new Project.
2. Open **Project knowledge** → **Custom instructions** and paste the fenced block from `SYSTEM_PROMPT.md`.
3. Upload `LEGAL_DISCLAIMER.md` and `spec/EVIDENCE_SOURCES.md` to Project knowledge so Claude can cite them.
4. (Optional) Enable web search / connectors in the Project so Claude can actually reach the libraries listed
   in `spec/EVIDENCE_SOURCES.md` rather than relying on memory.

## Wiring live evidence sources (recommended, not optional for production use)

If your Claude integration supports tool use / MCP, wire read-only tools for the Tier-1/2/3 sources in
`spec/EVIDENCE_SOURCES.md` (PubMed E-utilities, openFDA, DailyMed, MedlinePlus, WHO GHO, ClinicalTrials.gov)
so the "anchor every clinical statement to a live source" rule in the system prompt can actually be
satisfied. See `research/governance/sim/birca_live_evidence.py` in this repo for a reference pattern (pure
guard function + injectable fetch).

## Verify install

Ask: `/birca I've had a mild headache for 3 days, no other symptoms.` — the reply should open with the
`BIRI % · D<level> · Missing:[...] · Next questions(<=7)` disclosure line, run the safety screen first, and
end with the required disclaimer footer. If either is missing, the install is incomplete — recheck that the
full `SYSTEM_PROMPT.md` block (not a truncated copy) was loaded.

Status: v1.10.4. `human_pi` (the rights holder) approved publishing this package publicly under a non-commercial license -- a narrower, separate approval from a clinical-safety review. Human two-reviewer audit and cross-model validation remain open (see README "What's still open"). See `LEGAL_DISCLAIMER.md` before any real deployment.
