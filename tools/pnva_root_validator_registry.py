#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"
CHECKSUMS = "SHA256SUMS.txt"
WORKFLOW = ".github/workflows/validate.yml"
README = "README.md"
LLMS = "llms.txt"
SOVEREIGN_DOC = "docs/PNVA_SOVEREIGN_LOGS_ENTITIES_HEURISTICS.md"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _load_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    if not path.exists():
        return checksums
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            checksums[parts[1].strip()] = parts[0].strip()
    return checksums


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _root_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for name, value in manifest.get("summary", {}).items():
        if not isinstance(value, dict) or not name.startswith("root_"):
            continue
        if not {"tool", "doc", "report", "classification"}.issubset(value):
            continue
        entries[name] = value
    return entries


def build_report(repo: Path) -> dict[str, Any]:
    manifest = _read_json(repo / "MANIFEST.json")
    manifest_files = set(str(item) for item in manifest.get("files", []) if isinstance(item, str))
    checksums = _load_checksums(repo / CHECKSUMS)
    workflow = _text(repo / WORKFLOW) if (repo / WORKFLOW).exists() else ""
    readme = _text(repo / README) if (repo / README).exists() else ""
    llms = _text(repo / LLMS) if (repo / LLMS).exists() else ""
    sovereign_doc = _text(repo / SOVEREIGN_DOC) if (repo / SOVEREIGN_DOC).exists() else ""

    entries = _root_entries(manifest)
    rows = []
    missing_files = []
    missing_manifest_refs = []
    missing_checksums = []
    classification_failures = []
    workflow_missing = []
    readme_missing = []
    llms_missing = []
    sovereign_doc_missing = []
    root_hash_mismatches = []

    for name, entry in sorted(entries.items()):
        tool = str(entry.get("tool", ""))
        doc = str(entry.get("doc", ""))
        report = str(entry.get("report", ""))
        expected_classification = str(entry.get("classification", ""))
        paths = {"tool": tool, "doc": doc, "report": report}

        file_status = {kind: bool(path and (repo / path).exists()) for kind, path in paths.items()}
        manifest_status = {kind: path in manifest_files for kind, path in paths.items()}
        checksum_status = {kind: path in checksums for kind, path in paths.items()}
        if not all(file_status.values()):
            missing_files.append({"name": name, "paths": {kind: path for kind, path in paths.items() if not file_status[kind]}})
        if not all(manifest_status.values()):
            missing_manifest_refs.append({"name": name, "paths": {kind: path for kind, path in paths.items() if not manifest_status[kind]}})
        if not all(checksum_status.values()):
            missing_checksums.append({"name": name, "paths": {kind: path for kind, path in paths.items() if not checksum_status[kind]}})

        report_data = _read_json(repo / report) if file_status["report"] else {}
        is_self = name == "root_validator_registry"
        classification_ok = (
            True
            if is_self
            else report_data.get("classification") == expected_classification and report_data.get("pass") is True
        )
        if not classification_ok:
            classification_failures.append(
                {
                    "name": name,
                    "expected": expected_classification,
                    "actual": report_data.get("classification"),
                    "pass": report_data.get("pass"),
                }
            )
        root_hash = report_data.get("root_release_hash")
        if root_hash and root_hash != ROOT_RELEASE_HASH:
            root_hash_mismatches.append({"name": name, "root_release_hash": root_hash})

        if tool and tool not in workflow:
            workflow_missing.append({"name": name, "tool": tool})
        if doc and Path(doc).name not in readme:
            readme_missing.append({"name": name, "doc": doc})
        if doc and doc not in llms:
            llms_missing.append({"name": name, "doc": doc})
        if expected_classification and expected_classification not in sovereign_doc:
            sovereign_doc_missing.append({"name": name, "classification": expected_classification})

        rows.append(
            {
                "name": name,
                "tool": tool,
                "doc": doc,
                "report": report,
                "classification": expected_classification,
                "file_complete": all(file_status.values()),
                "manifest_complete": all(manifest_status.values()),
                "checksum_complete": all(checksum_status.values()),
                "workflow_registered": tool in workflow if tool else False,
                "readme_registered": Path(doc).name in readme if doc else False,
                "llms_registered": doc in llms if doc else False,
                "sovereign_doc_registered": expected_classification in sovereign_doc if expected_classification else False,
                "report_pass": classification_ok,
            }
        )

    checks = [
        _check("root_validator_entries_present", len(entries) >= 25, {"registry_count": len(entries), "minimum": 25}),
        _check("root_validator_files_exist", not missing_files, {"missing_files": missing_files}),
        _check("root_validator_manifest_refs_complete", not missing_manifest_refs, {"missing_manifest_refs": missing_manifest_refs}),
        _check("root_validator_checksums_complete", not missing_checksums, {"missing_checksums": missing_checksums}),
        _check("root_validator_reports_pass", not classification_failures, {"classification_failures": classification_failures}),
        _check("root_validator_workflow_registered", not workflow_missing, {"workflow_missing": workflow_missing}),
        _check("root_validator_public_docs_registered", not readme_missing and not llms_missing and not sovereign_doc_missing, {"readme_missing": readme_missing, "llms_missing": llms_missing, "sovereign_doc_missing": sovereign_doc_missing}),
        _check("root_validator_hashes_aligned", not root_hash_mismatches, {"root_hash_mismatches": root_hash_mismatches, "expected": ROOT_RELEASE_HASH}),
    ]

    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_VALIDATOR_REGISTRY_READY" if not failures else "PNVA_ROOT_VALIDATOR_REGISTRY_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "registry_count": len(entries),
        "root_release_hash": ROOT_RELEASE_HASH,
        "rows": [
            {
                "name": row["name"],
                "tool": row["tool"],
                "doc": row["doc"],
                "report": row["report"],
                "classification": row["classification"],
            }
            for row in rows
        ],
    }

    return {
        "schema_version": "pnva.root_validator_registry.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "registry_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "registry_count": len(entries),
        "manifest_file_count": len(manifest_files),
        "checksum_count": len(checksums),
        "workflow_registered_count": sum(1 for row in rows if row["workflow_registered"]),
        "public_doc_registered_count": sum(1 for row in rows if row["readme_registered"] and row["llms_registered"] and row["sovereign_doc_registered"]),
        "report_pass_count": sum(1 for row in rows if row["report_pass"]),
        "root_release_hash": ROOT_RELEASE_HASH,
        "validator_registry_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "rows": rows,
        "interpretation": {
            "purpose": "Prove that every root PNVA validator is registered across tool, report, document, Manifest, checksum, CI and public documentation.",
            "sovereignty": "A root proof system is stronger when validators are discoverable and cannot silently disappear from the release surface.",
            "boundary": "This registry audits public repository structure only. It does not execute actions, change live gates or alter runtime workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root validator registry.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--write", help="Optional report path.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
