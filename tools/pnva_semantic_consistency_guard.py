#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any


REPORTS = {
    "manifest": "MANIFEST.json",
    "bridge": "reports/pnva-canonical-bridge-summary-2026-05-05.json",
    "replay": "reports/pnva-replay-validation-2026-05-05.json",
    "no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native_emitter": "reports/pnva-native-emitter-summary-2026-05-05.json",
    "native_no_tick": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "policy": "reports/pnva-sovereign-policy-2026-05-05.json",
    "native_policy": "reports/pnva-native-sovereign-policy-2026-05-05.json",
    "proof_chain": "reports/pnva-proof-chain-2026-05-05.json",
    "native_proof_chain": "reports/pnva-native-proof-chain-2026-05-05.json",
    "causal_graph": "reports/pnva-causal-graph-2026-05-05.json",
    "native_causal_graph": "reports/pnva-native-causal-graph-2026-05-05.json",
    "schema_contract": "reports/pnva-schema-contract-validation-2026-05-05.json",
    "causal_chronology": "reports/pnva-causal-chronology-2026-05-05.json",
    "tension_decision": "reports/pnva-tension-decision-calibration-2026-05-05.json",
    "entity_no_tick_matrix": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
    "suppression_ledger": "reports/pnva-suppression-ledger-2026-05-05.json",
    "adversarial": "reports/pnva-adversarial-validation-2026-05-05.json",
    "maturity": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
    "attestation": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
    "audit": "reports/pnva-sovereign-audit-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "replay": "REPLAY_VALID",
    "no_tick": "SOVEREIGN_NO_TICK_READY",
    "native_emitter": "NATIVE_EMITTER_READY",
    "native_no_tick": "SOVEREIGN_NO_TICK_READY",
    "policy": "SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS",
    "native_policy": "SOVEREIGN_POLICY_READY",
    "proof_chain": "PROOF_CHAIN_SEALED",
    "native_proof_chain": "PROOF_CHAIN_SEALED",
    "causal_graph": "CAUSAL_GRAPH_READY",
    "native_causal_graph": "CAUSAL_GRAPH_READY",
    "schema_contract": "SCHEMA_CONTRACT_READY_WITH_LEGACY_WARNINGS",
    "causal_chronology": "CAUSAL_CHRONOLOGY_READY_WITH_LEGACY_WARNINGS",
    "tension_decision": "TENSION_DECISION_READY_WITH_LEGACY_WARNINGS",
    "entity_no_tick_matrix": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
    "suppression_ledger": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
    "adversarial": "ADVERSARIAL_VALIDATION_PASS",
    "maturity": "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS",
    "attestation": "PNVA_SOVEREIGN_EVIDENCE_ATTESTED",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _ratio(part: int | float, total: int | float, digits: int = 6) -> float:
    return round(float(part) / max(1.0, float(total)), digits)


def _equal(left: Any, right: Any, *, tolerance: float = 0.0) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)
    return left == right


def _check(
    checks: list[dict[str, Any]],
    findings: list[dict[str, Any]],
    *,
    group: str,
    name: str,
    left_ref: str,
    left: Any,
    right_ref: str,
    right: Any,
    severity: str = "error",
    tolerance: float = 0.0,
) -> None:
    passed = _equal(left, right, tolerance=tolerance)
    item = {
        "group": group,
        "name": name,
        "pass": passed,
        "left_ref": left_ref,
        "left": left,
        "right_ref": right_ref,
        "right": right,
        "severity": severity,
    }
    if tolerance:
        item["tolerance"] = tolerance
    checks.append(item)
    if not passed:
        findings.append(item)


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    data = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    manifest_summary = data["manifest"].get("summary", {}) if isinstance(data["manifest"], dict) else {}
    checks: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def check_error(**kwargs: Any) -> None:
        _check(checks, errors, severity="error", **kwargs)

    def check_warning(**kwargs: Any) -> None:
        _check(checks, warnings, severity="warning", **kwargs)

    for key, classification in EXPECTED_CLASSIFICATIONS.items():
        check_error(
            group="classification",
            name=f"{key}_classification",
            left_ref=f"{REPORTS[key]}:classification",
            left=data[key].get("classification"),
            right_ref="expected",
            right=classification,
        )
        if "pass" in data[key]:
            check_error(
                group="classification",
                name=f"{key}_pass_flag",
                left_ref=f"{REPORTS[key]}:pass",
                left=data[key].get("pass"),
                right_ref="expected",
                right=True,
            )

    bridge_count = int(data["bridge"].get("event_count", 0))
    bridge_entities = int(data["bridge"].get("entity_count", 0))
    canonical_events = int(_dig(data["no_tick"], ["summary", "event_count"], 0))
    native_events = int(_dig(data["native_no_tick"], ["summary", "event_count"], 0))
    canonical_suppressed = int(_dig(data["no_tick"], ["no_tick_efficiency", "suppressed_count"], 0))
    native_suppressed = int(_dig(data["native_no_tick"], ["no_tick_efficiency", "suppressed_count"], 0))
    canonical_strong = int(_dig(data["policy"], ["summary", "strong_decision_count"], 0))
    native_strong = int(_dig(data["native_policy"], ["summary", "strong_decision_count"], 0))
    canonical_low_authority = int(_dig(data["policy"], ["summary", "low_authority_legacy_count"], 0))
    native_low_authority = int(_dig(data["native_policy"], ["summary", "low_authority_legacy_count"], 0))
    total_events = canonical_events + native_events
    total_suppressed = canonical_suppressed + native_suppressed
    total_strong = canonical_strong + native_strong
    total_hard = total_strong - canonical_low_authority - native_low_authority

    # Manifest to source reports.
    check_error(group="manifest", name="manifest_bridge_event_count", left_ref="MANIFEST:canonical_event_bridge.event_count", left=_dig(manifest_summary, ["canonical_event_bridge", "event_count"]), right_ref="bridge:event_count", right=bridge_count)
    check_error(group="manifest", name="manifest_bridge_entity_count", left_ref="MANIFEST:canonical_event_bridge.entity_count", left=_dig(manifest_summary, ["canonical_event_bridge", "entity_count"]), right_ref="bridge:entity_count", right=bridge_entities)
    check_error(group="manifest", name="manifest_replay_event_count", left_ref="MANIFEST:replay_validation.event_count", left=_dig(manifest_summary, ["replay_validation", "event_count"]), right_ref="replay:summary.event_count", right=_dig(data["replay"], ["summary", "event_count"]))
    check_error(group="manifest", name="manifest_no_tick_event_count", left_ref="MANIFEST:no_tick_invariants.event_count", left=_dig(manifest_summary, ["no_tick_invariants", "event_count"]), right_ref="no_tick:summary.event_count", right=canonical_events)
    check_error(group="manifest", name="manifest_no_tick_suppressed_count", left_ref="MANIFEST:no_tick_invariants.suppressed_count", left=_dig(manifest_summary, ["no_tick_invariants", "suppressed_count"]), right_ref="no_tick:no_tick_efficiency.suppressed_count", right=canonical_suppressed)
    check_error(group="manifest", name="manifest_native_event_count", left_ref="MANIFEST:native_event_emitter.event_count", left=_dig(manifest_summary, ["native_event_emitter", "event_count"]), right_ref="native_no_tick:summary.event_count", right=native_events)
    check_error(group="manifest", name="manifest_native_suppressed_count", left_ref="MANIFEST:native_event_emitter.suppressed_count", left=_dig(manifest_summary, ["native_event_emitter", "suppressed_count"]), right_ref="native_no_tick:no_tick_efficiency.suppressed_count", right=native_suppressed)
    check_error(group="manifest", name="manifest_policy_canonical_strong_count", left_ref="MANIFEST:sovereign_policy_validation.canonical_strong_decision_count", left=_dig(manifest_summary, ["sovereign_policy_validation", "canonical_strong_decision_count"]), right_ref="policy:summary.strong_decision_count", right=canonical_strong)
    check_error(group="manifest", name="manifest_policy_native_strong_count", left_ref="MANIFEST:sovereign_policy_validation.native_strong_decision_count", left=_dig(manifest_summary, ["sovereign_policy_validation", "native_strong_decision_count"]), right_ref="native_policy:summary.strong_decision_count", right=native_strong)
    check_error(group="manifest", name="manifest_adversarial_detected_count", left_ref="MANIFEST:adversarial_validation.detected_count", left=_dig(manifest_summary, ["adversarial_validation", "detected_count"]), right_ref="adversarial:detected_count", right=data["adversarial"].get("detected_count"))
    check_error(group="manifest", name="manifest_maturity_score", left_ref="MANIFEST:entity_heuristic_maturity.maturity_score", left=_dig(manifest_summary, ["entity_heuristic_maturity", "maturity_score"]), right_ref="maturity:maturity_score", right=data["maturity"].get("maturity_score"), tolerance=0.000001)
    check_error(group="manifest", name="manifest_attestation_artifact_count", left_ref="MANIFEST:sovereign_evidence_attestation.artifact_count", left=_dig(manifest_summary, ["sovereign_evidence_attestation", "artifact_count"]), right_ref="attestation:artifact_count", right=data["attestation"].get("artifact_count"))
    check_error(group="manifest", name="manifest_attestation_hash", left_ref="MANIFEST:sovereign_evidence_attestation.evidence_hash", left=_dig(manifest_summary, ["sovereign_evidence_attestation", "evidence_hash"]), right_ref="attestation:evidence_hash", right=data["attestation"].get("evidence_hash"))
    check_error(group="manifest", name="manifest_schema_contract_event_count", left_ref="MANIFEST:schema_contract_validation.event_count", left=_dig(manifest_summary, ["schema_contract_validation", "event_count"]), right_ref="schema_contract:event_count", right=data["schema_contract"].get("event_count"))
    check_error(group="manifest", name="manifest_schema_contract_entity_count", left_ref="MANIFEST:schema_contract_validation.entity_count", left=_dig(manifest_summary, ["schema_contract_validation", "entity_count"]), right_ref="schema_contract:entity_count", right=data["schema_contract"].get("entity_count"))
    check_error(group="manifest", name="manifest_schema_contract_warning_count", left_ref="MANIFEST:schema_contract_validation.warning_count", left=_dig(manifest_summary, ["schema_contract_validation", "warning_count"]), right_ref="schema_contract:warning_count", right=data["schema_contract"].get("warning_count"))
    check_error(group="manifest", name="manifest_causal_chronology_event_count", left_ref="MANIFEST:causal_chronology.event_count", left=_dig(manifest_summary, ["causal_chronology", "event_count"]), right_ref="causal_chronology:event_count", right=data["causal_chronology"].get("event_count"))
    check_error(group="manifest", name="manifest_causal_chronology_chain_count", left_ref="MANIFEST:causal_chronology.chain_count", left=_dig(manifest_summary, ["causal_chronology", "chain_count"]), right_ref="causal_chronology:chain_count", right=data["causal_chronology"].get("chain_count"))
    check_error(group="manifest", name="manifest_causal_chronology_backward_count", left_ref="MANIFEST:causal_chronology.global_backward_count", left=_dig(manifest_summary, ["causal_chronology", "global_backward_count"]), right_ref="causal_chronology:global_backward_count", right=data["causal_chronology"].get("global_backward_count"))
    check_error(group="manifest", name="manifest_tension_decision_event_count", left_ref="MANIFEST:tension_decision_calibration.event_count", left=_dig(manifest_summary, ["tension_decision_calibration", "event_count"]), right_ref="tension_decision:event_count", right=data["tension_decision"].get("event_count"))
    check_error(group="manifest", name="manifest_tension_decision_warning_count", left_ref="MANIFEST:tension_decision_calibration.warning_count", left=_dig(manifest_summary, ["tension_decision_calibration", "warning_count"]), right_ref="tension_decision:warning_count", right=data["tension_decision"].get("warning_count"))
    check_error(group="manifest", name="manifest_tension_decision_native_clean", left_ref="MANIFEST:tension_decision_calibration.native_calibration_clean", left=_dig(manifest_summary, ["tension_decision_calibration", "native_calibration_clean"]), right_ref="tension_decision:native_calibration_clean", right=data["tension_decision"].get("native_calibration_clean"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_event_count", left_ref="MANIFEST:entity_no_tick_matrix.event_count", left=_dig(manifest_summary, ["entity_no_tick_matrix", "event_count"]), right_ref="entity_no_tick_matrix:event_count", right=data["entity_no_tick_matrix"].get("event_count"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_suppressed_count", left_ref="MANIFEST:entity_no_tick_matrix.suppressed_count", left=_dig(manifest_summary, ["entity_no_tick_matrix", "suppressed_count"]), right_ref="entity_no_tick_matrix:suppressed_count", right=data["entity_no_tick_matrix"].get("suppressed_count"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_native_clean", left_ref="MANIFEST:entity_no_tick_matrix.native_matrix_clean", left=_dig(manifest_summary, ["entity_no_tick_matrix", "native_matrix_clean"]), right_ref="entity_no_tick_matrix:native_matrix_clean", right=data["entity_no_tick_matrix"].get("native_matrix_clean"))
    check_error(group="manifest", name="manifest_suppression_ledger_event_count", left_ref="MANIFEST:suppression_ledger.event_count", left=_dig(manifest_summary, ["suppression_ledger", "event_count"]), right_ref="suppression_ledger:event_count", right=data["suppression_ledger"].get("event_count"))
    check_error(group="manifest", name="manifest_suppression_ledger_suppressed_count", left_ref="MANIFEST:suppression_ledger.suppressed_count", left=_dig(manifest_summary, ["suppression_ledger", "suppressed_count"]), right_ref="suppression_ledger:suppressed_count", right=data["suppression_ledger"].get("suppressed_count"))
    check_error(group="manifest", name="manifest_suppression_ledger_native_clean", left_ref="MANIFEST:suppression_ledger.native_suppression_clean", left=_dig(manifest_summary, ["suppression_ledger", "native_suppression_clean"]), right_ref="suppression_ledger:native_suppression_clean", right=data["suppression_ledger"].get("native_suppression_clean"))

    # Canonical report agreement.
    for key, report_name in (
        ("replay", "replay"),
        ("policy", "policy"),
        ("proof_chain", "proof_chain"),
        ("causal_graph", "causal_graph"),
    ):
        path = REPORTS[report_name]
        if report_name == "proof_chain":
            observed = _dig(data[report_name], ["seal", "event_count"], 0)
        else:
            observed = _dig(data[report_name], ["summary", "event_count"], 0)
        check_error(group="canonical", name=f"canonical_event_count_matches_{key}", left_ref=f"{path}:event_count", left=observed, right_ref="bridge:event_count", right=bridge_count)
    check_error(group="canonical", name="bridge_entity_count_matches_graph_catalog", left_ref="bridge:entity_count", left=bridge_entities, right_ref="causal_graph:summary.catalog_entity_count", right=_dig(data["causal_graph"], ["summary", "catalog_entity_count"], 0))
    check_error(group="canonical", name="replay_proofs_match_event_count", left_ref="replay:summary.proof_hash_ok", left=_dig(data["replay"], ["summary", "proof_hash_ok"], 0), right_ref="replay:summary.event_count", right=_dig(data["replay"], ["summary", "event_count"], 0))
    check_error(group="canonical", name="proof_chain_unique_ids_match_event_count", left_ref="proof_chain:seal.unique_event_ids", left=_dig(data["proof_chain"], ["seal", "unique_event_ids"], 0), right_ref="proof_chain:seal.event_count", right=_dig(data["proof_chain"], ["seal", "event_count"], 0))

    # Native report agreement.
    for report_name in ("native_emitter", "native_policy", "native_proof_chain", "native_causal_graph"):
        if report_name == "native_proof_chain":
            observed = _dig(data[report_name], ["seal", "event_count"], 0)
        elif report_name == "native_emitter":
            observed = data[report_name].get("event_count")
        else:
            observed = _dig(data[report_name], ["summary", "event_count"], 0)
        check_error(group="native", name=f"native_event_count_matches_{report_name}", left_ref=f"{REPORTS[report_name]}:event_count", left=observed, right_ref="native_no_tick:summary.event_count", right=native_events)
    check_error(group="native", name="native_entity_count_matches_graph_catalog", left_ref="native_emitter:entity_count", left=data["native_emitter"].get("entity_count"), right_ref="native_causal_graph:summary.catalog_entity_count", right=_dig(data["native_causal_graph"], ["summary", "catalog_entity_count"], 0))
    check_error(group="native", name="native_proof_chain_unique_ids_match_event_count", left_ref="native_proof_chain:seal.unique_event_ids", left=_dig(data["native_proof_chain"], ["seal", "unique_event_ids"], 0), right_ref="native_proof_chain:seal.event_count", right=_dig(data["native_proof_chain"], ["seal", "event_count"], 0))
    check_error(group="chronology", name="chronology_total_event_count", left_ref="causal_chronology:event_count", left=data["causal_chronology"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="chronology", name="chronology_native_clean", left_ref="causal_chronology:native_chronology_clean", left=data["causal_chronology"].get("native_chronology_clean"), right_ref="expected", right=True)
    check_error(group="tension_decision", name="tension_decision_total_event_count", left_ref="tension_decision:event_count", left=data["tension_decision"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="tension_decision", name="tension_decision_native_clean", left_ref="tension_decision:native_calibration_clean", left=data["tension_decision"].get("native_calibration_clean"), right_ref="expected", right=True)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_total_event_count", left_ref="entity_no_tick_matrix:event_count", left=data["entity_no_tick_matrix"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_total_suppressed_count", left_ref="entity_no_tick_matrix:suppressed_count", left=data["entity_no_tick_matrix"].get("suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_native_clean", left_ref="entity_no_tick_matrix:native_matrix_clean", left=data["entity_no_tick_matrix"].get("native_matrix_clean"), right_ref="expected", right=True)
    check_error(group="suppression_ledger", name="suppression_ledger_total_event_count", left_ref="suppression_ledger:event_count", left=data["suppression_ledger"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="suppression_ledger", name="suppression_ledger_total_suppressed_count", left_ref="suppression_ledger:suppressed_count", left=data["suppression_ledger"].get("suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="suppression_ledger", name="suppression_ledger_avoided_matches_suppressed", left_ref="suppression_ledger:estimated_avoided_execution_count", left=data["suppression_ledger"].get("estimated_avoided_execution_count"), right_ref="suppression_ledger:suppressed_count", right=data["suppression_ledger"].get("suppressed_count"))
    check_error(group="suppression_ledger", name="suppression_ledger_native_clean", left_ref="suppression_ledger:native_suppression_clean", left=data["suppression_ledger"].get("native_suppression_clean"), right_ref="expected", right=True)

    # Maturity aggregate math.
    maturity_summary = data["maturity"].get("summary", {})
    check_error(group="maturity_math", name="maturity_total_events", left_ref="maturity:summary.total_event_count", left=maturity_summary.get("total_event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="maturity_math", name="maturity_total_suppressed", left_ref="maturity:summary.total_suppressed_count", left=maturity_summary.get("total_suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="maturity_math", name="maturity_total_strong", left_ref="maturity:summary.total_strong_decision_count", left=maturity_summary.get("total_strong_decision_count"), right_ref="policy_strong+native_policy_strong", right=total_strong)
    check_error(group="maturity_math", name="maturity_total_hard_authority", left_ref="maturity:summary.total_strong_with_hard_authority", left=maturity_summary.get("total_strong_with_hard_authority"), right_ref="strong-low_authority", right=total_hard)
    check_error(group="maturity_math", name="maturity_suppression_ratio", left_ref="maturity:summary.aggregate_no_tick_suppression_ratio", left=maturity_summary.get("aggregate_no_tick_suppression_ratio"), right_ref="total_suppressed/total_events", right=_ratio(total_suppressed, total_events), tolerance=0.000001)
    check_error(group="maturity_math", name="maturity_hard_authority_ratio", left_ref="maturity:summary.aggregate_hard_authority_ratio", left=maturity_summary.get("aggregate_hard_authority_ratio"), right_ref="total_hard/total_strong", right=_ratio(total_hard, total_strong), tolerance=0.000001)

    # Attestation and audit alignment.
    artifacts = data["attestation"].get("artifacts", [])
    artifact_ids = [str(item.get("id")) for item in artifacts if isinstance(item, dict)]
    check_error(group="attestation", name="artifact_count_matches_list", left_ref="attestation:artifact_count", left=data["attestation"].get("artifact_count"), right_ref="len(attestation.artifacts)", right=len(artifacts))
    check_error(group="attestation", name="failure_count_zero", left_ref="attestation:failure_count", left=data["attestation"].get("failure_count"), right_ref="expected", right=0)
    for required_id in ("schema_contract_validation", "causal_chronology", "tension_decision_calibration", "entity_no_tick_matrix", "suppression_ledger", "adversarial_validation", "entity_heuristic_maturity"):
        check_error(group="attestation", name=f"attestation_contains_{required_id}", left_ref="attestation:artifact_ids", left=required_id in artifact_ids, right_ref="expected", right=True)
    check_error(group="audit", name="audit_score_ready", left_ref="audit:score.classification", left=_dig(data["audit"], ["score", "classification"]), right_ref="expected", right="SOVEREIGN_READY")
    check_error(group="audit", name="audit_attestation_hash_matches", left_ref="audit:evidence_attestation.evidence_hash", left=_dig(data["audit"], ["evidence_attestation", "evidence_hash"]), right_ref="attestation:evidence_hash", right=data["attestation"].get("evidence_hash"))
    check_error(group="audit", name="audit_maturity_score_matches", left_ref="audit:entity_heuristic_maturity.maturity_score", left=_dig(data["audit"], ["entity_heuristic_maturity", "maturity_score"]), right_ref="maturity:maturity_score", right=data["maturity"].get("maturity_score"), tolerance=0.000001)
    check_error(group="audit", name="audit_schema_contract_matches", left_ref="audit:schema_contract.classification", left=_dig(data["audit"], ["schema_contract_validation", "classification"]), right_ref="schema_contract:classification", right=data["schema_contract"].get("classification"))
    check_error(group="audit", name="audit_chronology_matches", left_ref="audit:causal_chronology.classification", left=_dig(data["audit"], ["causal_chronology", "classification"]), right_ref="causal_chronology:classification", right=data["causal_chronology"].get("classification"))
    check_error(group="audit", name="audit_tension_decision_matches", left_ref="audit:tension_decision.classification", left=_dig(data["audit"], ["tension_decision_calibration", "classification"]), right_ref="tension_decision:classification", right=data["tension_decision"].get("classification"))
    check_error(group="audit", name="audit_entity_no_tick_matrix_matches", left_ref="audit:entity_no_tick_matrix.classification", left=_dig(data["audit"], ["entity_no_tick_matrix", "classification"]), right_ref="entity_no_tick_matrix:classification", right=data["entity_no_tick_matrix"].get("classification"))
    check_error(group="audit", name="audit_suppression_ledger_matches", left_ref="audit:suppression_ledger.classification", left=_dig(data["audit"], ["suppression_ledger", "classification"]), right_ref="suppression_ledger:classification", right=data["suppression_ledger"].get("classification"))

    manifest_files = data["manifest"].get("files", []) if isinstance(data["manifest"], dict) else []
    duplicate_files = sorted({item for item in manifest_files if manifest_files.count(item) > 1})
    check_warning(group="manifest_hygiene", name="manifest_file_list_has_no_duplicates", left_ref="MANIFEST:files duplicates", left=duplicate_files, right_ref="expected", right=[])
    missing_files = sorted(str(item) for item in manifest_files if isinstance(item, str) and not (repo / item).exists())
    check_error(group="manifest_hygiene", name="manifest_files_exist", left_ref="MANIFEST:files missing", left=missing_files, right_ref="expected", right=[])

    classification = "SEMANTIC_CONSISTENCY_READY" if not errors else "SEMANTIC_CONSISTENCY_FAIL"
    return {
        "schema_version": "pnva.semantic_consistency.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "check_count": len(checks),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "reports_checked": REPORTS,
        "summary": {
            "canonical_event_count": canonical_events,
            "native_event_count": native_events,
            "total_event_count": total_events,
            "canonical_suppressed_count": canonical_suppressed,
            "native_suppressed_count": native_suppressed,
            "total_suppressed_count": total_suppressed,
            "total_strong_decision_count": total_strong,
            "total_strong_with_hard_authority": total_hard,
            "schema_contract_event_count": data["schema_contract"].get("event_count"),
            "schema_contract_warning_count": data["schema_contract"].get("warning_count"),
            "causal_chronology_event_count": data["causal_chronology"].get("event_count"),
            "causal_chronology_warning_count": data["causal_chronology"].get("warning_count"),
            "tension_decision_event_count": data["tension_decision"].get("event_count"),
            "tension_decision_warning_count": data["tension_decision"].get("warning_count"),
            "entity_no_tick_matrix_event_count": data["entity_no_tick_matrix"].get("event_count"),
            "entity_no_tick_matrix_suppressed_count": data["entity_no_tick_matrix"].get("suppressed_count"),
            "entity_no_tick_matrix_warning_count": data["entity_no_tick_matrix"].get("warning_count"),
            "suppression_ledger_event_count": data["suppression_ledger"].get("event_count"),
            "suppression_ledger_suppressed_count": data["suppression_ledger"].get("suppressed_count"),
            "suppression_ledger_warning_count": data["suppression_ledger"].get("warning_count"),
            "attestation_artifact_count": data["attestation"].get("artifact_count"),
            "audit_score": _dig(data["audit"], ["score", "total"]),
        },
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
        "interpretation": {
            "purpose": "Detect drift between PNVA public evidence reports, manifest metadata, attestation and audit summaries.",
            "sovereignty": "A PNVA release is stronger when independent reports agree on event counts, suppression, authority, graph coverage, hashes and classifications.",
            "boundary": "This guard checks semantic consistency of the public evidence package; it does not replace runtime execution tests.",
        },
        "recommendations": [
            "Run this guard after regenerating reports and before publishing checksums.",
            "Treat any semantic mismatch as a release-blocking error unless explicitly documented.",
            "Keep this guard outside the evidence attestation hash seed because it consumes the attestation.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate semantic consistency across PNVA public evidence reports.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
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
