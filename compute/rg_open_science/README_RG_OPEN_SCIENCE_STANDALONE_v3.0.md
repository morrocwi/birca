# RG Open-Science Drug–Food–Lane Standalone v3.0

This release consolidates the v2.0 compiler and adds an open-science tool registry,
global scientific data adapters, dependency profiles, cache/provenance contracts,
and end-to-end workflow DAGs.

## Main artifacts
- `RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml` — standalone specification
- `rg_open_science_runner.py` — offline-by-default planning and validation runner
- `requirements-rg-core.txt` — core profile
- `requirements-rg-chemistry.txt` — chemistry/structure-admission profile
- `requirements-rg-full.txt` — full profile
- `.env.example` — environment variable template

## Commands
```bash
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml validate
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml list-tools --kind remote
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml dependency-check --profile core
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml workflow-plan --workflow integrated_drug_food_lane_research
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml adapter-template --adapter RCSB_PDB
python rg_open_science_runner.py --yaml RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml requirements --profile full
```

## Network and safety boundary
Network execution is disabled by default. API keys are read only from environment
variables. The package does not generate novel molecules, ligand/receptor coordinates,
docking grids, synthesis routes, doses, or clinical recommendations.

## Dependency notes
RDKit, AutoDock Vina, Meeko and Open Babel can require platform-specific installation.
The requirements files are profiles, not a universal lock file.
