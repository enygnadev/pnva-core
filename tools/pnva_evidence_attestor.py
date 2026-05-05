#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


EXPECTED_ARTIFACTS = [
    {
        "id": "proof_index",
        "path": "proofs/sanitized/INDEX.json",
        "kind": "proof_index",
        "required": True,
    },
    {
        "id": "canonical_bridge",
        "path": "reports/pnva-canonical-bridge-summary-2026-05-05.json",
        "kind": "bridge_summary",
        "required": True,
    },
    {
        "id": "canonical_events",
        "path": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
        "kind": "jsonl",
        "required": True,
    },
    {
        "id": "canonical_entities",
        "path": "reports/pnva-entity-catalog-2026-05-05.json",
        "kind": "entity_catalog",
        "required": True,
    },
    {
        "id": "canonical_replay",
        "path": "reports/pnva-replay-validation-2026-05-05.json",
        "kind": "json_classification",
        "expected": "REPLAY_VALID",
        "required": True,
    },
    {
        "id": "canonical_no_tick",
        "path": "reports/pnva-no-tick-invariants-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SOVEREIGN_NO_TICK_READY",
        "required": True,
    },
    {
        "id": "canonical_policy",
        "path": "reports/pnva-sovereign-policy-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "canonical_proof_chain",
        "path": "reports/pnva-proof-chain-2026-05-05.json",
        "kind": "json_classification",
        "expected": "PROOF_CHAIN_SEALED",
        "required": True,
    },
    {
        "id": "canonical_causal_graph",
        "path": "reports/pnva-causal-graph-2026-05-05.json",
        "kind": "json_classification",
        "expected": "CAUSAL_GRAPH_READY",
        "required": True,
    },
    {
        "id": "schema_contract_validation",
        "path": "reports/pnva-schema-contract-validation-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "causal_chronology",
        "path": "reports/pnva-causal-chronology-2026-05-05.json",
        "kind": "json_classification",
        "expected": "CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "tension_decision_calibration",
        "path": "reports/pnva-tension-decision-calibration-2026-05-05.json",
        "kind": "json_classification",
        "expected": "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "entity_no_tick_matrix",
        "path": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
        "kind": "json_classification",
        "expected": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "suppression_ledger",
        "path": "reports/pnva-suppression-ledger-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
    {
        "id": "native_emitter",
        "path": "reports/pnva-native-emitter-summary-2026-05-05.json",
        "kind": "json_classification",
        "expected": "NATIVE_EMITTER_READY",
        "required": True,
    },
    {
        "id": "native_events",
        "path": "reports/pnva-native-events-demo-2026-05-05.jsonl",
        "kind": "jsonl",
        "required": True,
    },
    {
        "id": "native_entities",
        "path": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
        "kind": "entity_catalog",
        "required": True,
    },
    {
        "id": "native_replay",
        "path": "reports/pnva-native-replay-validation-2026-05-05.json",
        "kind": "json_classification",
        "expected": "REPLAY_VALID",
        "required": True,
    },
    {
        "id": "native_no_tick",
        "path": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SOVEREIGN_NO_TICK_READY",
        "required": True,
    },
    {
        "id": "native_policy",
        "path": "reports/pnva-native-sovereign-policy-2026-05-05.json",
        "kind": "json_classification",
        "expected": "SOVEREIGN_POLICY_READY",
        "required": True,
    },
    {
        "id": "native_proof_chain",
        "path": "reports/pnva-native-proof-chain-2026-05-05.json",
        "kind": "json_classification",
        "expected": "PROOF_CHAIN_SEALED",
        "required": True,
    },
    {
        "id": "native_causal_graph",
        "path": "reports/pnva-native-causal-graph-2026-05-05.json",
        "kind": "json_classification",
        "expected": "CAUSAL_GRAPH_READY",
        "required": True,
    },
    {
        "id": "adversarial_validation",
        "path": "reports/pnva-adversarial-validation-2026-05-05.json",
        "kind": "json_classification",
        "expected": "ADVERSARIAL_VALIDATION_PASS",
        "required": True,
    },
    {
        "id": "entity_heuristic_maturity",
        "path": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
        "kind": "json_classification",
        "expected": "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS",
        "required": True,
    },
]


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, path: list[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _jsonl_count(path: Path) -> tuple[int, int]:
    count = 0
    bad = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            count += 1
            try:
                json.loads(line)
            except Exception:
                bad += 1
    return count, bad


def _artifact_status(repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    rel = str(spec["path"])
    path = repo / rel
    item: dict[str, Any] = {
        "id": spec["id"],
        "path": rel,
        "kind": spec["kind"],
        "required": bool(spec.get("required", True)),
        "present": path.exists(),
    }
    if not path.exists():
        item["pass"] = not item["required"]
        item["error"] = "missing"
        return item
    raw = path.read_bytes()
    item["sha256"] = _sha_bytes(raw)
    item["size_bytes"] = len(raw)
    try:
        if spec["kind"] == "jsonl":
            count, bad = _jsonl_count(path)
            item["line_count"] = count
            item["bad_json_lines"] = bad
            item["pass"] = bad == 0 and count > 0
        elif spec["kind"] == "proof_index":
            data = _read_json(path)
            item["entry_count"] = len(data) if isinstance(data, list) else 0
            item["pass"] = isinstance(data, list) and len(data) > 0
        elif spec["kind"] == "entity_catalog":
            data = _read_json(path)
            item["schema_version"] = data.get("schema_version") if isinstance(data, dict) else None
            item["entity_count"] = int(data.get("entity_count", 0)) if isinstance(data, dict) else 0
            item["pass"] = item["schema_version"] == "pnva.entity_catalog.v1" and item["entity_count"] > 0
        elif spec["kind"] == "bridge_summary":
            data = _read_json(path)
            safety = data.get("public_safety", {}) if isinstance(data, dict) else {}
            item["schema_version"] = data.get("schema_version") if isinstance(data, dict) else None
            item["event_count"] = int(data.get("event_count", 0)) if isinstance(data, dict) else 0
            item["pass"] = (
                item["schema_version"] == "pnva.canonical_bridge_summary.v1"
                and item["event_count"] > 0
                and safety.get("raw_ids_published") is False
                and safety.get("raw_paths_published") is False
            )
        elif spec["kind"] == "json_classification":
            data = _read_json(path)
            classification_path = spec.get("classification_path") or ["classification"]
            classification = _dig(data, classification_path)
            item["classification"] = classification
            item["expected"] = spec.get("expected")
            item["reported_pass"] = data.get("pass") if isinstance(data, dict) else None
            item["pass"] = classification == spec.get("expected") and (data.get("pass", True) is not False)
        else:
            item["pass"] = True
    except Exception as exc:
        item["pass"] = False
        item["error"] = str(exc)
    return item


def build_attestation(repo: Path) -> dict[str, Any]:
    artifacts = [_artifact_status(repo, spec) for spec in EXPECTED_ARTIFACTS]
    failures = [item for item in artifacts if not item.get("pass")]
    artifact_seed = [
        {
            "id": item["id"],
            "path": item["path"],
            "sha256": item.get("sha256", ""),
            "classification": item.get("classification", ""),
            "pass": item.get("pass", False),
        }
        for item in artifacts
    ]
    evidence_hash = "sha256:" + _sha_text(json.dumps(artifact_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    classification = "PNVA_SOVEREIGN_EVIDENCE_ATTESTED" if not failures else "PNVA_EVIDENCE_ATTESTATION_FAIL"
    return {
        "schema_version": "pnva.evidence_attestation.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not failures,
        "evidence_hash": evidence_hash,
        "artifact_count": len(artifacts),
        "failure_count": len(failures),
        "artifacts": artifacts,
        "dependency_order": [
            "sanitized proof gates",
            "canonical bridge",
            "replay validation",
            "no-tick invariants",
            "native event emission",
            "sovereign policy validation",
            "proof-chain sealing",
            "causal graph audit",
            "schema contract validation",
            "causal chronology guard",
            "tension-decision calibration",
            "entity no-tick matrix",
            "suppression ledger",
            "adversarial negative controls",
            "entity and heuristic maturity",
            "sovereign audit consumes this attestation without being part of its hash seed",
        ],
        "interpretation": {
            "purpose": "Aggregate public PNVA evidence into a single machine-readable attestation.",
            "hash_policy": "The evidence_hash changes when any tracked artifact hash, classification or pass flag changes.",
            "boundary": "This attests repository evidence integrity; it is not a universal proof of all possible PNVA deployments.",
        },
        "recommendations": [
            "Publish this attestation with every production-evidence release.",
            "Use evidence_hash as the public anchor when citing a PNVA evidence package.",
            "Keep legacy warnings visible while requiring native clean policy for new runtime events.",
            "Run adversarial negative controls so bad evidence is rejected or exposed before publication.",
            "Use entity and heuristic maturity scores to guide the next no-tick runtime hardening step.",
            "Run schema contract validation before attestation so event/entity shape defects become release blockers.",
            "Run causal chronology before attestation so timestamp regressions and batch compaction are explicit.",
            "Run tension-decision calibration before attestation so threshold/decision drift is explicit.",
            "Run entity no-tick matrix before attestation so suppression and execution are attributable by entity.",
            "Run suppression ledger before attestation so avoided execution is proof-backed.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA sovereign evidence attestation over public proof artifacts.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_attestation(repo)
    raw = json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
