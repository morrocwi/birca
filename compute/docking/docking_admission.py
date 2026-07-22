#!/usr/bin/env python3
"""
docking_admission.py — a thin, honest wrapper around a local AutoDock Vina install that
implements the "Molecular Docking Admission Bridge" contract described in
compute/rg_open_science/RG_OPEN_SCIENCE_DRUG_FOOD_LANE_STANDALONE_v3.0.yaml
(`docking_execution: ADMISSION_ONLY_UNTIL_EXTERNAL_STRUCTURES_PASS`).

WHAT THIS DOES: takes an externally-sourced PDB entry (a real, already-solved crystal
structure identified by its RCSB PDB ID) and an already-known co-crystallized ligand
(identified by its official 3-letter PDB chemical-component code), then re-docks that
ligand back into its own binding site as a validity check (RMSD vs. the ligand's real
crystallographic pose). This is ADMISSION of externally-verified structures, never
GENERATION of novel ones.

WHAT THIS DOES NOT DO (matches the forbidden_outputs list in both RG standalone specs and
in this repo's own SYSTEM_PROMPT.md/LEGAL_DISCLAIMER.md):
  - does NOT invent, design, or optimize any novel ligand or receptor structure
  - does NOT produce SMILES, synthesis routes, or manufacturing recipes
  - does NOT accept a ligand/receptor pair that was not sourced from a real external
    database entry (RCSB PDB) -- there is no "blind docking of a made-up molecule" path here
  - does NOT make or imply any clinical or dosing claim -- a PASS here means "the docking
    engine reproduces a known experimental result," nothing about efficacy in a person

CLAIM TIER: finite_diagnostic. A PASS/FAIL/UNRESOLVED verdict is a property of the docking
software's re-docking accuracy on a specific, real, externally-solved structure -- it is
NOT a claim about any drug's real-world safety or efficacy. readout-not-truth.

REQUIRES: a Python environment with the `vina` package (AutoDock Vina 1.2.x Python bindings)
and Open Babel's `obabel`/`obrms` command-line tools on PATH (see
compute/rg_open_science/requirements-rg-chemistry.txt). This session's reference
environment: `conda create -n vina -c conda-forge python=3.11 openbabel rdkit && pip
install vina meeko` inside that env.
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

RCSB_DOWNLOAD_URL = "https://files.rcsb.org/download/{pdb_id}.pdb"
RMSD_PASS_THRESHOLD_ANGSTROM = 2.0

# Real RCSB PDB entry IDs are exactly 4 characters: a digit followed by 3 alphanumerics
# (e.g. "1HVR", "4A9J"). PDB chemical-component (ligand) codes are 1-3 alphanumerics.
# Validating BOTH strictly, before either is used in a file path or URL, closes a path-
# traversal hole a code review found: an unvalidated pdb_id like "../../../etc/passwd"
# would otherwise land directly in a local file path (`workdir / f"{pdb_id.lower()}.pdb"`).
_PDB_ID_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")
_LIGAND_CODE_RE = re.compile(r"^[A-Za-z0-9]{1,3}$")
_CHAIN_RE = re.compile(r"^[A-Za-z0-9]{1,4}$")


class InvalidIdentifierError(ValueError):
    """Raised when pdb_id/ligand_code/chain fails the strict external-identifier format
    check -- never caused by a real RCSB PDB entry, only by malformed or malicious input."""


def _validate_identifiers(pdb_id: str, ligand_code: str, ligand_chain: str,
                           receptor_chains: "set[str] | None") -> None:
    if not _PDB_ID_RE.match(pdb_id):
        raise InvalidIdentifierError(
            f"pdb_id {pdb_id!r} is not a valid RCSB PDB entry ID (expected 4 characters: "
            "a digit followed by 3 alphanumerics, e.g. '1HVR')"
        )
    if not _LIGAND_CODE_RE.match(ligand_code):
        raise InvalidIdentifierError(
            f"ligand_code {ligand_code!r} is not a valid PDB chemical-component code "
            "(expected 1-3 alphanumeric characters, e.g. 'XK2')"
        )
    if not _CHAIN_RE.match(ligand_chain):
        raise InvalidIdentifierError(f"ligand_chain {ligand_chain!r} is not a valid chain ID")
    for c in (receptor_chains or ()):
        if not _CHAIN_RE.match(c):
            raise InvalidIdentifierError(f"receptor chain {c!r} is not a valid chain ID")


@dataclass
class DockingAdmissionResult:
    verdict: str  # PASS | FAIL | UNRESOLVED
    pdb_id: str
    ligand_code: str
    chain: str
    reason: str
    best_affinity_kcal_per_mol: float | None = None
    best_pose_rmsd_angstrom: float | None = None
    all_pose_rmsd_angstrom: list = field(default_factory=list)
    claim_tier: str = "finite_diagnostic"
    what_this_does_not_mean: str = (
        "This is a docking-software re-docking-accuracy check on a real, externally-"
        "solved structure. It is NOT a clinical, dosing, or efficacy claim, and it does "
        "NOT validate any novel molecule -- both ligand and receptor came from the named "
        "external PDB entry, not from generation."
    )

    def to_dict(self) -> dict:
        return asdict(self)


def _require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(
            f"docking_admission: required tool '{name}' not found on PATH -- install "
            "Open Babel (provides obabel/obrms) per requirements-rg-chemistry.txt"
        )


def _download_pdb(pdb_id: str, dest: Path) -> None:
    url = RCSB_DOWNLOAD_URL.format(pdb_id=pdb_id.upper())
    with urllib.request.urlopen(url, timeout=30) as resp:
        dest.write_bytes(resp.read())


def _extract_receptor_atoms(pdb_path: Path, chains: set[str] | None, out_path: Path) -> int:
    """Extract protein ATOM records for the receptor. `chains=None` means ALL protein
    chains -- the correct default for multi-chain biological assemblies (e.g. homodimers
    like HIV protease, 1HVR chains A+B) where the real binding pocket is formed by
    residues from more than one chain. Pass an explicit chain set only when the target
    pocket is genuinely confined to a subset of chains."""
    n = 0
    with pdb_path.open() as fin, out_path.open("w") as fout:
        for line in fin:
            if line.startswith("ATOM") and (chains is None or line[21] in chains):
                fout.write(line)
                n += 1
        fout.write("END\n")
    return n


def _extract_ligand(pdb_path: Path, ligand_code: str, chain: str, out_path: Path) -> int:
    n = 0
    with pdb_path.open() as fin, out_path.open("w") as fout:
        for line in fin:
            if line.startswith("HETATM") and line[17:20].strip() == ligand_code and line[21] == chain:
                fout.write(line)
                n += 1
    return n


def _ligand_centroid(ligand_pdb: Path) -> tuple[float, float, float]:
    xs, ys, zs = [], [], []
    for line in ligand_pdb.read_text().splitlines():
        if line.startswith("HETATM"):
            xs.append(float(line[30:38]))
            ys.append(float(line[38:46]))
            zs.append(float(line[46:54]))
    if not xs:
        raise RuntimeError("docking_admission: no ligand atoms found to compute a centroid")
    n = len(xs)
    return (sum(xs) / n, sum(ys) / n, sum(zs) / n)


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=True, **kw)


@contextlib.contextmanager
def _suppress_native_stdout():
    """The `vina` package's C++ extension writes its progress text (grid computation,
    docking progress bar, energy tables) directly to the OS-level file descriptor 1, not
    Python's `sys.stdout` object -- so `contextlib.redirect_stdout` alone does not catch
    it. When this module is called from an MCP server (stdio transport), that stray text
    corrupts the JSON-RPC message stream on the SAME file descriptor the protocol uses,
    which a real end-to-end MCP test caught (empagliflozin-vs-SGLT2 docking produced
    "Failed to parse JSONRPC message" errors even though the underlying docking result
    was still correct). Fix: dup2 fd 1 to /dev/null for the duration of the native calls,
    then restore the real stdout fd.

    A first version of this fix (dup2-only, no explicit flush) left a residual leak: the
    final "mode | affinity | ..." results table is written through a BUFFERED C stdio
    stream inside the Vina extension that is not flushed synchronously -- verified by
    instrumenting the actual code path, those bytes only reached the real fd at Python
    interpreter shutdown, AFTER dup2 had already restored fd 1. An independent review
    caught this. Fix: flush C's own stdio buffers via libc `fflush(NULL)` (flushes every
    open C stream, not just Python's, since `sys.stdout.flush()` alone cannot reach a
    buffer the Vina C++ extension wrote into directly) BEFORE restoring the real fd, so
    any buffered native output drains to /dev/null instead of leaking out later."""
    stdout_fd = sys.stdout.fileno()
    saved_fd = os.dup(stdout_fd)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    libc = ctypes.CDLL(None)
    try:
        os.dup2(devnull_fd, stdout_fd)
        yield
    finally:
        libc.fflush(None)  # drain any buffered native (C stdio) output while fd -> /dev/null
        os.dup2(saved_fd, stdout_fd)
        os.close(devnull_fd)
        os.close(saved_fd)


def dock_reference_ligand(
    pdb_id: str,
    ligand_code: str,
    ligand_chain: str = "A",
    receptor_chains: set[str] | None = None,
    box_size: float = 20.0,
    exhaustiveness: int = 8,
    n_poses: int = 9,
    workdir: Path | None = None,
) -> DockingAdmissionResult:
    """Re-dock a known co-crystallized ligand back into its own binding site and report
    whether the docking engine reproduces the real experimental pose (RMSD < 2 Angstrom).

    `pdb_id` must be a real RCSB PDB entry ID (e.g. "1HVR"); `ligand_code` must be that
    entry's own 3-letter PDB chemical-component code for an existing HETATM ligand
    (e.g. "XK2"), read from the specific `ligand_chain` copy (asymmetric units can contain
    several copies of the same ligand -- e.g. 4A9J has three TYL copies on chains A/B/C).
    `receptor_chains=None` (the default) uses ALL protein chains in the entry -- correct
    for multi-chain biological assemblies where the pocket spans more than one chain (e.g.
    1HVR's HIV-protease homodimer, chains A+B); pass an explicit set only when the pocket
    is confirmed to sit within a chain subset. Nothing here is generated -- both receptor
    and ligand come from the named external record.
    """
    _validate_identifiers(pdb_id, ligand_code, ligand_chain, receptor_chains)

    try:
        _require_tool("obabel")
        _require_tool("obrms")
        from vina import Vina
    except ImportError as exc:
        return DockingAdmissionResult(
            verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
            reason=(
                "the 'vina' Python package is not installed in this environment -- see "
                "compute/rg_open_science/requirements-rg-chemistry.txt"
            ),
        )
    except RuntimeError as exc:
        return DockingAdmissionResult(
            verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
            reason=str(exc),
        )

    own_tmp = workdir is None
    workdir = workdir or Path(tempfile.mkdtemp(prefix="birca_docking_"))
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        raw_pdb = workdir / f"{pdb_id.lower()}.pdb"
        try:
            _download_pdb(pdb_id, raw_pdb)
        except (urllib.error.URLError, OSError) as exc:
            return DockingAdmissionResult(
                verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
                reason=f"could not download {pdb_id} from RCSB: {exc}",
            )

        receptor_pdb = workdir / "receptor_only.pdb"
        n_receptor_atoms = _extract_receptor_atoms(raw_pdb, receptor_chains, receptor_pdb)
        if n_receptor_atoms == 0:
            chains_desc = "all chains" if receptor_chains is None else str(receptor_chains)
            return DockingAdmissionResult(
                verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
                reason=f"no ATOM records found for {chains_desc} in {pdb_id} -- check the chain ID(s)",
            )

        ligand_ref_pdb = workdir / "ligand_ref.pdb"
        n_ligand_atoms = _extract_ligand(raw_pdb, ligand_code, ligand_chain, ligand_ref_pdb)
        if n_ligand_atoms == 0:
            return DockingAdmissionResult(
                verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
                reason=(
                    f"no HETATM records for ligand code '{ligand_code}' on chain '{ligand_chain}' "
                    f"in {pdb_id} -- confirm the ligand code and chain against the RCSB entry"
                ),
            )

        try:
            receptor_pdbqt = workdir / "receptor.pdbqt"
            _run(["obabel", str(receptor_pdb), "-O", str(receptor_pdbqt), "-xr",
                  "--partialcharge", "gasteiger"])

            ligand_pdbqt = workdir / "ligand_ref.pdbqt"
            _run(["obabel", str(ligand_ref_pdb), "-O", str(ligand_pdbqt),
                  "--partialcharge", "gasteiger"])

            ligand_sdf = workdir / "ligand_ref.sdf"
            _run(["obabel", str(ligand_ref_pdb), "-O", str(ligand_sdf)])

            cx, cy, cz = _ligand_centroid(ligand_ref_pdb)

            with _suppress_native_stdout():
                v = Vina(sf_name="vina")
                v.set_receptor(str(receptor_pdbqt))
                v.set_ligand_from_file(str(ligand_pdbqt))
                v.compute_vina_maps(center=[cx, cy, cz], box_size=[box_size, box_size, box_size])
                v.dock(exhaustiveness=exhaustiveness, n_poses=n_poses)

                docked_out = workdir / "docked_out.pdbqt"
                v.write_poses(str(docked_out), n_poses=n_poses, overwrite=True)
                energies = v.energies(n_poses=n_poses)
            best_affinity = float(energies[0][0])

            # Vina's write_poses() can write FEWER models than n_poses requested (it only
            # writes distinct poses it actually found) -- count real MODEL blocks rather
            # than trusting n_poses, or obabel/obrms silently fail past the last real model.
            n_written = sum(
                1 for ln in docked_out.read_text().splitlines() if ln.startswith("MODEL")
            )
            if n_written == 0:
                return DockingAdmissionResult(
                    verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
                    reason="Vina wrote zero pose models -- docking likely failed silently",
                )

            rmsds: list[float] = []
            for i in range(1, n_written + 1):
                pose_pdb = workdir / f"pose_{i}.pdb"
                _run(["obabel", str(docked_out), "-O", str(pose_pdb), "-f", str(i), "-l", str(i)])
                out = _run(["obrms", str(ligand_sdf), str(pose_pdb)]).stdout.strip()
                # obrms prints: "RMSD ref:test <value>"
                rmsds.append(float(out.split()[-1]))
        except subprocess.CalledProcessError as exc:
            return DockingAdmissionResult(
                verdict="UNRESOLVED", pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
                reason=(
                    f"a docking-pipeline subprocess failed ({exc.cmd[0]}, exit "
                    f"{exc.returncode}): {(exc.stderr or '').strip()[:300]}"
                ),
            )

        best_rmsd = min(rmsds)
        verdict = "PASS" if best_rmsd < RMSD_PASS_THRESHOLD_ANGSTROM else "FAIL"
        reason = (
            f"best re-docked pose RMSD {best_rmsd:.2f} A "
            f"({'<' if verdict == 'PASS' else '>='} {RMSD_PASS_THRESHOLD_ANGSTROM} A threshold) "
            f"across {n_written} poses"
        )
        return DockingAdmissionResult(
            verdict=verdict, pdb_id=pdb_id, ligand_code=ligand_code, chain=ligand_chain,
            reason=reason, best_affinity_kcal_per_mol=best_affinity,
            best_pose_rmsd_angstrom=best_rmsd, all_pose_rmsd_angstrom=rmsds,
        )
    finally:
        if own_tmp:
            shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdb-id", required=True, help="RCSB PDB entry ID, e.g. 1HVR")
    parser.add_argument("--ligand-code", required=True, help="3-letter PDB ligand code, e.g. XK2")
    parser.add_argument("--ligand-chain", default="A",
                         help="chain the specific ligand copy to re-dock sits on (default: A)")
    parser.add_argument("--receptor-chains", default=None,
                         help="comma-separated chain IDs to include in the receptor "
                              "(default: ALL protein chains -- correct for multi-chain "
                              "assemblies like homodimers)")
    parser.add_argument("--box-size", type=float, default=20.0)
    parser.add_argument("--exhaustiveness", type=int, default=8)
    parser.add_argument("--n-poses", type=int, default=9)
    parser.add_argument("--keep-workdir", action="store_true",
                         help="don't delete the temp working directory (for inspection)")
    args = parser.parse_args(argv)

    receptor_chains = set(args.receptor_chains.split(",")) if args.receptor_chains else None
    workdir = Path(tempfile.mkdtemp(prefix="birca_docking_")) if args.keep_workdir else None
    try:
        result = dock_reference_ligand(
            pdb_id=args.pdb_id, ligand_code=args.ligand_code, ligand_chain=args.ligand_chain,
            receptor_chains=receptor_chains,
            box_size=args.box_size, exhaustiveness=args.exhaustiveness, n_poses=args.n_poses,
            workdir=workdir,
        )
    except InvalidIdentifierError as exc:
        print(json.dumps({"verdict": "UNRESOLVED", "reason": str(exc)}, indent=2))
        return 1
    print(json.dumps(result.to_dict(), indent=2))
    if args.keep_workdir:
        print(f"# workdir kept at: {workdir}", file=sys.stderr)
    return 0 if result.verdict != "UNRESOLVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
