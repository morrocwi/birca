# `compute/docking/` — Molecular Docking Admission Bridge

Implements the `docking_execution: ADMISSION_ONLY_UNTIL_EXTERNAL_STRUCTURES_PASS` contract
declared in `compute/rg_open_science/RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml`.

## What it does

`docking_admission.py` re-docks an already-known, externally-solved ligand back into its
own crystallographic binding site (using a real RCSB PDB entry) and reports whether
[AutoDock Vina](https://vina.scripps.edu/) reproduces the real experimental pose
(RMSD < 2 Å = `PASS`). This is a **docking-software accuracy check**, not drug discovery —
it never invents a ligand, receptor, or binding site; every atom comes from the named
external PDB record.

## Requirements

```bash
conda create -n vina -c conda-forge python=3.11 openbabel rdkit
conda activate vina
pip install vina meeko scipy sympy
pip install -r ../rg_open_science/requirements-rg-core.txt
```

(See `../rg_open_science/requirements-rg-chemistry.txt` for the platform-specific chemistry
stack this repo's `RG_OPEN_SCIENCE` package expects — `vina`, `meeko`, `rdkit`, `biopython`,
`MDAnalysis`.)

## Usage

```bash
python3 docking_admission.py --pdb-id 1HVR --ligand-code XK2 --ligand-chain A
```

Options:
- `--receptor-chains A,B` — restrict the receptor to specific chains (default: **all**
  protein chains in the entry — required for multi-chain assemblies like homodimers,
  e.g. HIV protease/1HVR, where the pocket spans more than one chain)
- `--box-size`, `--exhaustiveness`, `--n-poses` — passed through to Vina
- `--keep-workdir` — don't delete the temp working directory (useful for inspection)

## Verified test cases (run this session)

| PDB ID | Ligand | Verdict | Best RMSD | Note |
|---|---|---|---|---|
| `1HVR` | `XK2` (HIV protease inhibitor) | **PASS** | 0.58 Å | designed high-affinity inhibitor, deep well-defined pocket |
| `4A9J` | `TYL` (paracetamol/acetaminophen) | **FAIL** | 2.26 Å | BRD2 bromodomain is not paracetamol's real pharmacological target; weak/shallow binding, multiple near-degenerate poses |

A `FAIL` here is not a bug report — it is the honest, correct answer for a ligand-target
pair that either isn't a real binding relationship or sits in a large/flexible pocket where
default-settings docking cannot reliably reproduce the crystal pose. See the tool's own
`what_this_does_not_mean` field on every result.

## Claim tier

`finite_diagnostic` — readout-not-truth. A result here says something about the docking
software's accuracy on one real, externally-solved structure. It is not a clinical claim,
not a novel-molecule claim, and not evidence of any drug's real-world safety or efficacy.
