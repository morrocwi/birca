"""
birca_compute_bridge.py — thin subprocess adapters exposing `compute/` as MCP tools.

Deliberately thin: every function here shells out to a vendored, independently-runnable
script in `compute/` and returns its structured output. No business logic is re-implemented
here, and no claim from those scripts is loosened or strengthened in translation -- this
file's only job is "run the real thing, return what it actually printed."

claim tier: whatever the underlying `compute/` script declares for its own output
(finite_diagnostic / Dr -- see each module's own docstring and PROVENANCE.md). This bridge
adds no new claim of its own.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
_COMPUTE = _REPO_ROOT / "compute"


def _run_python(script: Path, args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, cwd=str(cwd or script.parent),
    )


def birca_math_consistency_check() -> dict:
    """Run the two vendored BIRCA math solver self-tests (`compute/birca_math/`) and
    report whether they pass. This is the SAME check `spec/birca_universal_skill.yaml`'s
    `mathematical_consistency_finding` field describes in prose -- this function makes it
    live-runnable instead of a static claim. Requires numpy/scipy/sympy/networkx installed
    in the calling Python environment (see compute/birca_math/PROVENANCE.md).
    """
    results = {}
    for name in ("birca_repair.py", "health_atlas.py"):
        script = _COMPUTE / "birca_math" / name
        proc = _run_python(script, [])
        results[name] = {
            "exit_code": proc.returncode,
            "passed": proc.returncode == 0,
            "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-8:]),
            "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-8:]) if proc.stderr else "",
        }
    all_passed = all(r["passed"] for r in results.values())
    return {
        "claim_tier": "finite_diagnostic",
        "all_passed": all_passed,
        "results": results,
        "provenance": "compute/birca_math/PROVENANCE.md",
        "what_this_does_not_mean": (
            "Mathematical internal-consistency verification only (does the equation "
            "behave as its own surrounding prose says it should) -- NOT clinical or "
            "empirical validation of BIRCA's repair mechanism, and does not change "
            "BIRCA's own claim tier or eligibility gates."
        ),
    }


def birca_drug_food_lane_plan(workflow: str = "integrated_drug_food_lane_research") -> dict:
    """Run the vendored RG Open-Science drug-food-lane compiler's `workflow-plan` command
    (`compute/rg_open_science/`) for a named workflow and return its structured plan.
    Strictly a RESEARCH-mode planning tool -- see the package's own
    `scope_and_safety_boundary.forbidden_outputs` list (no dosing, no SMILES, no synthesis
    routes, no individual clinical recommendations). This tool must never be surfaced as
    part of an individual health-intake conversation turn; birca's own §8b
    out_of_scope_decline_rule already covers that separation.
    """
    runner = _COMPUTE / "rg_open_science" / "rg_open_science_runner.py"
    yaml_path = _COMPUTE / "rg_open_science" / "RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml"
    proc = _run_python(runner, ["--yaml", str(yaml_path), "workflow-plan", "--workflow", workflow])
    return {
        "exit_code": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "forbidden_outputs_note": (
            "This tool never returns SMILES, synthesis routes, dosing, or "
            "docking-ready coordinates -- see the package's own scope_and_safety_boundary."
        ),
    }


def birca_docking_admission(pdb_id: str, ligand_code: str, ligand_chain: str = "A") -> dict:
    """Re-dock a known, externally-solved ligand into its own crystallographic binding
    site via `compute/docking/docking_admission.py` and return PASS/FAIL/UNRESOLVED with
    RMSD. Requires a `vina`-capable Python environment (AutoDock Vina + Open Babel) -- see
    compute/docking/README.md. Never generates a novel ligand or receptor; both must be a
    real RCSB PDB entry.
    """
    sys.path.insert(0, str(_COMPUTE / "docking"))
    try:
        from docking_admission import InvalidIdentifierError, dock_reference_ligand
    except ImportError as exc:
        return {
            "verdict": "UNRESOLVED",
            "reason": (
                "docking_admission module could not be imported -- likely missing the "
                f"'vina' Python package or Open Babel in this environment ({exc})"
            ),
        }
    try:
        result = dock_reference_ligand(pdb_id=pdb_id, ligand_code=ligand_code, ligand_chain=ligand_chain)
    except InvalidIdentifierError as exc:
        return {"verdict": "UNRESOLVED", "reason": str(exc)}
    return result.to_dict()


if __name__ == "__main__":
    print(json.dumps(birca_math_consistency_check(), indent=2))
