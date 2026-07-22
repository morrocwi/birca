"""
birca_evidence_bridge.py — a thin adapter onto the vendored RG_QOR_v0.5.0_STANDALONE
evidence-quotient/claim-citation runtime (`compute/rg_qor/`), used to give birca a
code-level (not model-asserted) check that a claim's cited evidence actually supports it.

Two capabilities, both genuinely runnable and tested, deliberately scoped narrow:

  1. `run_qor_selftest()` -- an environment/health check: runs the vendored standalone's
     own `selftest` subcommand and reports pass/fail. Use this to confirm the vendored QOR
     runtime still works after any change to `compute/rg_qor/`.

  2. `check_claim_citations(claims, evidence)` -- the actual citation-validation primitive:
     given a list of claims (fact_key/value/citations) and a list of evidence items
     (evidence_id/fact_key/value), runs QOR's own `ClaimCitationChecker` and returns any
     defects (CLAIM_WITHOUT_CITATION, CITATION_OUTSIDE_EVIDENCE_QUOTIENT,
     CLAIM_VALUE_NOT_SUPPORTED_BY_CITATION, REQUIRED_FACT_NOT_CLAIMED).

NOT IMPLEMENTED (future work, do not claim otherwise): full TaskCard-driven retrieval
(`EvidenceRetriever`/`StandaloneRuntime`), tenant/permission-scoped evidence stores, and
the cache/audit envelope. Those require a real evidence corpus and task-card contract this
integration has not been given -- wiring them in without that would be exactly the kind of
overclaim this whole ecosystem's "readout, not truth" discipline forbids. What's here is
the citation-consistency CHECK only, which is genuinely useful and fully testable on its
own.

claim tier: `EXACT_WITHIN_STANDALONE_REFERENCE_IMPLEMENTATION` (QOR's own tier for this
mechanism) -- not "production_proven" or "universally_safe" (both explicitly forbidden
claims in compute/rg_qor/RG_QOR_v0.5.0_STANDALONE.yaml).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

_HERE = Path(__file__).resolve().parent
_QOR_DIR = _HERE.parent / "compute" / "rg_qor"
_QOR_SCRIPT = _QOR_DIR / "RG_QOR_v0.5.0_STANDALONE.py"

sys.path.insert(0, str(_QOR_DIR))


def run_qor_selftest() -> dict:
    """Run the vendored QOR standalone's own `selftest` subcommand as an environment
    health-check. Standard-library-only, no network, no external dependencies."""
    proc = subprocess.run(
        [sys.executable, str(_QOR_SCRIPT), "selftest"],
        capture_output=True, text=True, cwd=str(_QOR_DIR),
    )
    return {
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": "\n".join(proc.stdout.strip().splitlines()[-15:]),
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-15:]) if proc.stderr else "",
    }


def check_claim_citations(
    claims: Sequence[dict[str, Any]],
    evidence: Sequence[dict[str, Any]],
) -> dict:
    """Validate that each claim's cited evidence_id actually exists and its value matches.

    `claims`: list of {"claim_id", "fact_key", "value", "citations": [evidence_id, ...]}
    `evidence`: list of {"evidence_id", "fact_key", "value"} -- minimal fields; other
    EvidenceItem fields (trust_tier, source_id, effective_from, ...) are filled with inert
    defaults since this check only exercises citation/value matching, not trust ranking or
    time-effectivity (that's the full retriever's job, not implemented here -- see module
    docstring).

    Returns {"passed": bool, "defects": [...]} where an empty defects list means every
    claim is fully citation-supported.
    """
    import importlib.util

    module_name = "rg_qor_standalone"
    if module_name in sys.modules:
        mod = sys.modules[module_name]
    else:
        spec = importlib.util.spec_from_file_location(module_name, _QOR_SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        # dataclasses' own introspection looks up cls.__module__ in sys.modules, so the
        # module must be registered there BEFORE exec_module runs its dataclass decorators,
        # or it fails with "NoneType has no attribute '__dict__'".
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]

    evidence_items = tuple(
        mod.EvidenceItem(
            evidence_id=e["evidence_id"],
            fact_key=e["fact_key"],
            value=e["value"],
            content=e.get("content", ""),
            source_id=e.get("source_id", "unspecified"),
            source_version=e.get("source_version", "1"),
            revision=e.get("revision", 0),
            effective_from=e.get("effective_from", "2020-01-01T00:00:00Z"),
            effective_until=e.get("effective_until"),
            trust_tier=e.get("trust_tier", "primary"),
        )
        for e in evidence
    )
    claim_objs = tuple(
        mod.Claim(
            claim_id=c["claim_id"], fact_key=c["fact_key"], value=c["value"],
            citations=tuple(c.get("citations", [])),
        )
        for c in claims
    )
    quotient = mod.EvidenceQuotient(
        query="birca_evidence_bridge.check_claim_citations",
        status=mod.GateStatus.ADMITTED,
        selected=evidence_items,
        missing_fact_keys=(),
        conflicts={},
        defects=(),
        snapshot_hash=mod.canonical_hash([e.to_dict() for e in evidence_items]),
        candidate_count=len(evidence_items),
        filtered_count=len(evidence_items),
        quarantined_evidence_ids=(),
    )
    checker = mod.ClaimCitationChecker()
    defects = checker.check(claim_objs, quotient)
    return {
        "passed": len(defects) == 0,
        "defects": [d.to_dict() for d in defects],
        "claim_tier": "EXACT_WITHIN_STANDALONE_REFERENCE_IMPLEMENTATION",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_qor_selftest(), indent=2))
