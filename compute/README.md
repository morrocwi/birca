# `compute/` — birca's compute layer (new in v5.0.0)

birca's chat layer (`SYSTEM_PROMPT.md`, `spec/`) is unchanged in mechanism since v1.x — a
pure, safety-gated conversational skill. `compute/` adds a SEPARATE, additive layer of
real, independently-runnable research tools, wired in as four new MCP tools
(`mcp_server/server.py`) that a tool-calling host can invoke when a Layer 2/3 turn
genuinely needs computation instead of prose. **None of this is mandatory, and none of it
replaces the chat layer's own safety gates** (Layers 0/0b/1/2/3, the depth gate, the
out-of-scope-decline rule) — see `SYSTEM_PROMPT.md`'s own v5.0.0 note.

## What's here

| Directory | What it is | Vendored from | Verified (this integration) |
|---|---|---|---|
| `birca_math/` | The BIRCA repair-equation fixes + 17-model health atlas, re-derived on a canonical spine, fixing 3 concrete faults in the source monograph's literal equations | `research_universal_solver` PRs #7 (Python) and #8 (7 Coq files, kept upstream) | `birca_repair.py` 6/6 PASS, `health_atlas.py` 17/17 PASS (real scipy integration) |
| `rg_qor/` | RG_QOR v0.5.0 — an offline, standard-library-only evidence-quotient/claim-citation-validation runtime | `morrocwi/readout_genesis`, pinned commit `f7aa4ca3cf6a81172bbd2f2c9a3ae92f3ecd075f` | `selftest`: 14/14 PASS |
| `rg_open_science/` | RG Open-Science Drug-Food-Lane v3.0 — a research-only drug/food/disease lane compiler with a molecular-docking admission bridge, tool registry, and data-adapter contracts (network disabled by default) | `readout_genesis` family, supersedes an earlier v2.0 package (confirmed by structural diff — v2.0 is fully contained in v3.0) | `validate`, `list-tools`, `dependency-check`, `workflow-plan`, `adapter-template` all run successfully |
| `docking/` | A thin wrapper around a local AutoDock Vina install implementing `rg_open_science`'s `docking_execution: ADMISSION_ONLY` contract — re-docks an externally-sourced, already-known ligand into its own crystal binding site as a docking-software accuracy check | New for this integration (not vendored — written against this session's proven Vina pipeline) | 1HVR+XK2: PASS (RMSD 0.58 Å); 4A9J+TYL (paracetamol): FAIL (RMSD 2.26 Å, correctly — see `docking/README.md`) |

## What none of this does

Every piece here inherits the same forbidden-outputs discipline as the RG packages it's
built from: no novel-molecule generation, no SMILES/synthesis routes, no dosing or
clinical recommendations, no docking-ready coordinates fabricated from nothing. Every
input (a PDB structure, a citation's evidence item) must be externally sourced and named
explicitly — nothing here invents anything.

## Claim tiers

Each subdirectory carries its own explicit claim tier in its own README/PROVENANCE —
`finite_diagnostic` (math/atlas/docking), `EXACT_WITHIN_STANDALONE_REFERENCE_IMPLEMENTATION`
(QOR). None of these is a clinical or empirical validation claim. See
`spec/birca_universal_skill.yaml` → `dynamic_graph_boundary` for how the chat layer frames
this distinction to an end user.

## Installing the compute layer

The chat layer needs nothing extra. To use the compute-layer MCP tools:

```bash
conda create -n birca-compute -c conda-forge python=3.11 openbabel rdkit
conda activate birca-compute
pip install vina meeko scipy sympy
pip install -r compute/rg_open_science/requirements-rg-core.txt
pip install -r mcp_server/requirements.txt   # mcp>=1.28.0
python3 mcp_server/server.py
```

Each subdirectory's own README documents its exact requirements; `birca_math_consistency_check`
needs only numpy/scipy/sympy/networkx, `birca_evidence_quotient_check` needs nothing beyond
the standard library, `birca_drug_food_lane_plan` needs `rg_open_science`'s core profile,
and `birca_docking_admission` needs the full chemistry profile (vina/openbabel/rdkit/meeko).

## Keeping in sync

`birca_math/` is a vendored, unmodified copy — see `birca_math/PROVENANCE.md` for how to
re-sync it if the upstream `research_universal_solver` modules change. `rg_qor/` and
`rg_open_science/` are vendored standalone release packages — re-vendor from a newer
release rather than hand-editing them in place.
