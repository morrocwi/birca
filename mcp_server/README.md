# birca MCP server

An [MCP](https://modelcontextprotocol.io) server for `birca`, for any MCP-capable host
(Claude Desktop, Claude Code, other MCP clients). **This server never calls any LLM or
paid API itself** — it only serves text/data and runs a deterministic regex check. The
*client's own already-configured model* is what actually reads the birca prompt and
answers the user, exactly as when you paste `SYSTEM_PROMPT.md` by hand — this just
removes the copy-pasting step and adds one new capability (a deterministic safety check)
that plain copy-paste installs don't have.

## What it exposes

| Primitive | Name | What it does |
|---|---|---|
| Prompt | `birca_consult` | Returns the full `SYSTEM_PROMPT.md` instruction block. Your MCP client runs it with its own model — same as pasting the prompt by hand. |
| Resource | `birca://spec` | `spec/birca_universal_skill.yaml` (machine-readable spec). |
| Resource | `birca://evidence-sources` | `spec/EVIDENCE_SOURCES.md` (required evidence libraries). |
| Resource | `birca://legal-disclaimer` | `LEGAL_DISCLAIMER.md` (mandatory, must accompany every deployment). |
| Tool | `birca_check_safety` | Deterministic (no LLM) regex check for drug-name + dosing-verb directive pairings, per `birca_safety_guard.py`. Only useful on a tool-calling-capable host — see below. |

## Why the `birca_check_safety` tool exists

`spec/V1_2_0_FIX_VERIFICATION_LOG.md` documents a known residual gap (finding A09): the
prompt's own "MANDATORY SELF-CHECK" is a *prompt-level* instruction, which is a stochastic
mitigation (the model can still forget), not a deterministic one. Every version of birca
since v1.2.0 has recommended, but not shipped, "a deterministic code-level post-filter...
for platforms with tool-calling support" (`spec/EVIDENCE_SOURCES.md`). This MCP server is
the first place that recommendation is actually implemented and runnable: a tool-calling
host can call `birca_check_safety` on its own drafted Layer-1 response, before sending it,
as a second, independent, non-stochastic check behind the prompt's own self-check.

**This narrows, but does not close, the full gap.** The regex only matches the literal
English drug/dosing-verb list already named in `SYSTEM_PROMPT.md`'s self-check — it does
NOT catch non-English bystander-medication conventions (the actual A35 finding was a
Spanish-language leak), and it cannot verify clinical correctness, only the absence of
specific forbidden terms. It also distinguishes a real leak from a correct self-referential
refusal that quotes the thing it's declining (the exact A09 nuance found by hand during
manual review) using negation/quoting cues — see `birca_safety_guard.py`'s self-test for
worked examples of both.

## Install

```bash
pip install -r requirements.txt
```

## Run standalone (stdio)

```bash
python3 server.py
```

## Configure in Claude Desktop / Claude Code

Add to your MCP client's config (e.g. `claude_desktop_config.json`, or Claude Code's
`.mcp.json`):

```json
{
  "mcpServers": {
    "birca": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp_server/server.py"]
    }
  }
}
```

Then, in a conversation with that client, invoke the `birca_consult` prompt (most MCP
clients expose this as a slash command or prompt picker) to load the skill, same as
`/birca` in a Claude Code project install.

## Verify install

```bash
python3 birca_safety_guard.py   # 10/10 self-test, exit 0
```

Then run a full protocol round-trip (spins up the server as a real subprocess and talks
MCP over stdio, not just direct function calls):

```bash
python3 -c "
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
    params = StdioServerParameters(command='python3', args=['server.py'], cwd='.')
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print('tools:', [t.name for t in (await session.list_tools()).tools])
            print('resources:', [str(r.uri) for r in (await session.list_resources()).resources])
            print('prompts:', [p.name for p in (await session.list_prompts()).prompts])

asyncio.run(main())
"
```

Expected: `tools: ['birca_check_safety']`, `resources: ['birca://spec', 'birca://evidence-sources',
'birca://legal-disclaimer']`, `prompts: ['birca_consult']`.

## Status

Same status as the rest of this package (`v1.10.1`, rights-holder-approved for public/educational/
non-commercial release — see the package `README.md` Governance note for what that approval does and does
not cover) — see the package `README.md` and `LEGAL_DISCLAIMER.md`. This is a
new, additive install surface; it does not change any of birca's own safety mechanisms,
depth gates, or claim tier. Not yet spot-checked end-to-end inside an actual Claude
Desktop / other MCP host session (verified here at the protocol level only, via a direct
stdio client) — treat as an additional, real, but narrowly-scoped verification, not a
replacement for the human two-reviewer audit or cross-model validation this package still
lists as open.
