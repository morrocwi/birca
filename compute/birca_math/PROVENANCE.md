# Provenance — `compute/birca_math/`

`birca_repair.py` and `health_atlas.py` are vendored, unmodified copies of the Python solver
modules from `morrocwi/research_universal_solver`, `src/anse_spine/solvers/`, as merged in
[PR #7](https://github.com/morrocwi/research_universal_solver/pull/7) ("solvers: BIRCA
repair-equation fixes + 17-model health atlas (with overclaim correction)").

The same equations are additionally formalized as 7 discrete, axiom-free Coq files
(`InfoHealthCuspFold`, `InfoHealthCausalRelax`, `InfoBioHomeostasis`, `InfoEpidemicThreshold`,
`InfoCoupledCuspEP3`, `InfoEP3Directionality`, `InfoEP3LagGranger`) in
[PR #8](https://github.com/morrocwi/research_universal_solver/pull/8) of that same repo.
**The Coq proofs are not vendored here** — they stay in `research_universal_solver` under its
own CI (`make verify-attempts`), which is the authoritative place to re-check `Th_coqc`
status. This directory only carries the derived, independently-runnable Python.

## What these two files verify (by running, not by assertion)

- `birca_repair.py` — 6/6 PASS: fixes 3 concrete faults in the *Wellbeing from Informationism*
  (BIRCA v4.5) monograph's literal Eq(2)/Eq(4)/Eq(3-7) (dimensional inconsistency, unbounded
  causal-safety term, a repair state with no restoring term so it cannot show bistability).
  Verified by real `scipy` numerical integration.
- `health_atlas.py` — 17/17 PASS: 17 standard textbook health-domain models (epidemiology,
  PK/PD, oncology, homeostasis, chronic/aging/repair), each checked against its own known
  qualitative behavior.

**Claim tier: `finite_diagnostic` / `Dr` (readout-not-truth).** This is mathematical
internal-consistency and textbook-reproduction verification only — **NOT clinical or
empirical validation**, does not diagnose or predict any individual's physiology, and does
not change BIRCA's own claim tier or eligibility gates (see `spec/birca_universal_skill.yaml`
→ `dynamic_graph_boundary.mathematical_consistency_finding`).

## Running the self-tests locally

Both files are standalone scripts with a `__main__` self-test:

```bash
pip install numpy scipy sympy networkx
python3 compute/birca_math/birca_repair.py
python3 compute/birca_math/health_atlas.py
```

Both exit `0` on full pass, non-zero otherwise.

## Keeping this in sync

If `research_universal_solver`'s `birca_repair.py`/`health_atlas.py` changes, re-vendor from
there — do not hand-edit the copies here without also updating upstream, or the two will
silently drift and this directory's provenance claim becomes false.
