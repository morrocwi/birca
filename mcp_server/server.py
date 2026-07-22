"""
birca MCP server.

CHAT LAYER (unchanged since v1.x): exposes birca as MCP primitives, deliberately with NO
LLM call inside this server (this server never contacts any paid model API -- it only
serves text/data and runs a deterministic regex check). The MCP client's own
already-configured model is what actually reads the prompt and answers the user; this
server's job is to make the birca skill installable in any MCP-capable host with zero
copy-pasting, and to give tool-calling-capable hosts a deterministic, code-level pre-send
check that the prompt's own self-check cannot guarantee on its own (see
spec/V1_2_0_FIX_VERIFICATION_LOG.md, the A09 finding).

  1. PROMPT  `birca_consult`      -- the full SYSTEM_PROMPT.md block as an MCP prompt
                                     template; the client's own model runs it.
  2. RESOURCES                    -- spec/birca_universal_skill.yaml, EVIDENCE_SOURCES.md,
                                     LEGAL_DISCLAIMER.md, served read-only.
  3. TOOL    `birca_check_safety` -- wraps birca_safety_guard.check_response(); a
                                     tool-calling client can run this on its own drafted
                                     response BEFORE sending it, as a deterministic second
                                     check behind SYSTEM_PROMPT.md's prompt-level one.

COMPUTE LAYER (new in v5.0.0, see ../compute/ and CHANGELOG.md): four additional tools,
each a thin, honest wrapper around a vendored, independently-runnable script under
`compute/` -- never invoked automatically, never replacing the chat layer's safety gates,
always available for a tool-calling host to invoke when a Layer 2/3 turn genuinely needs
research-grade computation instead of prose:

  4. TOOL `birca_math_consistency_check` -- runs the vendored BIRCA repair-equation
                                            solvers (compute/birca_math/), live-verifying
                                            the claim spec/birca_universal_skill.yaml's
                                            mathematical_consistency_finding field states.
  5. TOOL `birca_evidence_quotient_check`-- runs cited claims through the vendored QOR
                                            citation checker (compute/rg_qor/) to catch
                                            uncited or value-mismatched claims in code,
                                            not just by asking the model to self-check.
  6. TOOL `birca_drug_food_lane_plan`    -- runs the vendored RG Open-Science drug-food-
                                            disease compiler's workflow-plan command
                                            (compute/rg_open_science/); strictly a
                                            research-mode planning tool, never surfaced in
                                            an individual health-intake turn (see that
                                            package's own forbidden_outputs list).
  7. TOOL `birca_docking_admission`      -- re-docks an externally-sourced, already-known
                                            ligand into its own crystal binding site
                                            (compute/docking/) as a docking-software
                                            accuracy check; never generates a novel
                                            molecule or receptor.

claim tier: this server ships code, not a clinical claim. It does not diagnose, treat, or
give medical advice; it only serves the same skill text/spec already public in this repo,
runs a plain-text regex scan, and (compute layer) runs vendored research scripts that each
carry their own explicit claim tier and scope boundary (see PROVENANCE.md and each
compute/ subdirectory's own README). NOT medical advice. Not a substitute for
LEGAL_DISCLAIMER.md, which every deploying party must still surface to end users.
"""
from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from birca_safety_guard import check_response
from birca_compute_bridge import (
    birca_docking_admission as _birca_docking_admission,
    birca_drug_food_lane_plan as _birca_drug_food_lane_plan,
    birca_math_consistency_check as _birca_math_consistency_check,
)
from birca_evidence_bridge import check_claim_citations as _check_claim_citations

_HERE = Path(__file__).resolve().parent
_SKILL_ROOT = _HERE.parent

_START_MARKER = "<!-- BIRCA_PROMPT_START -->"
_END_MARKER = "<!-- BIRCA_PROMPT_END -->"


def _read_required(path: Path) -> str:
    """Read `path`, raising a descriptive RuntimeError (not a bare FileNotFoundError) if
    it's missing -- a peer review found the resource handlers below called
    Path.read_text() directly with no error handling, unlike _extract_system_prompt's
    careful guarding, so a missing/renamed/moved file surfaced as a raw traceback with no
    context about which file was expected where."""
    if not path.is_file():
        raise RuntimeError(
            f"birca MCP server: expected file not found at {path} -- it may have been "
            "moved, renamed, or deleted."
        )
    return path.read_text(encoding="utf-8")


def _extract_system_prompt() -> str:
    """Extract the fenced instruction block from SYSTEM_PROMPT.md, the same
    marker-based method install.sh uses -- kept independent (no shared import) so this
    server has no dependency on install.sh's shell logic.

    Strips only the OUTER fence pair (the first and last '```' line in the marked
    block), not every line that happens to read '```'. A peer review found the original
    version stripped every such line -- harmless today (SYSTEM_PROMPT.md has exactly one
    fence pair), but it would silently corrupt the extracted prompt the moment a future
    edit adds a nested fenced code example inside the marked block, with no error raised.
    """
    text = _read_required(_SKILL_ROOT / "SYSTEM_PROMPT.md")
    try:
        start = text.index(_START_MARKER) + len(_START_MARKER)
        end = text.index(_END_MARKER, start)
    except ValueError as exc:
        # A peer review found these two lookups raised a bare, unhelpful
        # "substring not found" ValueError if a marker was missing/renamed -- the more
        # likely real-world break, and the opposite of the fence-count/length checks
        # below, which already raise a descriptive RuntimeError for their own failure
        # modes. Re-raised here in the same style for consistency.
        raise RuntimeError(
            "birca MCP server: could not find BIRCA_PROMPT_START/END markers in "
            "SYSTEM_PROMPT.md -- they may be missing or renamed."
        ) from exc
    block = text[start:end]
    lines = block.splitlines()
    fence_idxs = [i for i, ln in enumerate(lines) if ln.strip() == "```"]
    if len(fence_idxs) < 2:
        raise RuntimeError(
            "birca MCP server: expected an opening and closing ``` fence inside the "
            f"BIRCA_PROMPT_START/END block, found {len(fence_idxs)} -- markers may be "
            "missing or renamed."
        )
    first, last = fence_idxs[0], fence_idxs[-1]
    inner_lines = lines[first + 1:last]
    extracted = "\n".join(inner_lines).strip("\n")
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
        "sending it, as a deterministic second check. Four additional compute tools "
        "(birca_math_consistency_check, birca_evidence_quotient_check, "
        "birca_drug_food_lane_plan, birca_docking_admission) are available for "
        "research-grade computation -- never mandatory, never a substitute for the "
        "chat layer's own safety gates. For educational and research purposes only, "
        "not for commercial use -- see LEGAL_DISCLAIMER.md."
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
    return _read_required(_SKILL_ROOT / "spec" / "birca_universal_skill.yaml")


@mcp.resource("birca://evidence-sources", name="birca_evidence_sources", description="Required evidence libraries and grounding notes (EVIDENCE_SOURCES.md)")
def get_evidence_sources() -> str:
    return _read_required(_SKILL_ROOT / "spec" / "EVIDENCE_SOURCES.md")


@mcp.resource("birca://legal-disclaimer", name="birca_legal_disclaimer", description="Mandatory legal disclaimer -- must accompany every deployment (LEGAL_DISCLAIMER.md)")
def get_legal_disclaimer() -> str:
    return _read_required(_SKILL_ROOT / "LEGAL_DISCLAIMER.md")


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


@mcp.tool(
    name="birca_math_consistency_check",
    description=(
        "Run the vendored BIRCA repair-equation solvers (compute/birca_math/) and report "
        "pass/fail. Live-verifies the same claim spec/birca_universal_skill.yaml's "
        "mathematical_consistency_finding field states in prose. finite_diagnostic tier -- "
        "internal mathematical consistency only, NOT clinical or empirical validation."
    ),
)
def birca_math_consistency_check() -> dict:
    return _birca_math_consistency_check()


@mcp.tool(
    name="birca_evidence_quotient_check",
    description=(
        "Code-level (not model-asserted) citation validator: given a list of claims "
        "({claim_id, fact_key, value, citations}) and evidence items "
        "({evidence_id, fact_key, value}), runs the vendored RG_QOR standalone's own "
        "ClaimCitationChecker and returns any defects -- uncited claims, citations that "
        "don't exist in the evidence set, or claims whose value doesn't match what their "
        "citation actually says. Use this to check a drafted response's citations before "
        "sending, the same way birca_check_safety checks for a directive-shaped leak."
    ),
)
def birca_evidence_quotient_check(claims: list[dict], evidence: list[dict]) -> dict:
    return _check_claim_citations(claims, evidence)


@mcp.tool(
    name="birca_drug_food_lane_plan",
    description=(
        "Run the vendored RG Open-Science drug-food-disease compiler's workflow-plan "
        "command (compute/rg_open_science/) for a named workflow (default: "
        "integrated_drug_food_lane_research). STRICTLY a research-mode planning tool -- "
        "never surfaced as part of an individual health-intake conversation turn; returns "
        "no dosing, no SMILES, no synthesis routes, no docking-ready coordinates (see the "
        "package's own scope_and_safety_boundary.forbidden_outputs)."
    ),
)
def birca_drug_food_lane_plan(workflow: str = "integrated_drug_food_lane_research") -> dict:
    return _birca_drug_food_lane_plan(workflow)


@mcp.tool(
    name="birca_docking_admission",
    description=(
        "Re-dock an externally-sourced, already-known ligand (a real RCSB PDB entry ID "
        "plus that entry's own 3-letter ligand chemical-component code) into its own "
        "crystallographic binding site via AutoDock Vina (compute/docking/) and report "
        "PASS/FAIL/UNRESOLVED with RMSD vs. the real experimental pose. This is a "
        "docking-SOFTWARE accuracy check, not drug discovery -- it never generates a "
        "novel molecule, receptor, or binding site; requires a vina-capable Python "
        "environment (see compute/docking/README.md)."
    ),
)
def birca_docking_admission(pdb_id: str, ligand_code: str, ligand_chain: str = "A") -> dict:
    return _birca_docking_admission(pdb_id, ligand_code, ligand_chain)


if __name__ == "__main__":
    mcp.run()
