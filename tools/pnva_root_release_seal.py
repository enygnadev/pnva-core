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

ARTIFACTS = [
    {
        "id": "root_sovereignty_guard",
        "path": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "root_causal_intelligence",
        "path": "reports/pnva-root-causal-intelligence-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "root_traceability_matrix",
        "path": "reports/pnva-root-traceability-matrix-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "root_adversarial_sentry",
        "path": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
        "pass_path": ["pass"],
    },
    {
        "id": "sovereign_evolution_ledger",
        "path": "reports/pnva-sovereign-evolution-ledger-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "r3_cutover_gate",
        "path": "reports/pnva-r3-cutover-gate-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "R3_CUTOVER_APPROVED",
        "pass_path": ["pass"],
    },
    {
        "id": "runtime_evidence_guard",
        "path": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "R3_RUNTIME_EVIDENCE_ACCEPTED",
        "pass_path": ["pass"],
    },
    {
        "id": "semantic_consistency",
        "path": "reports/pnva-semantic-consistency-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "SEMANTIC_CONSISTENCY_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "reproducibility",
        "path": "reports/pnva-reproducibility-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "REPRODUCIBILITY_READY",
        "pass_path": ["pass"],
    },
    {
        "id": "evidence_attestation",
        "path": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
        "classification_path": ["classification"],
        "expected": "PNVA_SOVEREIGN_EVIDENCE_ATTESTED",
        "pass_path": ["pass"],
    },
    {
        "id": "sovereign_audit",
        "path": "reports/pnva-sovereign-audit-2026-05-05.json",
        "classification_path": ["score", "classification"],
        "expected": "SOVEREIGN_READY",
        "pass_path": ["score", "total"],
        "pass_value": 100,
    },
]


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_data(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _stable_data(item)
            for key, item in value.items()
            if key not in {"generated_at", "repo_path"}
        }
    if isinstance(value, list):
        return [_stable_data(item) for item in value]
    return value


def _stable_json_hash(data: Any) -> str:
    stable = _stable_data(data)
    return _sha_text(json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=True))


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _artifact(repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    rel = spec["path"]
    path = repo / rel
    item: dict[str, Any] = {
        "id": spec["id"],
        "path": rel,
        "present": path.exists(),
        "expected": spec["expected"],
    }
    if not path.exists():
        item["pass"] = False
        item["error"] = "missing"
        return item
    raw = path.read_bytes()
    data = _read_json(path)
    classification = _dig(data, spec["classification_path"])
    pass_value = _dig(data, spec["pass_path"], True)
    expected_pass = spec.get("pass_value", True)
    item.update(
        {
            "sha256": _sha_bytes(raw),
            "stable_sha256": _stable_json_hash(data),
            "size_bytes": len(raw),
            "classification": classification,
            "reported_pass": pass_value,
            "pass": classification == spec["expected"] and pass_value == expected_pass,
        }
    )
    if spec["id"] == "sovereign_audit":
        path_leaks = _dig(data, ["sovereignty", "path_leaks"], [])
        item["path_leak_count"] = len(path_leaks or [])
        item["pass"] = item["pass"] and not path_leaks
    return item


def build_report(repo: Path) -> dict[str, Any]:
    artifacts = [_artifact(repo, spec) for spec in ARTIFACTS]
    failures = [item for item in artifacts if not item.get("pass")]
    seed = [
        {
            "id": item["id"],
            "path": item["path"],
            "stable_sha256": item.get("stable_sha256", ""),
            "classification": item.get("classification", ""),
            "pass": item.get("pass", False),
        }
        for item in artifacts
    ]
    root_release_hash = "sha256:" + _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True))

    by_id = {item["id"]: item for item in artifacts}
    attestation = _read_json(repo / "reports/pnva-sovereign-evidence-attestation-2026-05-05.json")
    root_guard = _read_json(repo / "reports/pnva-root-sovereignty-guard-2026-05-05.json")
    causal = _read_json(repo / "reports/pnva-root-causal-intelligence-2026-05-05.json")
    sentry = _read_json(repo / "reports/pnva-root-adversarial-sentry-2026-05-05.json")
    ledger = _read_json(repo / "reports/pnva-sovereign-evolution-ledger-2026-05-05.json")
    guard = _read_json(repo / "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json")

    classification = "PNVA_ROOT_RELEASE_SEALED" if not failures else "PNVA_ROOT_RELEASE_SEAL_FAIL"
    return {
        "schema_version": "pnva.root_release_seal.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "root_release_hash": root_release_hash,
        "evidence_hash": attestation.get("evidence_hash"),
        "sealed_artifact_count": len(artifacts),
        "failure_count": len(failures),
        "artifacts": artifacts,
        "failures": failures,
        "release_vector": {
            "root_score": root_guard.get("root_score"),
            "root_causal_intelligence_score": causal.get("root_causal_intelligence_score"),
            "root_adversarial_detection_ratio": f"{sentry.get('detected_count')}/{sentry.get('test_count')}",
            "sovereign_evolution_score": ledger.get("sovereign_evolution_score"),
            "runtime_accepted_slots": guard.get("accepted_slot_count"),
            "runtime_pending_slots": guard.get("pending_slot_count"),
            "runtime_no_tick_pairs": guard.get("no_tick_pair_integrity_count"),
            "attestation_artifact_count": attestation.get("artifact_count"),
            "attestation_failure_count": attestation.get("failure_count"),
        },
        "claim_boundary": {
            "public_claim_allowed": classification == "PNVA_ROOT_RELEASE_SEALED",
            "allowed_claim": "The public PNVA-Core evidence package is root-sealed for the deterministic R3 runtime sample.",
            "not_claimed": [
                "universal performance improvement",
                "private deployment validation",
                "hardware-level energy gain without separate counters",
                "physical particle or physics proof",
            ],
        },
        "hash_policy": {
            "root_release_hash": "Hashes final root reports, attestation, semantic consistency, reproducibility, audit, cutover and runtime evidence guard classifications.",
            "not_in_attestation_seed": True,
            "not_self_referential": True,
            "manifest_and_checksums": "MANIFEST.json and SHA256SUMS.txt are updated after the seal and are not part of this seal hash.",
        },
        "interpretation": {
            "purpose": "Provide one citeable root release hash for the final PNVA public evidence package.",
            "sovereignty": "A release is stronger when its green path, causal intelligence, adversarial rejection, reproducibility, semantic agreement and publication hygiene are sealed together.",
            "boundary": "This seal protects the public evidence package; it does not replace independent replication on external deployments.",
        },
        "recommendations": [
            "Publish root_release_hash next to evidence_hash in release notes.",
            "Regenerate this seal after any root report, attestation, audit, semantic or reproducibility change.",
            "Keep this seal outside the attestation seed to avoid circular evidence hashing.",
        ],
        "artifact_index": {item["id"]: item.get("sha256") for item in artifacts},
        "artifact_status": {item["id"]: item.get("pass") for item in artifacts},
        "artifact_classifications": {item["id"]: item.get("classification") for item in artifacts},
        "artifact_sources": by_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seal the PNVA root release evidence package.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    raw = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
