"""
birca MCP server.

Exposes birca as three MCP primitives, deliberately with NO LLM call inside this server
(this server never contacts any paid model API -- it only serves text/data and runs a
deterministic regex check). The MCP client's own already-configured model is what
actually reads the prompt and answers the user; this server's job is to make the birca
skill installable in any MCP-capable host with zero copy-pasting, and to give
tool-calling-capable hosts a deterministic, code-level pre-send check that the prompt's
own self-check cannot guarantee on its own (see spec/V1_2_0_FIX_VERIFICATION_LOG.md, the
A09 finding).

  1. PROMPT  `birca_consult`      -- the full SYSTEM_PROMPT.md block as an MCP prompt
                                     template; the client's own model runs it.
  2. RESOURCES                    -- spec/birca_universal_skill.yaml, EVIDENCE_SOURCES.md,
                                     LEGAL_DISCLAIMER.md, served read-only.
  3. TOOL    `birca_check_safety` -- wraps birca_safety_guard.check_response(); a
                                     tool-calling client can run this on its own drafted
                                     response BEFORE sending it, as a deterministic second
                                     check behind SYSTEM_PROMPT.md's prompt-level one.

claim tier: this server ships code, not a clinical claim. It does not diagnose, treat, or
give medical advice; it only serves the same skill text/spec already public in this repo
and runs a plain-text regex scan. NOT medical advice. Not a substitute for
LEGAL_DISCLAIMER.md, which every deploying party must still surface to end users.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from birca_safety_guard import check_response

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent

_START_MARKER = "<!-- BIRCA_PROMPT_START -->"
_END_MARKER = "<!-- BIRCA_PROMPT_END -->"


def _extract_system_prompt() -> str:
    """Extract the fenced instruction block from SYSTEM_PROMPT.md, the same
    marker-based method install.sh uses -- kept independent (no shared import) so this
    server has no dependency on install.sh's shell logic."""
    text = (_SKILL_ROOT / "SYSTEM_PROMPT.md").read_text(encoding="utf-8")
    start = text.index(_START_MARKER) + len(_START_MARKER)
    end = text.index(_END_MARKER, start)
    block = text[start:end]
    lines = [ln for ln in block.splitlines() if ln.strip() != "```"]
    extracted = "\n".join(lines).strip("\n")
    if len(extracted.splitlines()) < 20:
        raise RuntimeError(
            "birca MCP server: extracted SYSTEM_PROMPT.md block is suspiciously short "
            f"({len(extracted.splitlines())} lines) -- markers may be missing or renamed."
        )
    return extracted


mcp = FastMCP(
    name="birca",
    instructions=(
        "birca: a safety-gated, context-bound health-information skill. Call the "
        "'birca_consult' prompt to load the full skill instructions, then follow them "
        "exactly for any health-related turn. If your host supports tool calling, call "
        "'birca_check_safety' on any Layer-1 emergency response you draft, before "
        "sending it, as a deterministic second check. For educational and research "
        "purposes only, not for commercial use -- see LEGAL_DISCLAIMER.md."
    ),
)


@mcp.prompt(
    name="birca_consult",
    description=(
        "Load the full birca system prompt (safety-gated, context-bound health-"
        "information skill). Run the returned instructions exactly for the user's "
        "health-related question."
    ),
)
def birca_consult() -> str:
    return _extract_system_prompt()


@mcp.resource("birca://spec", name="birca_spec", description="Machine-readable birca skill spec (birca_universal_skill.yaml)")
def get_spec() -> str:
    return (_SKILL_ROOT / "spec" / "birca_universal_skill.yaml").read_text(encoding="utf-8")


@mcp.resource("birca://evidence-sources", name="birca_evidence_sources", description="Required evidence libraries and grounding notes (EVIDENCE_SOURCES.md)")
def get_evidence_sources() -> str:
    return (_SKILL_ROOT / "spec" / "EVIDENCE_SOURCES.md").read_text(encoding="utf-8")


@mcp.resource("birca://legal-disclaimer", name="birca_legal_disclaimer", description="Mandatory legal disclaimer -- must accompany every deployment (LEGAL_DISCLAIMER.md)")
def get_legal_disclaimer() -> str:
    return (_SKILL_ROOT / "LEGAL_DISCLAIMER.md").read_text(encoding="utf-8")


@mcp.tool(
    name="birca_check_safety",
    description=(
        "Deterministic, code-level check (no LLM call) for a drafted birca Layer-1 "
        "STOP response: scans for drug-name + dosing-verb directive pairings named in "
        "SYSTEM_PROMPT.md's own mandatory self-check list. Run this on your own drafted "
        "response BEFORE sending it. Returns passed=false if a directive-shaped leak is "
        "found; regenerate the response without that sentence if so. weak_matches are "
        "drug names mentioned without a nearby dosing verb, or preceded by a refusal/"
        "negation cue (e.g. quoting the thing being declined) -- usually fine, but "
        "surfaced for you to glance at."
    ),
)
def birca_check_safety(drafted_response: str) -> dict:
    return check_response(drafted_response).to_dict()


if __name__ == "__main__":
    mcp.run()
