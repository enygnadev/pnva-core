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
    "decision_trace_index": "reports/pnva-decision-trace-index-2026-05-05.json",
    "heuristic_influence_map": "reports/pnva-heuristic-influence-map-2026-05-05.json",
    "entity_no_tick_matrix": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
    "suppression_ledger": "reports/pnva-suppression-ledger-2026-05-05.json",
    "sovereign_robustness_gate": "reports/pnva-sovereign-robustness-gate-2026-05-05.json",
    "r3_migration_plan": "reports/pnva-r3-migration-plan-2026-05-05.json",
    "authority_migration_ledger": "reports/pnva-authority-migration-ledger-2026-05-05.json",
    "r3_authority_projection": "reports/pnva-r3-authority-projection-summary-2026-05-05.json",
    "r3_authority_projection_replay": "reports/pnva-r3-authority-projection-replay-2026-05-05.json",
    "r3_authority_projection_policy": "reports/pnva-r3-authority-projection-policy-2026-05-05.json",
    "r3_authority_projection_no_tick": "reports/pnva-r3-authority-projection-no-tick-2026-05-05.json",
    "r3_cutover_gate": "reports/pnva-r3-cutover-gate-2026-05-05.json",
    "r3_runtime_capture_matrix": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
    "r3_runtime_evidence_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "r3_runtime_instrumentation_plan": "reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json",
    "r3_runtime_contract_validation": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
    "sovereign_evolution_ledger": "reports/pnva-sovereign-evolution-ledger-2026-05-05.json",
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
    "decision_trace_index": "DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS",
    "heuristic_influence_map": "HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS",
    "entity_no_tick_matrix": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
    "suppression_ledger": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
    "sovereign_robustness_gate": "SOVEREIGN_ROBUSTNESS_GATE_READY_WITH_LEGACY_WARNINGS",
    "r3_migration_plan": "R3_MIGRATION_PLAN_READY",
    "authority_migration_ledger": "AUTHORITY_MIGRATION_LEDGER_READY_WITH_LEGACY_WARNINGS",
    "r3_authority_projection": "R3_AUTHORITY_PROJECTION_READY",
    "r3_authority_projection_replay": "REPLAY_VALID",
    "r3_authority_projection_policy": "SOVEREIGN_POLICY_READY",
    "r3_authority_projection_no_tick": "SOVEREIGN_NO_TICK_READY",
    "r3_cutover_gate": "R3_CUTOVER_APPROVED",
    "r3_runtime_capture_matrix": "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE",
    "r3_runtime_evidence_guard": "R3_RUNTIME_EVIDENCE_ACCEPTED",
    "r3_runtime_instrumentation_plan": "R3_RUNTIME_INSTRUMENTATION_PLAN_READY",
    "r3_runtime_contract_validation": "R3_RUNTIME_CONTRACT_VALIDATED_READY",
    "sovereign_evolution_ledger": "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY",
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
    check_error(group="manifest", name="manifest_decision_trace_event_count", left_ref="MANIFEST:decision_trace_index.event_count", left=_dig(manifest_summary, ["decision_trace_index", "event_count"]), right_ref="decision_trace_index:event_count", right=data["decision_trace_index"].get("event_count"))
    check_error(group="manifest", name="manifest_decision_trace_trace_coverage", left_ref="MANIFEST:decision_trace_index.trace_coverage_ratio", left=_dig(manifest_summary, ["decision_trace_index", "trace_coverage_ratio"]), right_ref="decision_trace_index:trace_coverage_ratio", right=data["decision_trace_index"].get("trace_coverage_ratio"), tolerance=0.000001)
    check_error(group="manifest", name="manifest_decision_trace_warning_count", left_ref="MANIFEST:decision_trace_index.warning_count", left=_dig(manifest_summary, ["decision_trace_index", "warning_count"]), right_ref="decision_trace_index:warning_count", right=data["decision_trace_index"].get("warning_count"))
    check_error(group="manifest", name="manifest_decision_trace_native_clean", left_ref="MANIFEST:decision_trace_index.native_trace_clean", left=_dig(manifest_summary, ["decision_trace_index", "native_trace_clean"]), right_ref="decision_trace_index:native_trace_clean", right=data["decision_trace_index"].get("native_trace_clean"))
    check_error(group="manifest", name="manifest_heuristic_influence_event_count", left_ref="MANIFEST:heuristic_influence_map.event_count", left=_dig(manifest_summary, ["heuristic_influence_map", "event_count"]), right_ref="heuristic_influence_map:event_count", right=data["heuristic_influence_map"].get("event_count"))
    check_error(group="manifest", name="manifest_heuristic_influence_rule_count", left_ref="MANIFEST:heuristic_influence_map.heuristic_rule_count", left=_dig(manifest_summary, ["heuristic_influence_map", "heuristic_rule_count"]), right_ref="heuristic_influence_map:heuristic_rule_count", right=data["heuristic_influence_map"].get("heuristic_rule_count"))
    check_error(group="manifest", name="manifest_heuristic_influence_edge_count", left_ref="MANIFEST:heuristic_influence_map.influence_edge_count", left=_dig(manifest_summary, ["heuristic_influence_map", "influence_edge_count"]), right_ref="heuristic_influence_map:influence_edge_count", right=data["heuristic_influence_map"].get("influence_edge_count"))
    check_error(group="manifest", name="manifest_heuristic_influence_warning_count", left_ref="MANIFEST:heuristic_influence_map.warning_count", left=_dig(manifest_summary, ["heuristic_influence_map", "warning_count"]), right_ref="heuristic_influence_map:warning_count", right=data["heuristic_influence_map"].get("warning_count"))
    check_error(group="manifest", name="manifest_heuristic_influence_native_clean", left_ref="MANIFEST:heuristic_influence_map.native_influence_clean", left=_dig(manifest_summary, ["heuristic_influence_map", "native_influence_clean"]), right_ref="heuristic_influence_map:native_influence_clean", right=data["heuristic_influence_map"].get("native_influence_clean"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_event_count", left_ref="MANIFEST:entity_no_tick_matrix.event_count", left=_dig(manifest_summary, ["entity_no_tick_matrix", "event_count"]), right_ref="entity_no_tick_matrix:event_count", right=data["entity_no_tick_matrix"].get("event_count"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_suppressed_count", left_ref="MANIFEST:entity_no_tick_matrix.suppressed_count", left=_dig(manifest_summary, ["entity_no_tick_matrix", "suppressed_count"]), right_ref="entity_no_tick_matrix:suppressed_count", right=data["entity_no_tick_matrix"].get("suppressed_count"))
    check_error(group="manifest", name="manifest_entity_no_tick_matrix_native_clean", left_ref="MANIFEST:entity_no_tick_matrix.native_matrix_clean", left=_dig(manifest_summary, ["entity_no_tick_matrix", "native_matrix_clean"]), right_ref="entity_no_tick_matrix:native_matrix_clean", right=data["entity_no_tick_matrix"].get("native_matrix_clean"))
    check_error(group="manifest", name="manifest_suppression_ledger_event_count", left_ref="MANIFEST:suppression_ledger.event_count", left=_dig(manifest_summary, ["suppression_ledger", "event_count"]), right_ref="suppression_ledger:event_count", right=data["suppression_ledger"].get("event_count"))
    check_error(group="manifest", name="manifest_suppression_ledger_suppressed_count", left_ref="MANIFEST:suppression_ledger.suppressed_count", left=_dig(manifest_summary, ["suppression_ledger", "suppressed_count"]), right_ref="suppression_ledger:suppressed_count", right=data["suppression_ledger"].get("suppressed_count"))
    check_error(group="manifest", name="manifest_suppression_ledger_native_clean", left_ref="MANIFEST:suppression_ledger.native_suppression_clean", left=_dig(manifest_summary, ["suppression_ledger", "native_suppression_clean"]), right_ref="suppression_ledger:native_suppression_clean", right=data["suppression_ledger"].get("native_suppression_clean"))
    check_error(group="manifest", name="manifest_robustness_score", left_ref="MANIFEST:sovereign_robustness_gate.robustness_score", left=_dig(manifest_summary, ["sovereign_robustness_gate", "robustness_score"]), right_ref="sovereign_robustness_gate:robustness_score", right=data["sovereign_robustness_gate"].get("robustness_score"))
    check_error(group="manifest", name="manifest_robustness_event_count", left_ref="MANIFEST:sovereign_robustness_gate.event_count", left=_dig(manifest_summary, ["sovereign_robustness_gate", "event_count"]), right_ref="sovereign_robustness_gate:event_count", right=data["sovereign_robustness_gate"].get("event_count"))
    check_error(group="manifest", name="manifest_robustness_suppressed_count", left_ref="MANIFEST:sovereign_robustness_gate.suppressed_count", left=_dig(manifest_summary, ["sovereign_robustness_gate", "suppressed_count"]), right_ref="sovereign_robustness_gate:suppressed_count", right=data["sovereign_robustness_gate"].get("suppressed_count"))
    check_error(group="manifest", name="manifest_robustness_native_clean_count", left_ref="MANIFEST:sovereign_robustness_gate.native_clean_signal_count", left=_dig(manifest_summary, ["sovereign_robustness_gate", "native_clean_signal_count"]), right_ref="sovereign_robustness_gate:native_clean_signal_count", right=data["sovereign_robustness_gate"].get("native_clean_signal_count"))
    check_error(group="manifest", name="manifest_robustness_legacy_debt_count", left_ref="MANIFEST:sovereign_robustness_gate.legacy_debt_count", left=_dig(manifest_summary, ["sovereign_robustness_gate", "legacy_debt_count"]), right_ref="sovereign_robustness_gate:legacy_debt_count", right=data["sovereign_robustness_gate"].get("legacy_debt_count"))
    check_error(group="manifest", name="manifest_r3_current_score", left_ref="MANIFEST:r3_migration_plan.current_robustness_score", left=_dig(manifest_summary, ["r3_migration_plan", "current_robustness_score"]), right_ref="r3_migration_plan:current_robustness_score", right=data["r3_migration_plan"].get("current_robustness_score"))
    check_error(group="manifest", name="manifest_r3_primary_debt", left_ref="MANIFEST:r3_migration_plan.primary_blocking_debt_count", left=_dig(manifest_summary, ["r3_migration_plan", "primary_blocking_debt_count"]), right_ref="r3_migration_plan:primary_blocking_debt_count", right=data["r3_migration_plan"].get("primary_blocking_debt_count"))
    check_error(group="manifest", name="manifest_r3_action_count", left_ref="MANIFEST:r3_migration_plan.migration_action_count", left=_dig(manifest_summary, ["r3_migration_plan", "migration_action_count"]), right_ref="r3_migration_plan:migration_action_count", right=data["r3_migration_plan"].get("migration_action_count"))
    check_error(group="manifest", name="manifest_r3_raw_signal_count", left_ref="MANIFEST:r3_migration_plan.raw_migration_signal_count", left=_dig(manifest_summary, ["r3_migration_plan", "raw_migration_signal_count"]), right_ref="r3_migration_plan:raw_migration_signal_count", right=data["r3_migration_plan"].get("raw_migration_signal_count"))
    check_error(group="manifest", name="manifest_authority_migration_candidate_count", left_ref="MANIFEST:authority_migration_ledger.candidate_event_count", left=_dig(manifest_summary, ["authority_migration_ledger", "candidate_event_count"]), right_ref="authority_migration_ledger:candidate_event_count", right=data["authority_migration_ledger"].get("candidate_event_count"))
    check_error(group="manifest", name="manifest_authority_migration_entity_count", left_ref="MANIFEST:authority_migration_ledger.entity_candidate_count", left=_dig(manifest_summary, ["authority_migration_ledger", "entity_candidate_count"]), right_ref="authority_migration_ledger:entity_candidate_count", right=data["authority_migration_ledger"].get("entity_candidate_count"))
    check_error(group="manifest", name="manifest_authority_migration_coverage", left_ref="MANIFEST:authority_migration_ledger.migration_coverage_ratio", left=_dig(manifest_summary, ["authority_migration_ledger", "migration_coverage_ratio"]), right_ref="authority_migration_ledger:migration_coverage_ratio", right=data["authority_migration_ledger"].get("migration_coverage_ratio"), tolerance=0.000001)
    check_error(group="manifest", name="manifest_authority_migration_native_debt", left_ref="MANIFEST:authority_migration_ledger.native_low_authority_strong_count", left=_dig(manifest_summary, ["authority_migration_ledger", "native_low_authority_strong_count"]), right_ref="authority_migration_ledger:native_low_authority_strong_count", right=data["authority_migration_ledger"].get("native_low_authority_strong_count"))
    check_error(group="manifest", name="manifest_r3_projection_event_count", left_ref="MANIFEST:r3_authority_projection.projected_event_count", left=_dig(manifest_summary, ["r3_authority_projection", "projected_event_count"]), right_ref="r3_authority_projection:projected_event_count", right=data["r3_authority_projection"].get("projected_event_count"))
    check_error(group="manifest", name="manifest_r3_projection_commit_count", left_ref="MANIFEST:r3_authority_projection.projected_commit_count", left=_dig(manifest_summary, ["r3_authority_projection", "projected_commit_count"]), right_ref="r3_authority_projection:projected_commit_count", right=data["r3_authority_projection"].get("projected_commit_count"))
    check_error(group="manifest", name="manifest_r3_projection_suppression_count", left_ref="MANIFEST:r3_authority_projection.projected_no_tick_suppression_count", left=_dig(manifest_summary, ["r3_authority_projection", "projected_no_tick_suppression_count"]), right_ref="r3_authority_projection:projected_no_tick_suppression_count", right=data["r3_authority_projection"].get("projected_no_tick_suppression_count"))
    check_error(group="manifest", name="manifest_r3_projection_low_authority_zero", left_ref="MANIFEST:r3_authority_projection.projected_low_authority_strong_count", left=_dig(manifest_summary, ["r3_authority_projection", "projected_low_authority_strong_count"]), right_ref="r3_authority_projection:projected_low_authority_strong_count", right=data["r3_authority_projection"].get("projected_low_authority_strong_count"))
    check_error(group="manifest", name="manifest_r3_cutover_contract_ready", left_ref="MANIFEST:r3_cutover_gate.contract_ready", left=_dig(manifest_summary, ["r3_cutover_gate", "contract_ready"]), right_ref="r3_cutover_gate:contract_ready", right=data["r3_cutover_gate"].get("contract_ready"))
    check_error(group="manifest", name="manifest_r3_cutover_approved", left_ref="MANIFEST:r3_cutover_gate.cutover_approved", left=_dig(manifest_summary, ["r3_cutover_gate", "cutover_approved"]), right_ref="r3_cutover_gate:cutover_approved", right=data["r3_cutover_gate"].get("cutover_approved"))
    check_error(group="manifest", name="manifest_r3_cutover_remaining_replacement", left_ref="MANIFEST:r3_cutover_gate.remaining_runtime_replacement_count", left=_dig(manifest_summary, ["r3_cutover_gate", "remaining_runtime_replacement_count"]), right_ref="r3_cutover_gate:remaining_runtime_replacement_count", right=data["r3_cutover_gate"].get("remaining_runtime_replacement_count"))
    check_error(group="manifest", name="manifest_r3_cutover_runtime_blockers", left_ref="MANIFEST:r3_cutover_gate.runtime_blocker_count", left=_dig(manifest_summary, ["r3_cutover_gate", "runtime_blocker_count"]), right_ref="r3_cutover_gate:runtime_blocker_count", right=data["r3_cutover_gate"].get("runtime_blocker_count"))
    check_error(group="manifest", name="manifest_r3_capture_contract_ready", left_ref="MANIFEST:r3_runtime_capture_matrix.capture_contract_ready", left=_dig(manifest_summary, ["r3_runtime_capture_matrix", "capture_contract_ready"]), right_ref="r3_runtime_capture_matrix:capture_contract_ready", right=data["r3_runtime_capture_matrix"].get("capture_contract_ready"))
    check_error(group="manifest", name="manifest_r3_capture_slot_count", left_ref="MANIFEST:r3_runtime_capture_matrix.capture_slot_count", left=_dig(manifest_summary, ["r3_runtime_capture_matrix", "capture_slot_count"]), right_ref="r3_runtime_capture_matrix:capture_slot_count", right=data["r3_runtime_capture_matrix"].get("capture_slot_count"))
    check_error(group="manifest", name="manifest_r3_capture_pending_slot_count", left_ref="MANIFEST:r3_runtime_capture_matrix.pending_slot_count", left=_dig(manifest_summary, ["r3_runtime_capture_matrix", "pending_slot_count"]), right_ref="r3_runtime_capture_matrix:pending_slot_count", right=data["r3_runtime_capture_matrix"].get("pending_slot_count"))
    check_error(group="manifest", name="manifest_r3_capture_required_runtime_event_count", left_ref="MANIFEST:r3_runtime_capture_matrix.required_runtime_event_count", left=_dig(manifest_summary, ["r3_runtime_capture_matrix", "required_runtime_event_count"]), right_ref="r3_runtime_capture_matrix:required_runtime_event_count", right=data["r3_runtime_capture_matrix"].get("required_runtime_event_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_ready", left_ref="MANIFEST:r3_runtime_evidence_guard.intake_guard_ready", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "intake_guard_ready"]), right_ref="r3_runtime_evidence_guard:intake_guard_ready", right=data["r3_runtime_evidence_guard"].get("intake_guard_ready"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_slot_count", left_ref="MANIFEST:r3_runtime_evidence_guard.capture_slot_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "capture_slot_count"]), right_ref="r3_runtime_evidence_guard:capture_slot_count", right=data["r3_runtime_evidence_guard"].get("capture_slot_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_required_runtime_event_count", left_ref="MANIFEST:r3_runtime_evidence_guard.required_runtime_event_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "required_runtime_event_count"]), right_ref="r3_runtime_evidence_guard:required_runtime_event_count", right=data["r3_runtime_evidence_guard"].get("required_runtime_event_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_negative_control_total", left_ref="MANIFEST:r3_runtime_evidence_guard.negative_control_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "negative_control_count"]), right_ref="r3_runtime_evidence_guard:negative_control_count", right=data["r3_runtime_evidence_guard"].get("negative_control_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_negative_control_count", left_ref="MANIFEST:r3_runtime_evidence_guard.negative_control_detected_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "negative_control_detected_count"]), right_ref="r3_runtime_evidence_guard:negative_control_detected_count", right=data["r3_runtime_evidence_guard"].get("negative_control_detected_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_positive_control_count", left_ref="MANIFEST:r3_runtime_evidence_guard.positive_control_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "positive_control_count"]), right_ref="r3_runtime_evidence_guard:positive_control_count", right=data["r3_runtime_evidence_guard"].get("positive_control_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_positive_control_passed_count", left_ref="MANIFEST:r3_runtime_evidence_guard.positive_control_passed_count", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "positive_control_passed_count"]), right_ref="r3_runtime_evidence_guard:positive_control_passed_count", right=data["r3_runtime_evidence_guard"].get("positive_control_passed_count"))
    check_error(group="manifest", name="manifest_r3_evidence_guard_positive_fixture_only", left_ref="MANIFEST:r3_runtime_evidence_guard.positive_controls_fixture_only", left=_dig(manifest_summary, ["r3_runtime_evidence_guard", "positive_controls_fixture_only"]), right_ref="r3_runtime_evidence_guard:positive_controls_fixture_only", right=data["r3_runtime_evidence_guard"].get("positive_controls_fixture_only"))
    check_error(group="manifest", name="manifest_r3_instrumentation_plan_ready", left_ref="MANIFEST:r3_runtime_instrumentation_plan.instrumentation_plan_ready", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "instrumentation_plan_ready"]), right_ref="r3_runtime_instrumentation_plan:instrumentation_plan_ready", right=data["r3_runtime_instrumentation_plan"].get("instrumentation_plan_ready"))
    check_error(group="manifest", name="manifest_r3_instrumentation_action_contract_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.action_contract_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "action_contract_count"]), right_ref="r3_runtime_instrumentation_plan:action_contract_count", right=data["r3_runtime_instrumentation_plan"].get("action_contract_count"))
    check_error(group="manifest", name="manifest_r3_instrumentation_required_runtime_event_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.required_runtime_event_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "required_runtime_event_count"]), right_ref="r3_runtime_instrumentation_plan:required_runtime_event_count", right=data["r3_runtime_instrumentation_plan"].get("required_runtime_event_count"))
    check_error(group="manifest", name="manifest_r3_instrumentation_template_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.event_template_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "event_template_count"]), right_ref="r3_runtime_instrumentation_plan:event_template_count", right=data["r3_runtime_instrumentation_plan"].get("event_template_count"))
    check_error(group="manifest", name="manifest_r3_instrumentation_mandatory_field_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.mandatory_field_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "mandatory_field_count"]), right_ref="r3_runtime_instrumentation_plan:mandatory_field_count", right=data["r3_runtime_instrumentation_plan"].get("mandatory_field_count"))
    check_error(group="manifest", name="manifest_r3_instrumentation_positive_control_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.positive_control_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "positive_control_count"]), right_ref="r3_runtime_instrumentation_plan:positive_control_count", right=data["r3_runtime_instrumentation_plan"].get("positive_control_count"))
    check_error(group="manifest", name="manifest_r3_instrumentation_positive_control_passed_count", left_ref="MANIFEST:r3_runtime_instrumentation_plan.positive_control_passed_count", left=_dig(manifest_summary, ["r3_runtime_instrumentation_plan", "positive_control_passed_count"]), right_ref="r3_runtime_instrumentation_plan:positive_control_passed_count", right=data["r3_runtime_instrumentation_plan"].get("positive_control_passed_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_ready", left_ref="MANIFEST:r3_runtime_contract_validation.contract_validation_ready", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "contract_validation_ready"]), right_ref="r3_runtime_contract_validation:contract_validation_ready", right=data["r3_runtime_contract_validation"].get("contract_validation_ready"))
    check_error(group="manifest", name="manifest_r3_contract_validation_check_count", left_ref="MANIFEST:r3_runtime_contract_validation.contract_check_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "contract_check_count"]), right_ref="r3_runtime_contract_validation:contract_check_count", right=data["r3_runtime_contract_validation"].get("contract_check_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_failure_count", left_ref="MANIFEST:r3_runtime_contract_validation.failure_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "failure_count"]), right_ref="r3_runtime_contract_validation:failure_count", right=data["r3_runtime_contract_validation"].get("failure_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_mandatory_field_count", left_ref="MANIFEST:r3_runtime_contract_validation.mandatory_field_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "mandatory_field_count"]), right_ref="r3_runtime_contract_validation:mandatory_field_count", right=data["r3_runtime_contract_validation"].get("mandatory_field_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_enforced_control_count", left_ref="MANIFEST:r3_runtime_contract_validation.enforced_control_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "enforced_control_count"]), right_ref="r3_runtime_contract_validation:enforced_control_count", right=data["r3_runtime_contract_validation"].get("enforced_control_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_positive_control_count", left_ref="MANIFEST:r3_runtime_contract_validation.positive_control_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "positive_control_count"]), right_ref="r3_runtime_contract_validation:positive_control_count", right=data["r3_runtime_contract_validation"].get("positive_control_count"))
    check_error(group="manifest", name="manifest_r3_contract_validation_positive_control_passed_count", left_ref="MANIFEST:r3_runtime_contract_validation.positive_control_passed_count", left=_dig(manifest_summary, ["r3_runtime_contract_validation", "positive_control_passed_count"]), right_ref="r3_runtime_contract_validation:positive_control_passed_count", right=data["r3_runtime_contract_validation"].get("positive_control_passed_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_score", left_ref="MANIFEST:sovereign_evolution_ledger.sovereign_evolution_score", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "sovereign_evolution_score"]), right_ref="sovereign_evolution_ledger:sovereign_evolution_score", right=data["sovereign_evolution_ledger"].get("sovereign_evolution_score"), tolerance=0.000001)
    check_error(group="manifest", name="manifest_sovereign_evolution_runtime_pending", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_pending_slot_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_pending_slot_count"]), right_ref="sovereign_evolution_ledger:runtime_pending_slot_count", right=data["sovereign_evolution_ledger"].get("runtime_pending_slot_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_required_events", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_required_event_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_required_event_count"]), right_ref="sovereign_evolution_ledger:runtime_required_event_count", right=data["sovereign_evolution_ledger"].get("runtime_required_event_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_contract_checks", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_contract_check_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_contract_check_count"]), right_ref="sovereign_evolution_ledger:runtime_contract_check_count", right=data["sovereign_evolution_ledger"].get("runtime_contract_check_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_positive_controls", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_positive_control_passed_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_positive_control_passed_count"]), right_ref="sovereign_evolution_ledger:runtime_positive_control_passed_count", right=data["sovereign_evolution_ledger"].get("runtime_positive_control_passed_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_mandatory_fields", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_mandatory_field_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_mandatory_field_count"]), right_ref="sovereign_evolution_ledger:runtime_mandatory_field_count", right=data["sovereign_evolution_ledger"].get("runtime_mandatory_field_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_enforced_controls", left_ref="MANIFEST:sovereign_evolution_ledger.runtime_enforced_control_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "runtime_enforced_control_count"]), right_ref="sovereign_evolution_ledger:runtime_enforced_control_count", right=data["sovereign_evolution_ledger"].get("runtime_enforced_control_count"))
    check_error(group="manifest", name="manifest_sovereign_evolution_blockers", left_ref="MANIFEST:sovereign_evolution_ledger.blocker_count", left=_dig(manifest_summary, ["sovereign_evolution_ledger", "blocker_count"]), right_ref="sovereign_evolution_ledger:blocker_count", right=data["sovereign_evolution_ledger"].get("blocker_count"))

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
    check_error(group="decision_trace_index", name="decision_trace_total_event_count", left_ref="decision_trace_index:event_count", left=data["decision_trace_index"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="decision_trace_index", name="decision_trace_traced_count", left_ref="decision_trace_index:traced_event_count", left=data["decision_trace_index"].get("traced_event_count"), right_ref="decision_trace_index:event_count", right=data["decision_trace_index"].get("event_count"))
    check_error(group="decision_trace_index", name="decision_trace_trace_coverage", left_ref="decision_trace_index:trace_coverage_ratio", left=data["decision_trace_index"].get("trace_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="decision_trace_index", name="decision_trace_entity_coverage", left_ref="decision_trace_index:entity_coverage_ratio", left=data["decision_trace_index"].get("entity_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="decision_trace_index", name="decision_trace_proof_coverage", left_ref="decision_trace_index:proof_coverage_ratio", left=data["decision_trace_index"].get("proof_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="decision_trace_index", name="decision_trace_heuristic_coverage", left_ref="decision_trace_index:heuristic_coverage_ratio", left=data["decision_trace_index"].get("heuristic_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="decision_trace_index", name="decision_trace_native_clean", left_ref="decision_trace_index:native_trace_clean", left=data["decision_trace_index"].get("native_trace_clean"), right_ref="expected", right=True)
    check_error(group="heuristic_influence_map", name="heuristic_influence_total_event_count", left_ref="heuristic_influence_map:event_count", left=data["heuristic_influence_map"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="heuristic_influence_map", name="heuristic_influence_rule_count_matches_schema", left_ref="heuristic_influence_map:heuristic_rule_count", left=data["heuristic_influence_map"].get("heuristic_rule_count"), right_ref="schema_contract:heuristic_rule_count", right=data["schema_contract"].get("heuristic_rule_count"))
    check_error(group="heuristic_influence_map", name="heuristic_influence_coverage", left_ref="heuristic_influence_map:heuristic_coverage_ratio", left=data["heuristic_influence_map"].get("heuristic_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="heuristic_influence_map", name="heuristic_influence_proof_coverage", left_ref="heuristic_influence_map:proof_event_coverage_ratio", left=data["heuristic_influence_map"].get("proof_event_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="heuristic_influence_map", name="heuristic_influence_native_clean", left_ref="heuristic_influence_map:native_influence_clean", left=data["heuristic_influence_map"].get("native_influence_clean"), right_ref="expected", right=True)
    check_error(group="heuristic_influence_map", name="heuristic_influence_edges_present", left_ref="heuristic_influence_map:influence_edge_count", left=int(data["heuristic_influence_map"].get("influence_edge_count", 0)) > 0, right_ref="expected", right=True)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_total_event_count", left_ref="entity_no_tick_matrix:event_count", left=data["entity_no_tick_matrix"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_total_suppressed_count", left_ref="entity_no_tick_matrix:suppressed_count", left=data["entity_no_tick_matrix"].get("suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="entity_no_tick_matrix", name="entity_matrix_native_clean", left_ref="entity_no_tick_matrix:native_matrix_clean", left=data["entity_no_tick_matrix"].get("native_matrix_clean"), right_ref="expected", right=True)
    check_error(group="suppression_ledger", name="suppression_ledger_total_event_count", left_ref="suppression_ledger:event_count", left=data["suppression_ledger"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="suppression_ledger", name="suppression_ledger_total_suppressed_count", left_ref="suppression_ledger:suppressed_count", left=data["suppression_ledger"].get("suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="suppression_ledger", name="suppression_ledger_avoided_matches_suppressed", left_ref="suppression_ledger:estimated_avoided_execution_count", left=data["suppression_ledger"].get("estimated_avoided_execution_count"), right_ref="suppression_ledger:suppressed_count", right=data["suppression_ledger"].get("suppressed_count"))
    check_error(group="suppression_ledger", name="suppression_ledger_native_clean", left_ref="suppression_ledger:native_suppression_clean", left=data["suppression_ledger"].get("native_suppression_clean"), right_ref="expected", right=True)
    check_error(group="sovereign_robustness_gate", name="robustness_total_event_count", left_ref="sovereign_robustness_gate:event_count", left=data["sovereign_robustness_gate"].get("event_count"), right_ref="canonical_events+native_events", right=total_events)
    check_error(group="sovereign_robustness_gate", name="robustness_total_suppressed_count", left_ref="sovereign_robustness_gate:suppressed_count", left=data["sovereign_robustness_gate"].get("suppressed_count"), right_ref="canonical_suppressed+native_suppressed", right=total_suppressed)
    check_error(group="sovereign_robustness_gate", name="robustness_suppression_ratio", left_ref="sovereign_robustness_gate:no_tick_suppression_ratio", left=data["sovereign_robustness_gate"].get("no_tick_suppression_ratio"), right_ref="total_suppressed/total_events", right=_ratio(total_suppressed, total_events), tolerance=0.000001)
    check_error(group="sovereign_robustness_gate", name="robustness_native_all_clean", left_ref="sovereign_robustness_gate:native_clean_signal_count", left=data["sovereign_robustness_gate"].get("native_clean_signal_count"), right_ref="sovereign_robustness_gate:native_clean_signal_total", right=data["sovereign_robustness_gate"].get("native_clean_signal_total"))
    check_error(group="sovereign_robustness_gate", name="robustness_legacy_debt_matches_maturity", left_ref="sovereign_robustness_gate:legacy_debt_count", left=data["sovereign_robustness_gate"].get("legacy_debt_count"), right_ref="maturity:canonical_low_authority_legacy_count", right=_dig(data["maturity"], ["summary", "canonical_low_authority_legacy_count"]))
    check_error(group="sovereign_robustness_gate", name="robustness_blocker_count_zero", left_ref="sovereign_robustness_gate:blocker_count", left=data["sovereign_robustness_gate"].get("blocker_count"), right_ref="expected", right=0)
    check_error(group="sovereign_robustness_gate", name="robustness_score_expected", left_ref="sovereign_robustness_gate:robustness_score", left=data["sovereign_robustness_gate"].get("robustness_score"), right_ref="expected", right=97)
    check_error(group="r3_migration_plan", name="r3_source_event_count", left_ref="r3_migration_plan:source_event_count", left=data["r3_migration_plan"].get("source_event_count"), right_ref="sovereign_robustness_gate:event_count", right=data["sovereign_robustness_gate"].get("event_count"))
    check_error(group="r3_migration_plan", name="r3_current_score_matches_robustness", left_ref="r3_migration_plan:current_robustness_score", left=data["r3_migration_plan"].get("current_robustness_score"), right_ref="sovereign_robustness_gate:robustness_score", right=data["sovereign_robustness_gate"].get("robustness_score"))
    check_error(group="r3_migration_plan", name="r3_primary_debt_matches_robustness", left_ref="r3_migration_plan:primary_blocking_debt_count", left=data["r3_migration_plan"].get("primary_blocking_debt_count"), right_ref="sovereign_robustness_gate:legacy_debt_count", right=data["sovereign_robustness_gate"].get("legacy_debt_count"))
    check_error(group="r3_migration_plan", name="r3_native_clean_count_matches_robustness", left_ref="r3_migration_plan:native_clean_signal_count", left=data["r3_migration_plan"].get("native_clean_signal_count"), right_ref="sovereign_robustness_gate:native_clean_signal_count", right=data["sovereign_robustness_gate"].get("native_clean_signal_count"))
    check_error(group="r3_migration_plan", name="r3_action_count_expected", left_ref="r3_migration_plan:migration_action_count", left=data["r3_migration_plan"].get("migration_action_count"), right_ref="expected", right=6)
    check_error(group="r3_migration_plan", name="r3_not_candidate_while_debt_exists", left_ref="r3_migration_plan:estimated_r3_candidate", left=data["r3_migration_plan"].get("estimated_r3_candidate"), right_ref="expected", right=False)
    check_error(group="authority_migration_ledger", name="authority_candidate_matches_r3", left_ref="authority_migration_ledger:candidate_event_count", left=data["authority_migration_ledger"].get("candidate_event_count"), right_ref="r3_migration_plan:primary_blocking_debt_count", right=data["r3_migration_plan"].get("primary_blocking_debt_count"))
    check_error(group="authority_migration_ledger", name="authority_candidate_matches_policy", left_ref="authority_migration_ledger:candidate_event_count", left=data["authority_migration_ledger"].get("candidate_event_count"), right_ref="policy:summary.low_authority_legacy_count", right=_dig(data["policy"], ["summary", "low_authority_legacy_count"]))
    check_error(group="authority_migration_ledger", name="authority_candidate_matches_influence", left_ref="authority_migration_ledger:candidate_event_count", left=data["authority_migration_ledger"].get("candidate_event_count"), right_ref="heuristic_influence_map:uncompensated_low_authority_strong_event_count", right=data["heuristic_influence_map"].get("uncompensated_low_authority_strong_event_count"))
    check_error(group="authority_migration_ledger", name="authority_native_debt_zero", left_ref="authority_migration_ledger:native_low_authority_strong_count", left=data["authority_migration_ledger"].get("native_low_authority_strong_count"), right_ref="expected", right=0)
    check_error(group="authority_migration_ledger", name="authority_migration_full_coverage", left_ref="authority_migration_ledger:migration_coverage_ratio", left=data["authority_migration_ledger"].get("migration_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="authority_migration_ledger", name="authority_proof_full_coverage", left_ref="authority_migration_ledger:proof_coverage_ratio", left=data["authority_migration_ledger"].get("proof_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="authority_migration_ledger", name="authority_unmapped_zero", left_ref="authority_migration_ledger:unmapped_candidate_count", left=data["authority_migration_ledger"].get("unmapped_candidate_count"), right_ref="expected", right=0)
    check_error(group="r3_authority_projection", name="projection_source_matches_authority_ledger", left_ref="r3_authority_projection:source_candidate_count", left=data["r3_authority_projection"].get("source_candidate_count"), right_ref="authority_migration_ledger:candidate_event_count", right=data["authority_migration_ledger"].get("candidate_event_count"))
    check_error(group="r3_authority_projection", name="projection_commit_matches_authority_ledger", left_ref="r3_authority_projection:projected_commit_count", left=data["r3_authority_projection"].get("projected_commit_count"), right_ref="authority_migration_ledger:candidate_event_count", right=data["authority_migration_ledger"].get("candidate_event_count"))
    check_error(group="r3_authority_projection", name="projection_event_count_is_precheck_plus_commit", left_ref="r3_authority_projection:projected_event_count", left=data["r3_authority_projection"].get("projected_event_count"), right_ref="precheck+commit", right=int(data["r3_authority_projection"].get("projected_precheck_count", 0)) + int(data["r3_authority_projection"].get("projected_commit_count", 0)))
    check_error(group="r3_authority_projection", name="projection_low_authority_strong_zero", left_ref="r3_authority_projection:projected_low_authority_strong_count", left=data["r3_authority_projection"].get("projected_low_authority_strong_count"), right_ref="expected", right=0)
    check_error(group="r3_authority_projection", name="projection_proof_full_coverage", left_ref="r3_authority_projection:proof_coverage_ratio", left=data["r3_authority_projection"].get("proof_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="r3_authority_projection", name="projection_replay_event_count_matches", left_ref="r3_authority_projection_replay:summary.event_count", left=_dig(data["r3_authority_projection_replay"], ["summary", "event_count"]), right_ref="r3_authority_projection:projected_event_count", right=data["r3_authority_projection"].get("projected_event_count"))
    check_error(group="r3_authority_projection", name="projection_policy_strong_matches_commit", left_ref="r3_authority_projection_policy:summary.strong_decision_count", left=_dig(data["r3_authority_projection_policy"], ["summary", "strong_decision_count"]), right_ref="r3_authority_projection:projected_commit_count", right=data["r3_authority_projection"].get("projected_commit_count"))
    check_error(group="r3_authority_projection", name="projection_policy_low_authority_zero", left_ref="r3_authority_projection_policy:summary.low_authority_legacy_count", left=_dig(data["r3_authority_projection_policy"], ["summary", "low_authority_legacy_count"]), right_ref="expected", right=0)
    check_error(group="r3_authority_projection", name="projection_no_tick_event_count_matches", left_ref="r3_authority_projection_no_tick:summary.event_count", left=_dig(data["r3_authority_projection_no_tick"], ["summary", "event_count"]), right_ref="r3_authority_projection:projected_event_count", right=data["r3_authority_projection"].get("projected_event_count"))
    check_error(group="r3_authority_projection", name="projection_no_tick_suppression_matches_precheck", left_ref="r3_authority_projection_no_tick:no_tick_efficiency.suppressed_count", left=_dig(data["r3_authority_projection_no_tick"], ["no_tick_efficiency", "suppressed_count"]), right_ref="r3_authority_projection:projected_precheck_count", right=data["r3_authority_projection"].get("projected_precheck_count"))
    check_error(group="r3_cutover_gate", name="cutover_authority_candidates_match_ledger", left_ref="r3_cutover_gate:authority_candidate_count", left=data["r3_cutover_gate"].get("authority_candidate_count"), right_ref="authority_migration_ledger:candidate_event_count", right=data["authority_migration_ledger"].get("candidate_event_count"))
    check_error(group="r3_cutover_gate", name="cutover_projected_commit_matches_projection", left_ref="r3_cutover_gate:projected_commit_count", left=data["r3_cutover_gate"].get("projected_commit_count"), right_ref="r3_authority_projection:projected_commit_count", right=data["r3_authority_projection"].get("projected_commit_count"))
    check_error(group="r3_cutover_gate", name="cutover_contract_ready_true", left_ref="r3_cutover_gate:contract_ready", left=data["r3_cutover_gate"].get("contract_ready"), right_ref="expected", right=True)
    check_error(group="r3_cutover_gate", name="cutover_approved_after_runtime", left_ref="r3_cutover_gate:cutover_approved", left=data["r3_cutover_gate"].get("cutover_approved"), right_ref="expected", right=True)
    check_error(group="r3_cutover_gate", name="cutover_legacy_free_claim_allowed", left_ref="r3_cutover_gate:legacy_free_claim_allowed", left=data["r3_cutover_gate"].get("legacy_free_claim_allowed"), right_ref="expected", right=True)
    check_error(group="r3_cutover_gate", name="cutover_remaining_runtime_zero", left_ref="r3_cutover_gate:remaining_runtime_replacement_count", left=data["r3_cutover_gate"].get("remaining_runtime_replacement_count"), right_ref="expected", right=0)
    check_error(group="r3_cutover_gate", name="cutover_preconditions_clean", left_ref="r3_cutover_gate:precondition_failure_count", left=data["r3_cutover_gate"].get("precondition_failure_count"), right_ref="expected", right=0)
    check_error(group="r3_runtime_capture_matrix", name="capture_slots_match_authority_candidates", left_ref="r3_runtime_capture_matrix:capture_slot_count", left=data["r3_runtime_capture_matrix"].get("capture_slot_count"), right_ref="authority_migration_ledger:candidate_event_count", right=data["authority_migration_ledger"].get("candidate_event_count"))
    check_error(group="r3_runtime_capture_matrix", name="capture_pending_matches_cutover_remaining", left_ref="r3_runtime_capture_matrix:pending_slot_count", left=data["r3_runtime_capture_matrix"].get("pending_slot_count"), right_ref="r3_cutover_gate:remaining_runtime_replacement_count", right=data["r3_cutover_gate"].get("remaining_runtime_replacement_count"))
    check_error(group="r3_runtime_capture_matrix", name="capture_contract_ready_true", left_ref="r3_runtime_capture_matrix:capture_contract_ready", left=data["r3_runtime_capture_matrix"].get("capture_contract_ready"), right_ref="expected", right=True)
    check_error(group="r3_runtime_capture_matrix", name="capture_complete_with_runtime", left_ref="r3_runtime_capture_matrix:runtime_capture_complete", left=data["r3_runtime_capture_matrix"].get("runtime_capture_complete"), right_ref="expected", right=True)
    check_error(group="r3_runtime_capture_matrix", name="capture_projection_pair_full_coverage", left_ref="r3_runtime_capture_matrix:projection_pair_coverage_ratio", left=data["r3_runtime_capture_matrix"].get("projection_pair_coverage_ratio"), right_ref="expected", right=1.0, tolerance=0.000001)
    check_error(group="r3_runtime_capture_matrix", name="capture_required_events_are_slot_pairs", left_ref="r3_runtime_capture_matrix:required_runtime_event_count", left=data["r3_runtime_capture_matrix"].get("required_runtime_event_count"), right_ref="capture_slot_count*2", right=int(data["r3_runtime_capture_matrix"].get("capture_slot_count", 0)) * 2)
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_matches_capture_slots", left_ref="r3_runtime_evidence_guard:capture_slot_count", left=data["r3_runtime_evidence_guard"].get("capture_slot_count"), right_ref="r3_runtime_capture_matrix:capture_slot_count", right=data["r3_runtime_capture_matrix"].get("capture_slot_count"))
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_required_events_match_matrix", left_ref="r3_runtime_evidence_guard:required_runtime_event_count", left=data["r3_runtime_evidence_guard"].get("required_runtime_event_count"), right_ref="r3_runtime_capture_matrix:required_runtime_event_count", right=data["r3_runtime_capture_matrix"].get("required_runtime_event_count"))
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_ready_true", left_ref="r3_runtime_evidence_guard:intake_guard_ready", left=data["r3_runtime_evidence_guard"].get("intake_guard_ready"), right_ref="expected", right=True)
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_runtime_present", left_ref="r3_runtime_evidence_guard:runtime_evidence_present", left=data["r3_runtime_evidence_guard"].get("runtime_evidence_present"), right_ref="expected", right=True)
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_runtime_approved", left_ref="r3_runtime_evidence_guard:runtime_evidence_approved", left=data["r3_runtime_evidence_guard"].get("runtime_evidence_approved"), right_ref="expected", right=True)
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_negative_controls_complete", left_ref="r3_runtime_evidence_guard:negative_control_detected_count", left=data["r3_runtime_evidence_guard"].get("negative_control_detected_count"), right_ref="r3_runtime_evidence_guard:negative_control_count", right=data["r3_runtime_evidence_guard"].get("negative_control_count"))
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_positive_controls_complete", left_ref="r3_runtime_evidence_guard:positive_control_passed_count", left=data["r3_runtime_evidence_guard"].get("positive_control_passed_count"), right_ref="r3_runtime_evidence_guard:positive_control_count", right=data["r3_runtime_evidence_guard"].get("positive_control_count"))
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_positive_controls_pass", left_ref="r3_runtime_evidence_guard:positive_controls_pass", left=data["r3_runtime_evidence_guard"].get("positive_controls_pass"), right_ref="expected", right=True)
    check_error(group="r3_runtime_evidence_guard", name="evidence_guard_positive_controls_fixture_only", left_ref="r3_runtime_evidence_guard:positive_controls_fixture_only", left=data["r3_runtime_evidence_guard"].get("positive_controls_fixture_only"), right_ref="expected", right=True)
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_matches_capture_slots", left_ref="r3_runtime_instrumentation_plan:capture_slot_count", left=data["r3_runtime_instrumentation_plan"].get("capture_slot_count"), right_ref="r3_runtime_capture_matrix:capture_slot_count", right=data["r3_runtime_capture_matrix"].get("capture_slot_count"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_matches_required_runtime_events", left_ref="r3_runtime_instrumentation_plan:required_runtime_event_count", left=data["r3_runtime_instrumentation_plan"].get("required_runtime_event_count"), right_ref="r3_runtime_capture_matrix:required_runtime_event_count", right=data["r3_runtime_capture_matrix"].get("required_runtime_event_count"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_uses_evidence_guard", left_ref="r3_runtime_instrumentation_plan:source_guard_classification", left=data["r3_runtime_instrumentation_plan"].get("source_guard_classification"), right_ref="r3_runtime_evidence_guard:classification", right=data["r3_runtime_evidence_guard"].get("classification"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_action_contracts_match_matrix_actions", left_ref="r3_runtime_instrumentation_plan:action_contract_count", left=data["r3_runtime_instrumentation_plan"].get("action_contract_count"), right_ref="r3_runtime_capture_matrix:action_target_count", right=data["r3_runtime_capture_matrix"].get("action_target_count"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_templates_are_pairs", left_ref="r3_runtime_instrumentation_plan:event_template_count", left=data["r3_runtime_instrumentation_plan"].get("event_template_count"), right_ref="action_contract_count*2", right=int(data["r3_runtime_instrumentation_plan"].get("action_contract_count", 0)) * 2)
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_runtime_approval_matches_guard", left_ref="r3_runtime_instrumentation_plan:runtime_evidence_approved", left=data["r3_runtime_instrumentation_plan"].get("runtime_evidence_approved"), right_ref="r3_runtime_evidence_guard:runtime_evidence_approved", right=data["r3_runtime_evidence_guard"].get("runtime_evidence_approved"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_negative_controls_match_guard", left_ref="r3_runtime_instrumentation_plan:negative_control_detected_count", left=data["r3_runtime_instrumentation_plan"].get("negative_control_detected_count"), right_ref="r3_runtime_evidence_guard:negative_control_detected_count", right=data["r3_runtime_evidence_guard"].get("negative_control_detected_count"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_positive_controls_match_guard", left_ref="r3_runtime_instrumentation_plan:positive_control_passed_count", left=data["r3_runtime_instrumentation_plan"].get("positive_control_passed_count"), right_ref="r3_runtime_evidence_guard:positive_control_passed_count", right=data["r3_runtime_evidence_guard"].get("positive_control_passed_count"))
    check_error(group="r3_runtime_instrumentation_plan", name="instrumentation_positive_controls_complete", left_ref="r3_runtime_instrumentation_plan:positive_control_passed_count", left=data["r3_runtime_instrumentation_plan"].get("positive_control_passed_count"), right_ref="r3_runtime_instrumentation_plan:positive_control_count", right=data["r3_runtime_instrumentation_plan"].get("positive_control_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_matches_matrix_slots", left_ref="r3_runtime_contract_validation:capture_slot_count", left=data["r3_runtime_contract_validation"].get("capture_slot_count"), right_ref="r3_runtime_capture_matrix:capture_slot_count", right=data["r3_runtime_capture_matrix"].get("capture_slot_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_matches_instrumentation_contracts", left_ref="r3_runtime_contract_validation:action_contract_count", left=data["r3_runtime_contract_validation"].get("action_contract_count"), right_ref="r3_runtime_instrumentation_plan:action_contract_count", right=data["r3_runtime_instrumentation_plan"].get("action_contract_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_matches_required_events", left_ref="r3_runtime_contract_validation:required_runtime_event_count", left=data["r3_runtime_contract_validation"].get("required_runtime_event_count"), right_ref="r3_runtime_instrumentation_plan:required_runtime_event_count", right=data["r3_runtime_instrumentation_plan"].get("required_runtime_event_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_matches_mandatory_fields", left_ref="r3_runtime_contract_validation:mandatory_field_count", left=data["r3_runtime_contract_validation"].get("mandatory_field_count"), right_ref="r3_runtime_instrumentation_plan:mandatory_field_count", right=data["r3_runtime_instrumentation_plan"].get("mandatory_field_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_negative_controls_match_guard", left_ref="r3_runtime_contract_validation:negative_control_detected_count", left=data["r3_runtime_contract_validation"].get("negative_control_detected_count"), right_ref="r3_runtime_evidence_guard:negative_control_detected_count", right=data["r3_runtime_evidence_guard"].get("negative_control_detected_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_positive_controls_match_guard", left_ref="r3_runtime_contract_validation:positive_control_passed_count", left=data["r3_runtime_contract_validation"].get("positive_control_passed_count"), right_ref="r3_runtime_evidence_guard:positive_control_passed_count", right=data["r3_runtime_evidence_guard"].get("positive_control_passed_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_positive_controls_complete", left_ref="r3_runtime_contract_validation:positive_control_passed_count", left=data["r3_runtime_contract_validation"].get("positive_control_passed_count"), right_ref="r3_runtime_contract_validation:positive_control_count", right=data["r3_runtime_contract_validation"].get("positive_control_count"))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_enforced_controls_match_guard", left_ref="r3_runtime_contract_validation:enforced_control_count", left=data["r3_runtime_contract_validation"].get("enforced_control_count"), right_ref="len(r3_runtime_evidence_guard.enforced_controls)", right=len(data["r3_runtime_evidence_guard"].get("enforced_controls", {})))
    check_error(group="r3_runtime_contract_validation", name="contract_validation_failure_count_zero", left_ref="r3_runtime_contract_validation:failure_count", left=data["r3_runtime_contract_validation"].get("failure_count"), right_ref="expected", right=0)
    check_error(group="r3_runtime_contract_validation", name="contract_validation_runtime_approval_matches_guard", left_ref="r3_runtime_contract_validation:runtime_evidence_approved", left=data["r3_runtime_contract_validation"].get("runtime_evidence_approved"), right_ref="r3_runtime_evidence_guard:runtime_evidence_approved", right=data["r3_runtime_evidence_guard"].get("runtime_evidence_approved"))
    check_error(group="sovereign_evolution_ledger", name="evolution_runtime_pending_matches_capture", left_ref="sovereign_evolution_ledger:runtime_pending_slot_count", left=data["sovereign_evolution_ledger"].get("runtime_pending_slot_count"), right_ref="r3_runtime_capture_matrix:pending_slot_count", right=data["r3_runtime_capture_matrix"].get("pending_slot_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_runtime_events_match_capture", left_ref="sovereign_evolution_ledger:runtime_required_event_count", left=data["sovereign_evolution_ledger"].get("runtime_required_event_count"), right_ref="r3_runtime_capture_matrix:required_runtime_event_count", right=data["r3_runtime_capture_matrix"].get("required_runtime_event_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_contract_checks_match_validator", left_ref="sovereign_evolution_ledger:runtime_contract_check_count", left=data["sovereign_evolution_ledger"].get("runtime_contract_check_count"), right_ref="r3_runtime_contract_validation:contract_check_count", right=data["r3_runtime_contract_validation"].get("contract_check_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_negative_controls_match_guard", left_ref="sovereign_evolution_ledger:runtime_negative_control_detected_count", left=data["sovereign_evolution_ledger"].get("runtime_negative_control_detected_count"), right_ref="r3_runtime_evidence_guard:negative_control_detected_count", right=data["r3_runtime_evidence_guard"].get("negative_control_detected_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_positive_controls_match_guard", left_ref="sovereign_evolution_ledger:runtime_positive_control_passed_count", left=data["sovereign_evolution_ledger"].get("runtime_positive_control_passed_count"), right_ref="r3_runtime_evidence_guard:positive_control_passed_count", right=data["r3_runtime_evidence_guard"].get("positive_control_passed_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_mandatory_fields_match_contract", left_ref="sovereign_evolution_ledger:runtime_mandatory_field_count", left=data["sovereign_evolution_ledger"].get("runtime_mandatory_field_count"), right_ref="r3_runtime_contract_validation:mandatory_field_count", right=data["r3_runtime_contract_validation"].get("mandatory_field_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_enforced_controls_match_contract", left_ref="sovereign_evolution_ledger:runtime_enforced_control_count", left=data["sovereign_evolution_ledger"].get("runtime_enforced_control_count"), right_ref="r3_runtime_contract_validation:enforced_control_count", right=data["r3_runtime_contract_validation"].get("enforced_control_count"))
    check_error(group="sovereign_evolution_ledger", name="evolution_no_tick_ratio_matches_maturity", left_ref="sovereign_evolution_ledger:aggregate_no_tick_suppression_ratio", left=data["sovereign_evolution_ledger"].get("aggregate_no_tick_suppression_ratio"), right_ref="maturity:summary.aggregate_no_tick_suppression_ratio", right=_dig(data["maturity"], ["summary", "aggregate_no_tick_suppression_ratio"]), tolerance=0.000001)
    check_error(group="sovereign_evolution_ledger", name="evolution_r3_preparation_ready", left_ref="sovereign_evolution_ledger:r3_preparation_ready", left=data["sovereign_evolution_ledger"].get("r3_preparation_ready"), right_ref="expected", right=True)
    check_error(group="sovereign_evolution_ledger", name="evolution_runtime_approved", left_ref="sovereign_evolution_ledger:r3_runtime_evidence_approved", left=data["sovereign_evolution_ledger"].get("r3_runtime_evidence_approved"), right_ref="expected", right=True)
    check_error(group="sovereign_evolution_ledger", name="evolution_priority_actions_present", left_ref="sovereign_evolution_ledger:priority_action_count", left=data["sovereign_evolution_ledger"].get("priority_action_count"), right_ref="minimum", right=4)

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
    for required_id in ("schema_contract_validation", "causal_chronology", "tension_decision_calibration", "decision_trace_index", "heuristic_influence_map", "entity_no_tick_matrix", "suppression_ledger", "sovereign_robustness_gate", "r3_migration_plan", "authority_migration_ledger", "r3_authority_projection_summary", "r3_authority_projection_events", "r3_authority_projection_entities", "r3_authority_projection_replay", "r3_authority_projection_policy", "r3_authority_projection_no_tick", "r3_cutover_gate", "r3_runtime_capture_matrix", "r3_runtime_evidence_guard", "r3_runtime_instrumentation_plan", "r3_runtime_contract_validation", "sovereign_evolution_ledger", "adversarial_validation", "entity_heuristic_maturity"):
        check_error(group="attestation", name=f"attestation_contains_{required_id}", left_ref="attestation:artifact_ids", left=required_id in artifact_ids, right_ref="expected", right=True)
    check_error(group="audit", name="audit_score_ready", left_ref="audit:score.classification", left=_dig(data["audit"], ["score", "classification"]), right_ref="expected", right="SOVEREIGN_READY")
    check_error(group="audit", name="audit_attestation_hash_matches", left_ref="audit:evidence_attestation.evidence_hash", left=_dig(data["audit"], ["evidence_attestation", "evidence_hash"]), right_ref="attestation:evidence_hash", right=data["attestation"].get("evidence_hash"))
    check_error(group="audit", name="audit_maturity_score_matches", left_ref="audit:entity_heuristic_maturity.maturity_score", left=_dig(data["audit"], ["entity_heuristic_maturity", "maturity_score"]), right_ref="maturity:maturity_score", right=data["maturity"].get("maturity_score"), tolerance=0.000001)
    check_error(group="audit", name="audit_schema_contract_matches", left_ref="audit:schema_contract.classification", left=_dig(data["audit"], ["schema_contract_validation", "classification"]), right_ref="schema_contract:classification", right=data["schema_contract"].get("classification"))
    check_error(group="audit", name="audit_chronology_matches", left_ref="audit:causal_chronology.classification", left=_dig(data["audit"], ["causal_chronology", "classification"]), right_ref="causal_chronology:classification", right=data["causal_chronology"].get("classification"))
    check_error(group="audit", name="audit_tension_decision_matches", left_ref="audit:tension_decision.classification", left=_dig(data["audit"], ["tension_decision_calibration", "classification"]), right_ref="tension_decision:classification", right=data["tension_decision"].get("classification"))
    check_error(group="audit", name="audit_decision_trace_matches", left_ref="audit:decision_trace_index.classification", left=_dig(data["audit"], ["decision_trace_index", "classification"]), right_ref="decision_trace_index:classification", right=data["decision_trace_index"].get("classification"))
    check_error(group="audit", name="audit_heuristic_influence_matches", left_ref="audit:heuristic_influence_map.classification", left=_dig(data["audit"], ["heuristic_influence_map", "classification"]), right_ref="heuristic_influence_map:classification", right=data["heuristic_influence_map"].get("classification"))
    check_error(group="audit", name="audit_entity_no_tick_matrix_matches", left_ref="audit:entity_no_tick_matrix.classification", left=_dig(data["audit"], ["entity_no_tick_matrix", "classification"]), right_ref="entity_no_tick_matrix:classification", right=data["entity_no_tick_matrix"].get("classification"))
    check_error(group="audit", name="audit_suppression_ledger_matches", left_ref="audit:suppression_ledger.classification", left=_dig(data["audit"], ["suppression_ledger", "classification"]), right_ref="suppression_ledger:classification", right=data["suppression_ledger"].get("classification"))
    check_error(group="audit", name="audit_robustness_gate_matches", left_ref="audit:sovereign_robustness_gate.classification", left=_dig(data["audit"], ["sovereign_robustness_gate", "classification"]), right_ref="sovereign_robustness_gate:classification", right=data["sovereign_robustness_gate"].get("classification"))
    check_error(group="audit", name="audit_r3_migration_plan_matches", left_ref="audit:r3_migration_plan.classification", left=_dig(data["audit"], ["r3_migration_plan", "classification"]), right_ref="r3_migration_plan:classification", right=data["r3_migration_plan"].get("classification"))
    check_error(group="audit", name="audit_authority_migration_ledger_matches", left_ref="audit:authority_migration_ledger.classification", left=_dig(data["audit"], ["authority_migration_ledger", "classification"]), right_ref="authority_migration_ledger:classification", right=data["authority_migration_ledger"].get("classification"))
    check_error(group="audit", name="audit_r3_authority_projection_matches", left_ref="audit:r3_authority_projection.classification", left=_dig(data["audit"], ["r3_authority_projection", "classification"]), right_ref="r3_authority_projection:classification", right=data["r3_authority_projection"].get("classification"))
    check_error(group="audit", name="audit_r3_cutover_gate_matches", left_ref="audit:r3_cutover_gate.classification", left=_dig(data["audit"], ["r3_cutover_gate", "classification"]), right_ref="r3_cutover_gate:classification", right=data["r3_cutover_gate"].get("classification"))
    check_error(group="audit", name="audit_r3_runtime_capture_matrix_matches", left_ref="audit:r3_runtime_capture_matrix.classification", left=_dig(data["audit"], ["r3_runtime_capture_matrix", "classification"]), right_ref="r3_runtime_capture_matrix:classification", right=data["r3_runtime_capture_matrix"].get("classification"))
    check_error(group="audit", name="audit_r3_runtime_evidence_guard_matches", left_ref="audit:r3_runtime_evidence_guard.classification", left=_dig(data["audit"], ["r3_runtime_evidence_guard", "classification"]), right_ref="r3_runtime_evidence_guard:classification", right=data["r3_runtime_evidence_guard"].get("classification"))
    check_error(group="audit", name="audit_r3_runtime_instrumentation_plan_matches", left_ref="audit:r3_runtime_instrumentation_plan.classification", left=_dig(data["audit"], ["r3_runtime_instrumentation_plan", "classification"]), right_ref="r3_runtime_instrumentation_plan:classification", right=data["r3_runtime_instrumentation_plan"].get("classification"))
    check_error(group="audit", name="audit_r3_runtime_contract_validation_matches", left_ref="audit:r3_runtime_contract_validation.classification", left=_dig(data["audit"], ["r3_runtime_contract_validation", "classification"]), right_ref="r3_runtime_contract_validation:classification", right=data["r3_runtime_contract_validation"].get("classification"))
    check_error(group="audit", name="audit_sovereign_evolution_ledger_matches", left_ref="audit:sovereign_evolution_ledger.classification", left=_dig(data["audit"], ["sovereign_evolution_ledger", "classification"]), right_ref="sovereign_evolution_ledger:classification", right=data["sovereign_evolution_ledger"].get("classification"))

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
            "decision_trace_event_count": data["decision_trace_index"].get("event_count"),
            "decision_trace_trace_coverage_ratio": data["decision_trace_index"].get("trace_coverage_ratio"),
            "decision_trace_warning_count": data["decision_trace_index"].get("warning_count"),
            "heuristic_influence_event_count": data["heuristic_influence_map"].get("event_count"),
            "heuristic_influence_edge_count": data["heuristic_influence_map"].get("influence_edge_count"),
            "heuristic_influence_warning_count": data["heuristic_influence_map"].get("warning_count"),
            "entity_no_tick_matrix_event_count": data["entity_no_tick_matrix"].get("event_count"),
            "entity_no_tick_matrix_suppressed_count": data["entity_no_tick_matrix"].get("suppressed_count"),
            "entity_no_tick_matrix_warning_count": data["entity_no_tick_matrix"].get("warning_count"),
            "suppression_ledger_event_count": data["suppression_ledger"].get("event_count"),
            "suppression_ledger_suppressed_count": data["suppression_ledger"].get("suppressed_count"),
            "suppression_ledger_warning_count": data["suppression_ledger"].get("warning_count"),
            "sovereign_robustness_score": data["sovereign_robustness_gate"].get("robustness_score"),
            "sovereign_robustness_event_count": data["sovereign_robustness_gate"].get("event_count"),
            "sovereign_robustness_suppressed_count": data["sovereign_robustness_gate"].get("suppressed_count"),
            "sovereign_robustness_legacy_debt_count": data["sovereign_robustness_gate"].get("legacy_debt_count"),
            "r3_migration_current_score": data["r3_migration_plan"].get("current_robustness_score"),
            "r3_migration_primary_debt_count": data["r3_migration_plan"].get("primary_blocking_debt_count"),
            "r3_migration_action_count": data["r3_migration_plan"].get("migration_action_count"),
            "r3_migration_raw_signal_count": data["r3_migration_plan"].get("raw_migration_signal_count"),
            "authority_migration_candidate_count": data["authority_migration_ledger"].get("candidate_event_count"),
            "authority_migration_entity_candidate_count": data["authority_migration_ledger"].get("entity_candidate_count"),
            "authority_migration_action_candidate_count": data["authority_migration_ledger"].get("action_candidate_count"),
            "authority_migration_coverage_ratio": data["authority_migration_ledger"].get("migration_coverage_ratio"),
            "r3_authority_projection_event_count": data["r3_authority_projection"].get("projected_event_count"),
            "r3_authority_projection_commit_count": data["r3_authority_projection"].get("projected_commit_count"),
            "r3_authority_projection_suppression_count": data["r3_authority_projection"].get("projected_no_tick_suppression_count"),
            "r3_authority_projection_low_authority_strong_count": data["r3_authority_projection"].get("projected_low_authority_strong_count"),
            "r3_cutover_contract_ready": data["r3_cutover_gate"].get("contract_ready"),
            "r3_cutover_approved": data["r3_cutover_gate"].get("cutover_approved"),
            "r3_cutover_remaining_runtime_replacement_count": data["r3_cutover_gate"].get("remaining_runtime_replacement_count"),
            "r3_cutover_runtime_blocker_count": data["r3_cutover_gate"].get("runtime_blocker_count"),
            "r3_runtime_capture_contract_ready": data["r3_runtime_capture_matrix"].get("capture_contract_ready"),
            "r3_runtime_capture_complete": data["r3_runtime_capture_matrix"].get("runtime_capture_complete"),
            "r3_runtime_capture_slot_count": data["r3_runtime_capture_matrix"].get("capture_slot_count"),
            "r3_runtime_capture_pending_slot_count": data["r3_runtime_capture_matrix"].get("pending_slot_count"),
            "r3_runtime_capture_required_event_count": data["r3_runtime_capture_matrix"].get("required_runtime_event_count"),
            "r3_runtime_evidence_guard_ready": data["r3_runtime_evidence_guard"].get("intake_guard_ready"),
            "r3_runtime_evidence_present": data["r3_runtime_evidence_guard"].get("runtime_evidence_present"),
            "r3_runtime_evidence_approved": data["r3_runtime_evidence_guard"].get("runtime_evidence_approved"),
            "r3_runtime_evidence_required_event_count": data["r3_runtime_evidence_guard"].get("required_runtime_event_count"),
            "r3_runtime_evidence_negative_controls": data["r3_runtime_evidence_guard"].get("negative_control_detected_count"),
            "r3_runtime_evidence_positive_controls": data["r3_runtime_evidence_guard"].get("positive_control_passed_count"),
            "r3_runtime_instrumentation_plan_ready": data["r3_runtime_instrumentation_plan"].get("instrumentation_plan_ready"),
            "r3_runtime_instrumentation_action_contract_count": data["r3_runtime_instrumentation_plan"].get("action_contract_count"),
            "r3_runtime_instrumentation_required_event_count": data["r3_runtime_instrumentation_plan"].get("required_runtime_event_count"),
            "r3_runtime_instrumentation_template_count": data["r3_runtime_instrumentation_plan"].get("event_template_count"),
            "r3_runtime_instrumentation_mandatory_field_count": data["r3_runtime_instrumentation_plan"].get("mandatory_field_count"),
            "r3_runtime_contract_validation_ready": data["r3_runtime_contract_validation"].get("contract_validation_ready"),
            "r3_runtime_contract_validation_check_count": data["r3_runtime_contract_validation"].get("contract_check_count"),
            "r3_runtime_contract_validation_enforced_control_count": data["r3_runtime_contract_validation"].get("enforced_control_count"),
            "r3_runtime_contract_validation_failure_count": data["r3_runtime_contract_validation"].get("failure_count"),
            "sovereign_evolution_score": data["sovereign_evolution_ledger"].get("sovereign_evolution_score"),
            "sovereign_evolution_runtime_pending_slot_count": data["sovereign_evolution_ledger"].get("runtime_pending_slot_count"),
            "sovereign_evolution_controlled_warning_count": data["sovereign_evolution_ledger"].get("controlled_warning_count"),
            "sovereign_evolution_blocker_count": data["sovereign_evolution_ledger"].get("blocker_count"),
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
