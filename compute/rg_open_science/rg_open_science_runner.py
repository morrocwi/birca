#!/usr/bin/env python3
"""RG Open-Science Standalone runner v3.0.

This runner validates and plans workflows. Network calls and molecular generation
are disabled by default. It does not create molecules, structures, docking grids,
synthesis routes, doses, or clinical recommendations.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

import yaml


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(doc: dict) -> dict:
    required = [
        "root_mathematical_contract",
        "runtime_pipeline",
        "tool_registry",
        "dependency_profiles",
        "adapter_contract",
        "workflow_dags",
        "open_science_governance",
    ]
    missing = [k for k in required if k not in doc]
    return {
        "status": "PASS" if not missing else "FAIL",
        "missing": missing,
        "version": doc.get("document", {}).get("version"),
        "network_default": doc.get("document", {}).get("network_execution_default"),
        "molecular_generation": doc.get("document", {}).get("molecular_generation"),
    }


def dependency_check(doc: dict, profile: str) -> dict:
    registry = doc["tool_registry"]["local_libraries"]
    statuses = []
    selected = {"core"}
    if profile == "chemistry":
        selected.add("chemistry")
    elif profile == "full":
        selected.update({"chemistry", "full"})

    for name, card in registry.items():
        if card.get("profile") not in selected:
            continue
        import_name = card.get("python_import")
        if import_name:
            found = importlib.util.find_spec(import_name) is not None
            statuses.append({"tool": name, "import": import_name, "installed": found})
        else:
            statuses.append({
                "tool": name,
                "installed": None,
                "note": "system or command dependency; check separately",
            })
    return {"profile": profile, "dependencies": statuses}


def list_tools(doc: dict, kind: str) -> dict:
    return {
        "kind": kind,
        "tools": doc["tool_registry"]["local_libraries" if kind == "local" else "remote_sources"],
    }


def workflow_plan(doc: dict, workflow: str) -> dict:
    dags = doc["workflow_dags"]
    if workflow not in dags:
        raise KeyError(f"Unknown workflow: {workflow}")
    return {
        "workflow": workflow,
        "plan": dags[workflow],
        "network_execution": "DISABLED_BY_DEFAULT",
        "claim_boundary": (
            "Plans and systems-level hypotheses only; no novel molecule, synthesis, dose, "
            "or therapeutic substitution."
        ),
    }


def adapter_template(doc: dict, adapter: str) -> dict:
    sources = doc["tool_registry"]["remote_sources"]
    if adapter not in sources:
        raise KeyError(f"Unknown adapter: {adapter}")
    return {
        "adapter": adapter,
        "source_card": sources[adapter],
        "request_contract": doc["adapter_contract"],
        "runtime_values": {
            "query_or_resource_id": "POPULATE",
            "retrieval_time_utc": "POPULATE",
            "accepted_license_status": "POPULATE",
            "cache_root": "POPULATE",
            "network_enabled": False,
        },
    }


def requirements(doc: dict, profile: str) -> dict:
    card = doc["dependency_profiles"][profile]
    return {
        "profile": profile,
        "packages": card.get("packages", []),
        "system_packages_optional": card.get("system_packages_optional", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yaml", required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    p_dep = sub.add_parser("dependency-check")
    p_dep.add_argument("--profile", choices=["core", "chemistry", "full"], default="core")

    p_tools = sub.add_parser("list-tools")
    p_tools.add_argument("--kind", choices=["local", "remote"], default="local")

    p_wf = sub.add_parser("workflow-plan")
    p_wf.add_argument("--workflow", required=True)

    p_ad = sub.add_parser("adapter-template")
    p_ad.add_argument("--adapter", required=True)

    p_req = sub.add_parser("requirements")
    p_req.add_argument("--profile", choices=["core", "chemistry", "full"], default="core")

    args = parser.parse_args()
    doc = load(Path(args.yaml))

    if args.command == "validate":
        result = validate(doc)
    elif args.command == "dependency-check":
        result = dependency_check(doc, args.profile)
    elif args.command == "list-tools":
        result = list_tools(doc, args.kind)
    elif args.command == "workflow-plan":
        result = workflow_plan(doc, args.workflow)
    elif args.command == "adapter-template":
        result = adapter_template(doc, args.adapter)
    else:
        result = requirements(doc, args.profile)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
