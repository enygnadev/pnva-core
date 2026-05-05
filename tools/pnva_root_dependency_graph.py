#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"


NODES: dict[str, dict[str, Any]] = {
    "public_contract": {
        "phase": 0,
        "artifacts": [
            "README.md",
            "MANIFEST.json",
            "SHA256SUMS.txt",
            "LICENSE",
            "LICENSE-DOCS",
            "CITATION.cff",
            "robots.txt",
            "sitemap.xml",
            "llms.txt",
        ],
        "depends_on": [],
    },
    "proof_gates": {
        "phase": 0,
        "artifacts": [
            "proofs/sanitized/prove-long-run-live-gate.json",
            "proofs/sanitized/prove-distribution-gate.json",
            "proofs/sanitized/prove-production-candidate.json",
            "proofs/sanitized/prove-real-stable-opportunity-capture.json",
            "proofs/sanitized/prove-long-run-stability-24h-live.json",
        ],
        "depends_on": ["public_contract"],
    },
    "canonical_bridge": {
        "phase": 1,
        "artifacts": [
            "tools/pnva_canonical_bridge.py",
            "docs/PNVA_CANONICAL_EVENT_BRIDGE.md",
            "reports/pnva-canonical-bridge-summary-2026-05-05.json",
            "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
            "reports/pnva-entity-catalog-2026-05-05.json",
        ],
        "report": "reports/pnva-canonical-bridge-summary-2026-05-05.json",
        "depends_on": ["proof_gates"],
        "ready_fields": {"event_count": {"min": 1}, "public_safety.raw_paths_published": False},
    },
    "native_event_emitter": {
        "phase": 1,
        "artifacts": [
            "tools/pnva_native_event_emitter.py",
            "docs/PNVA_NATIVE_EVENT_EMITTER.md",
            "reports/pnva-native-emitter-summary-2026-05-05.json",
            "reports/pnva-native-events-demo-2026-05-05.jsonl",
            "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
        ],
        "report": "reports/pnva-native-emitter-summary-2026-05-05.json",
        "classification": "NATIVE_EMITTER_READY",
        "depends_on": ["public_contract"],
    },
    "canonical_replay": {
        "phase": 2,
        "artifacts": ["tools/pnva_replay_validator.py", "docs/PNVA_REPLAY_VALIDATION.md", "reports/pnva-replay-validation-2026-05-05.json"],
        "report": "reports/pnva-replay-validation-2026-05-05.json",
        "classification": "REPLAY_VALID",
        "depends_on": ["canonical_bridge"],
    },
    "canonical_no_tick": {
        "phase": 2,
        "artifacts": ["tools/pnva_no_tick_invariant_analyzer.py", "docs/PNVA_NO_TICK_INVARIANTS.md", "reports/pnva-no-tick-invariants-2026-05-05.json"],
        "report": "reports/pnva-no-tick-invariants-2026-05-05.json",
        "classification": "SOVEREIGN_NO_TICK_READY",
        "depends_on": ["canonical_replay"],
    },
    "canonical_policy": {
        "phase": 2,
        "artifacts": ["tools/pnva_sovereign_policy_validator.py", "docs/PNVA_SOVEREIGN_POLICY_VALIDATION.md", "reports/pnva-sovereign-policy-2026-05-05.json"],
        "report": "reports/pnva-sovereign-policy-2026-05-05.json",
        "classification": "SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_replay"],
    },
    "canonical_proof_chain": {
        "phase": 2,
        "artifacts": ["tools/pnva_proof_chain_sealer.py", "docs/PNVA_PROOF_CHAIN_SEALING.md", "reports/pnva-proof-chain-2026-05-05.json"],
        "report": "reports/pnva-proof-chain-2026-05-05.json",
        "classification": "PROOF_CHAIN_SEALED",
        "depends_on": ["canonical_replay"],
    },
    "canonical_causal_graph": {
        "phase": 2,
        "artifacts": ["tools/pnva_causal_graph_auditor.py", "docs/PNVA_CAUSAL_GRAPH_AUDIT.md", "reports/pnva-causal-graph-2026-05-05.json"],
        "report": "reports/pnva-causal-graph-2026-05-05.json",
        "classification": "CAUSAL_GRAPH_READY",
        "depends_on": ["canonical_replay"],
    },
    "native_replay": {
        "phase": 2,
        "artifacts": ["reports/pnva-native-replay-validation-2026-05-05.json"],
        "report": "reports/pnva-native-replay-validation-2026-05-05.json",
        "classification": "REPLAY_VALID",
        "depends_on": ["native_event_emitter"],
    },
    "native_no_tick": {
        "phase": 2,
        "artifacts": ["reports/pnva-native-no-tick-invariants-2026-05-05.json"],
        "report": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
        "classification": "SOVEREIGN_NO_TICK_READY",
        "depends_on": ["native_replay"],
    },
    "native_policy": {
        "phase": 2,
        "artifacts": ["reports/pnva-native-sovereign-policy-2026-05-05.json"],
        "report": "reports/pnva-native-sovereign-policy-2026-05-05.json",
        "classification": "SOVEREIGN_POLICY_READY",
        "depends_on": ["native_replay"],
    },
    "native_proof_chain": {
        "phase": 2,
        "artifacts": ["reports/pnva-native-proof-chain-2026-05-05.json"],
        "report": "reports/pnva-native-proof-chain-2026-05-05.json",
        "classification": "PROOF_CHAIN_SEALED",
        "depends_on": ["native_replay"],
    },
    "native_causal_graph": {
        "phase": 2,
        "artifacts": ["reports/pnva-native-causal-graph-2026-05-05.json"],
        "report": "reports/pnva-native-causal-graph-2026-05-05.json",
        "classification": "CAUSAL_GRAPH_READY",
        "depends_on": ["native_replay"],
    },
    "schema_contract": {
        "phase": 3,
        "artifacts": ["tools/pnva_schema_contract_validator.py", "docs/PNVA_SCHEMA_CONTRACT_VALIDATION.md", "reports/pnva-schema-contract-validation-2026-05-05.json"],
        "report": "reports/pnva-schema-contract-validation-2026-05-05.json",
        "classification": "SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_replay", "native_replay"],
    },
    "causal_chronology": {
        "phase": 3,
        "artifacts": ["tools/pnva_causal_chronology_guard.py", "docs/PNVA_CAUSAL_CHRONOLOGY_GUARD.md", "reports/pnva-causal-chronology-2026-05-05.json"],
        "report": "reports/pnva-causal-chronology-2026-05-05.json",
        "classification": "CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_replay", "native_replay"],
    },
    "tension_decision": {
        "phase": 3,
        "artifacts": ["tools/pnva_tension_decision_calibrator.py", "docs/PNVA_TENSION_DECISION_CALIBRATION.md", "reports/pnva-tension-decision-calibration-2026-05-05.json"],
        "report": "reports/pnva-tension-decision-calibration-2026-05-05.json",
        "classification": "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_no_tick", "native_no_tick"],
    },
    "decision_trace": {
        "phase": 3,
        "artifacts": ["tools/pnva_decision_trace_index.py", "docs/PNVA_DECISION_TRACE_INDEX.md", "reports/pnva-decision-trace-index-2026-05-05.json"],
        "report": "reports/pnva-decision-trace-index-2026-05-05.json",
        "classification": "DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_policy", "native_policy"],
    },
    "heuristic_influence": {
        "phase": 3,
        "artifacts": ["tools/pnva_heuristic_influence_map.py", "docs/PNVA_HEURISTIC_INFLUENCE_MAP.md", "reports/pnva-heuristic-influence-map-2026-05-05.json"],
        "report": "reports/pnva-heuristic-influence-map-2026-05-05.json",
        "classification": "HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["decision_trace"],
    },
    "entity_no_tick": {
        "phase": 3,
        "artifacts": ["tools/pnva_entity_no_tick_matrix.py", "docs/PNVA_ENTITY_NO_TICK_MATRIX.md", "reports/pnva-entity-no-tick-matrix-2026-05-05.json"],
        "report": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
        "classification": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["canonical_no_tick", "native_no_tick", "heuristic_influence"],
    },
    "suppression_ledger": {
        "phase": 3,
        "artifacts": ["tools/pnva_suppression_ledger.py", "docs/PNVA_SUPPRESSION_LEDGER.md", "reports/pnva-suppression-ledger-2026-05-05.json"],
        "report": "reports/pnva-suppression-ledger-2026-05-05.json",
        "classification": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["entity_no_tick", "tension_decision"],
    },
    "adversarial_validation": {
        "phase": 3,
        "artifacts": ["tools/pnva_adversarial_validator.py", "docs/PNVA_ADVERSARIAL_VALIDATION.md", "reports/pnva-adversarial-validation-2026-05-05.json"],
        "report": "reports/pnva-adversarial-validation-2026-05-05.json",
        "classification": "ADVERSARIAL_VALIDATION_PASS",
        "depends_on": ["canonical_policy", "canonical_proof_chain", "canonical_causal_graph"],
    },
    "entity_heuristic_maturity": {
        "phase": 3,
        "artifacts": ["tools/pnva_entity_heuristic_maturity.py", "docs/PNVA_ENTITY_HEURISTIC_MATURITY.md", "reports/pnva-entity-heuristic-maturity-2026-05-05.json"],
        "report": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
        "classification": "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["entity_no_tick", "heuristic_influence"],
    },
    "sovereign_robustness": {
        "phase": 4,
        "artifacts": ["tools/pnva_sovereign_robustness_gate.py", "docs/PNVA_SOVEREIGN_ROBUSTNESS_GATE.md", "reports/pnva-sovereign-robustness-gate-2026-05-05.json"],
        "report": "reports/pnva-sovereign-robustness-gate-2026-05-05.json",
        "classification": "SOVEREIGN_ROBUSTNESS_GATE_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["suppression_ledger", "adversarial_validation", "entity_heuristic_maturity", "schema_contract", "causal_chronology"],
    },
    "r3_migration_plan": {
        "phase": 4,
        "artifacts": ["tools/pnva_r3_migration_planner.py", "docs/PNVA_R3_MIGRATION_PLAN.md", "reports/pnva-r3-migration-plan-2026-05-05.json"],
        "report": "reports/pnva-r3-migration-plan-2026-05-05.json",
        "classification": "R3_MIGRATION_PLAN_READY",
        "depends_on": ["sovereign_robustness"],
    },
    "authority_migration": {
        "phase": 4,
        "artifacts": ["tools/pnva_authority_migration_ledger.py", "docs/PNVA_AUTHORITY_MIGRATION_LEDGER.md", "reports/pnva-authority-migration-ledger-2026-05-05.json"],
        "report": "reports/pnva-authority-migration-ledger-2026-05-05.json",
        "classification": "AUTHORITY_MIGRATION_LEDGER_READY_WITH_LEGACY_WARNINGS",
        "depends_on": ["r3_migration_plan"],
    },
    "r3_authority_projection": {
        "phase": 4,
        "artifacts": ["tools/pnva_r3_authority_projection.py", "docs/PNVA_R3_AUTHORITY_PROJECTION.md", "reports/pnva-r3-authority-projection-summary-2026-05-05.json"],
        "report": "reports/pnva-r3-authority-projection-summary-2026-05-05.json",
        "classification": "R3_AUTHORITY_PROJECTION_READY",
        "depends_on": ["authority_migration"],
    },
    "r3_cutover": {
        "phase": 4,
        "artifacts": ["tools/pnva_r3_cutover_gate.py", "docs/PNVA_R3_CUTOVER_GATE.md", "reports/pnva-r3-cutover-gate-2026-05-05.json"],
        "report": "reports/pnva-r3-cutover-gate-2026-05-05.json",
        "classification": "R3_CUTOVER_APPROVED",
        "depends_on": ["r3_authority_projection"],
    },
    "r3_runtime_emitter": {
        "phase": 5,
        "artifacts": ["tools/pnva_r3_runtime_event_emitter.py", "reports/pnva-r3-runtime-event-emitter-summary-2026-05-05.json", "reports/pnva-r3-runtime-events-2026-05-05.jsonl"],
        "report": "reports/pnva-r3-runtime-event-emitter-summary-2026-05-05.json",
        "classification": "R3_RUNTIME_EVENT_EMITTER_READY",
        "depends_on": ["r3_cutover"],
    },
    "r3_runtime_capture": {
        "phase": 5,
        "artifacts": ["tools/pnva_r3_runtime_capture_matrix.py", "docs/PNVA_R3_RUNTIME_CAPTURE_MATRIX.md", "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
        "classification": "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE",
        "depends_on": ["r3_runtime_emitter"],
    },
    "r3_runtime_guard": {
        "phase": 5,
        "artifacts": ["tools/pnva_r3_runtime_evidence_guard.py", "docs/PNVA_R3_RUNTIME_EVIDENCE_GUARD.md", "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
        "classification": "R3_RUNTIME_EVIDENCE_ACCEPTED",
        "depends_on": ["r3_runtime_capture"],
    },
    "r3_runtime_replay": {
        "phase": 5,
        "artifacts": ["reports/pnva-r3-runtime-replay-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-replay-2026-05-05.json",
        "classification": "REPLAY_VALID",
        "depends_on": ["r3_runtime_guard"],
    },
    "r3_runtime_policy": {
        "phase": 5,
        "artifacts": ["reports/pnva-r3-runtime-policy-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-policy-2026-05-05.json",
        "classification": "SOVEREIGN_POLICY_READY",
        "depends_on": ["r3_runtime_replay"],
    },
    "r3_runtime_no_tick": {
        "phase": 5,
        "artifacts": ["reports/pnva-r3-runtime-no-tick-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
        "classification": "SOVEREIGN_NO_TICK_READY",
        "depends_on": ["r3_runtime_replay"],
    },
    "r3_runtime_proof_chain": {
        "phase": 5,
        "artifacts": ["reports/pnva-r3-runtime-proof-chain-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-proof-chain-2026-05-05.json",
        "classification": "PROOF_CHAIN_SEALED",
        "depends_on": ["r3_runtime_replay"],
    },
    "r3_runtime_instrumentation": {
        "phase": 5,
        "artifacts": ["tools/pnva_r3_runtime_instrumentation_plan.py", "docs/PNVA_R3_RUNTIME_INSTRUMENTATION_PLAN.md", "reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json",
        "classification": "R3_RUNTIME_INSTRUMENTATION_PLAN_READY",
        "depends_on": ["r3_runtime_capture", "r3_runtime_guard"],
    },
    "r3_runtime_contract": {
        "phase": 5,
        "artifacts": ["tools/pnva_r3_runtime_contract_validator.py", "docs/PNVA_R3_RUNTIME_CONTRACT_VALIDATION.md", "reports/pnva-r3-runtime-contract-validation-2026-05-05.json"],
        "report": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
        "classification": "R3_RUNTIME_CONTRACT_VALIDATED_READY",
        "depends_on": ["r3_runtime_instrumentation", "r3_runtime_policy", "r3_runtime_no_tick", "r3_runtime_proof_chain"],
    },
    "sovereign_evolution": {
        "phase": 6,
        "artifacts": ["tools/pnva_sovereign_evolution_ledger.py", "docs/PNVA_SOVEREIGN_EVOLUTION_LEDGER.md", "reports/pnva-sovereign-evolution-ledger-2026-05-05.json"],
        "report": "reports/pnva-sovereign-evolution-ledger-2026-05-05.json",
        "classification": "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY",
        "depends_on": ["r3_runtime_contract", "sovereign_robustness"],
    },
    "evidence_attestation": {
        "phase": 6,
        "artifacts": ["tools/pnva_evidence_attestor.py", "docs/PNVA_SOVEREIGN_EVIDENCE_ATTESTATION.md", "reports/pnva-sovereign-evidence-attestation-2026-05-05.json"],
        "report": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
        "classification": "PNVA_SOVEREIGN_EVIDENCE_ATTESTED",
        "depends_on": ["sovereign_evolution", "adversarial_validation"],
    },
    "semantic_consistency": {
        "phase": 6,
        "artifacts": ["tools/pnva_semantic_consistency_guard.py", "docs/PNVA_SEMANTIC_CONSISTENCY_GUARD.md", "reports/pnva-semantic-consistency-2026-05-05.json"],
        "report": "reports/pnva-semantic-consistency-2026-05-05.json",
        "classification": "SEMANTIC_CONSISTENCY_READY",
        "depends_on": [
            "canonical_no_tick",
            "canonical_policy",
            "canonical_proof_chain",
            "canonical_causal_graph",
            "native_no_tick",
            "native_policy",
            "native_proof_chain",
            "native_causal_graph",
            "schema_contract",
            "causal_chronology",
            "tension_decision",
            "decision_trace",
            "heuristic_influence",
            "entity_no_tick",
            "suppression_ledger",
            "sovereign_robustness",
            "r3_migration_plan",
            "authority_migration",
            "r3_authority_projection",
            "r3_cutover",
            "r3_runtime_capture",
            "r3_runtime_guard",
            "r3_runtime_instrumentation",
            "r3_runtime_contract",
            "sovereign_evolution",
            "adversarial_validation",
            "entity_heuristic_maturity",
            "evidence_attestation",
        ],
    },
    "reproducibility": {
        "phase": 6,
        "artifacts": ["tools/pnva_reproducibility_guard.py", "docs/PNVA_REPRODUCIBILITY_GUARD.md", "reports/pnva-reproducibility-2026-05-05.json"],
        "report": "reports/pnva-reproducibility-2026-05-05.json",
        "classification": "REPRODUCIBILITY_READY",
        "depends_on": ["semantic_consistency"],
    },
    "root_traceability": {
        "phase": 7,
        "artifacts": ["tools/pnva_root_traceability_matrix.py", "docs/PNVA_ROOT_TRACEABILITY_MATRIX.md", "reports/pnva-root-traceability-matrix-2026-05-05.json"],
        "report": "reports/pnva-root-traceability-matrix-2026-05-05.json",
        "classification": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
        "depends_on": ["r3_runtime_contract"],
    },
    "root_sovereignty": {
        "phase": 7,
        "artifacts": ["tools/pnva_root_sovereignty_guard.py", "docs/PNVA_ROOT_SOVEREIGNTY_GUARD.md", "reports/pnva-root-sovereignty-guard-2026-05-05.json"],
        "report": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
        "classification": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
        "depends_on": ["root_traceability", "semantic_consistency", "reproducibility", "evidence_attestation"],
    },
    "root_causal_intelligence": {
        "phase": 7,
        "artifacts": ["tools/pnva_root_causal_intelligence.py", "docs/PNVA_ROOT_CAUSAL_INTELLIGENCE.md", "reports/pnva-root-causal-intelligence-2026-05-05.json"],
        "report": "reports/pnva-root-causal-intelligence-2026-05-05.json",
        "classification": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
        "depends_on": ["root_sovereignty", "root_traceability"],
    },
    "root_adversarial_sentry": {
        "phase": 7,
        "artifacts": ["tools/pnva_root_adversarial_sentry.py", "docs/PNVA_ROOT_ADVERSARIAL_SENTRY.md", "reports/pnva-root-adversarial-sentry-2026-05-05.json"],
        "report": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
        "classification": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
        "depends_on": ["root_sovereignty", "root_causal_intelligence"],
    },
    "root_release_seal": {
        "phase": 8,
        "artifacts": ["tools/pnva_root_release_seal.py", "docs/PNVA_ROOT_RELEASE_SEAL.md", "reports/pnva-root-release-seal-2026-05-05.json"],
        "report": "reports/pnva-root-release-seal-2026-05-05.json",
        "classification": "PNVA_ROOT_RELEASE_SEALED",
        "depends_on": ["root_sovereignty", "root_causal_intelligence", "root_traceability", "root_adversarial_sentry"],
    },
    "root_release_verifier": {
        "phase": 9,
        "artifacts": ["tools/pnva_root_release_verifier.py", "docs/PNVA_ROOT_RELEASE_VERIFIER.md", "reports/pnva-root-release-verifier-2026-05-05.json"],
        "report": "reports/pnva-root-release-verifier-2026-05-05.json",
        "classification": "PNVA_ROOT_RELEASE_VERIFIED",
        "depends_on": ["root_release_seal"],
    },
    "root_claim_boundary": {
        "phase": 10,
        "artifacts": ["tools/pnva_root_claim_boundary_guard.py", "docs/PNVA_ROOT_CLAIM_BOUNDARY_GUARD.md", "reports/pnva-root-claim-boundary-guard-2026-05-05.json"],
        "report": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
        "classification": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
        "depends_on": ["root_release_verifier"],
    },
    "root_publication": {
        "phase": 10,
        "artifacts": ["tools/pnva_root_publication_gate.py", "docs/PNVA_ROOT_PUBLICATION_GATE.md", "reports/pnva-root-publication-gate-2026-05-05.json"],
        "report": "reports/pnva-root-publication-gate-2026-05-05.json",
        "classification": "PNVA_ROOT_PUBLICATION_GATE_READY",
        "depends_on": ["root_claim_boundary", "public_contract"],
    },
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, dotted: str, default: Any = None) -> Any:
    current = data
    for key in dotted.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _node_report(repo: Path, node_id: str, node: dict[str, Any]) -> dict[str, Any]:
    artifacts = [str(item) for item in node.get("artifacts", [])]
    missing_artifacts = [rel for rel in artifacts if not (repo / rel).exists()]
    report_rel = node.get("report")
    report_data: dict[str, Any] = {}
    report_parse_error = ""
    if report_rel and (repo / str(report_rel)).exists():
        try:
            loaded = _read_json(repo / str(report_rel))
            if isinstance(loaded, dict):
                report_data = loaded
        except Exception as exc:
            report_parse_error = str(exc)

    readiness_failures: list[str] = []
    expected = node.get("classification")
    if expected:
        actual = report_data.get("classification")
        if actual != expected:
            readiness_failures.append(f"classification:{actual}!={expected}")
        if report_data.get("pass") is not True:
            readiness_failures.append("pass_not_true")

    for field, expected_value in node.get("ready_fields", {}).items():
        actual_value = _dig(report_data, field)
        if isinstance(expected_value, dict) and "min" in expected_value:
            try:
                if float(actual_value) < float(expected_value["min"]):
                    readiness_failures.append(f"{field}_below_min")
            except (TypeError, ValueError):
                readiness_failures.append(f"{field}_not_numeric")
        elif actual_value != expected_value:
            readiness_failures.append(f"{field}:{actual_value}!={expected_value}")

    return {
        "node_id": node_id,
        "phase": int(node.get("phase", 0)),
        "depends_on": list(node.get("depends_on", [])),
        "artifact_count": len(artifacts),
        "missing_artifacts": missing_artifacts,
        "report": report_rel,
        "report_parse_error": report_parse_error,
        "expected_classification": expected,
        "actual_classification": report_data.get("classification"),
        "actual_pass": report_data.get("pass"),
        "readiness_failures": readiness_failures,
        "ready": not missing_artifacts and not report_parse_error and not readiness_failures,
    }


def _cycles(nodes: dict[str, dict[str, Any]]) -> list[list[str]]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []
    cycles: list[list[str]] = []

    def visit(node_id: str) -> None:
        if node_id in visited:
            return
        if node_id in visiting:
            try:
                start = stack.index(node_id)
            except ValueError:
                start = 0
            cycles.append(stack[start:] + [node_id])
            return
        visiting.add(node_id)
        stack.append(node_id)
        for dep in nodes[node_id].get("depends_on", []):
            if dep in nodes:
                visit(dep)
        stack.pop()
        visiting.remove(node_id)
        visited.add(node_id)

    for node_id in sorted(nodes):
        visit(node_id)
    return cycles


def _reverse_edges(nodes: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    reverse: dict[str, list[str]] = defaultdict(list)
    for node_id, node in nodes.items():
        for dep in node.get("depends_on", []):
            reverse[str(dep)].append(node_id)
    return {key: sorted(value) for key, value in reverse.items()}


def _can_reach_root(nodes: dict[str, dict[str, Any]], target: str) -> tuple[list[str], dict[str, int]]:
    reachable: set[str] = set()
    distance: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque([(target, 0)])
    while queue:
        current, depth = queue.popleft()
        if current in reachable:
            continue
        reachable.add(current)
        distance[current] = depth
        for dependency in nodes[current].get("depends_on", []):
            if dependency in nodes:
                queue.append((str(dependency), depth + 1))
    missing = sorted(set(nodes) - reachable)
    return missing, distance


def _phase_violations(nodes: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    violations = []
    for node_id, node in nodes.items():
        phase = int(node.get("phase", 0))
        for dep in node.get("depends_on", []):
            if dep not in nodes:
                violations.append({"node": node_id, "dependency": dep, "reason": "unknown_dependency"})
                continue
            dep_phase = int(nodes[dep].get("phase", 0))
            if dep_phase > phase:
                violations.append({"node": node_id, "phase": phase, "dependency": dep, "dependency_phase": dep_phase})
    return violations


def _topological_order(nodes: dict[str, dict[str, Any]]) -> list[str]:
    indegree = {node_id: 0 for node_id in nodes}
    reverse = _reverse_edges(nodes)
    for node in nodes.values():
        for dep in node.get("depends_on", []):
            if dep in indegree:
                indegree[str(dep)] += 0
    for node_id, node in nodes.items():
        for dep in node.get("depends_on", []):
            if dep in nodes:
                indegree[node_id] += 1
    queue = deque(sorted(node_id for node_id, count in indegree.items() if count == 0))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child in reverse.get(current, []):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    return order


def build_report(repo: Path) -> dict[str, Any]:
    node_rows = [_node_report(repo, node_id, node) for node_id, node in sorted(NODES.items())]
    missing_artifacts = [
        {"node_id": row["node_id"], "missing_artifacts": row["missing_artifacts"]}
        for row in node_rows
        if row["missing_artifacts"]
    ]
    readiness_failures = [
        {"node_id": row["node_id"], "failures": row["readiness_failures"], "report_parse_error": row["report_parse_error"]}
        for row in node_rows
        if row["readiness_failures"] or row["report_parse_error"]
    ]
    cycles = _cycles(NODES)
    phase_violations = _phase_violations(NODES)
    unreachable, distance_to_publication = _can_reach_root(NODES, "root_publication")
    topological_order = _topological_order(NODES)

    sealed_dependencies = set(NODES["root_release_seal"]["depends_on"])
    expected_sealed_dependencies = {"root_sovereignty", "root_causal_intelligence", "root_traceability", "root_adversarial_sentry"}
    post_seal_nodes = {"root_release_verifier", "root_claim_boundary", "root_publication"}
    pre_seal_depends_on_post_seal = []
    for node_id, node in NODES.items():
        if int(node.get("phase", 0)) <= int(NODES["root_release_seal"]["phase"]):
            leaked = sorted(set(node.get("depends_on", [])) & post_seal_nodes)
            if leaked:
                pre_seal_depends_on_post_seal.append({"node_id": node_id, "post_seal_dependencies": leaked})

    checks = [
        _check("all_dependency_artifacts_exist", not missing_artifacts, {"missing_artifact_nodes": missing_artifacts[:20]}),
        _check("all_classified_reports_ready", not readiness_failures, {"readiness_failures": readiness_failures[:20]}),
        _check("dependency_graph_acyclic", not cycles, {"cycles": cycles[:10]}),
        _check("dependency_phase_order_valid", not phase_violations, {"phase_violations": phase_violations[:20]}),
        _check("all_nodes_reach_publication_gate", not unreachable, {"unreachable_nodes": unreachable}),
        _check(
            "root_release_seal_has_expected_inputs",
            expected_sealed_dependencies.issubset(sealed_dependencies),
            {"expected": sorted(expected_sealed_dependencies), "actual": sorted(sealed_dependencies)},
        ),
        _check("pre_seal_nodes_do_not_depend_on_post_seal_nodes", not pre_seal_depends_on_post_seal, {"violations": pre_seal_depends_on_post_seal}),
        _check("topological_order_covers_all_nodes", len(topological_order) == len(NODES), {"topological_order_count": len(topological_order), "node_count": len(NODES)}),
    ]
    failures = [item for item in checks if not item["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)

    graph_fingerprint_seed = {
        "nodes": [
            {
                "node_id": row["node_id"],
                "phase": row["phase"],
                "depends_on": row["depends_on"],
                "expected_classification": row["expected_classification"],
                "actual_classification": row["actual_classification"],
                "actual_pass": row["actual_pass"],
                "ready": row["ready"],
            }
            for row in node_rows
        ],
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
    }
    graph_hash = _sha_text(json.dumps(graph_fingerprint_seed, sort_keys=True, separators=(",", ":")))

    classification = "PNVA_ROOT_DEPENDENCY_GRAPH_READY" if not failures else "PNVA_ROOT_DEPENDENCY_GRAPH_FAIL"
    edge_count = sum(len(node.get("depends_on", [])) for node in NODES.values())
    phase_counts: dict[str, int] = defaultdict(int)
    for node in NODES.values():
        phase_counts[str(node.get("phase", 0))] += 1

    return {
        "schema_version": "pnva.root_dependency_graph.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "dependency_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "node_count": len(NODES),
        "edge_count": edge_count,
        "phase_count": len(phase_counts),
        "phase_counts": dict(sorted(phase_counts.items(), key=lambda item: int(item[0]))),
        "missing_artifact_count": sum(len(row["missing_artifacts"]) for row in node_rows),
        "readiness_failure_count": sum(len(row["readiness_failures"]) + (1 if row["report_parse_error"] else 0) for row in node_rows),
        "cycle_count": len(cycles),
        "phase_violation_count": len(phase_violations),
        "unreachable_node_count": len(unreachable),
        "topological_order_count": len(topological_order),
        "max_distance_to_publication": max(distance_to_publication.values()) if distance_to_publication else 0,
        "root_publication_node": "root_publication",
        "root_release_hash": _dig(_read_json(repo / "reports/pnva-root-release-seal-2026-05-05.json"), "root_release_hash", ""),
        "dependency_graph_hash": graph_hash,
        "checks": checks,
        "topological_order": topological_order,
        "nodes": node_rows,
        "boundary": "This graph validates public repository evidence dependencies only. It does not extend claims beyond the published proof reports.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root dependency graph.")
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
