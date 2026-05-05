#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


CANONICAL_EVENTS = "reports/pnva-canonical-events-sample-2026-05-05.jsonl"
CANONICAL_ENTITIES = "reports/pnva-entity-catalog-2026-05-05.json"
NATIVE_EVENTS = "reports/pnva-native-events-demo-2026-05-05.jsonl"
NATIVE_ENTITIES = "reports/pnva-native-entity-catalog-demo-2026-05-05.json"

PUBLISHED_REPORTS = {
    "replay": "reports/pnva-replay-validation-2026-05-05.json",
    "native_replay": "reports/pnva-native-replay-validation-2026-05-05.json",
    "no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native_no_tick": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "native_emitter": "reports/pnva-native-emitter-summary-2026-05-05.json",
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
    "adversarial": "reports/pnva-adversarial-validation-2026-05-05.json",
    "maturity": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
    "attestation": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
    "semantic": "reports/pnva-semantic-consistency-2026-05-05.json",
}


STABLE_PATHS = {
    "replay": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "unique_event_ids"],
        ["summary", "proof_hash_ok"],
        ["summary", "proof_hash_bad"],
        ["summary", "guard_pass_ok"],
        ["summary", "guard_block_ok"],
        ["summary", "relation_count"],
    ],
    "native_replay": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "unique_event_ids"],
        ["summary", "proof_hash_ok"],
        ["summary", "proof_hash_bad"],
        ["summary", "guard_pass_ok"],
        ["summary", "guard_block_ok"],
        ["summary", "relation_count"],
    ],
    "no_tick": [
        ["classification"],
        ["pass"],
        ["no_tick_efficiency", "event_count"],
        ["no_tick_efficiency", "collapse_count"],
        ["no_tick_efficiency", "observe_count"],
        ["no_tick_efficiency", "block_count"],
        ["no_tick_efficiency", "suppressed_count"],
        ["no_tick_efficiency", "no_tick_suppression_ratio"],
        ["no_tick_efficiency", "proof_integrity_ratio"],
        ["no_tick_efficiency", "guard_consistency_ratio"],
    ],
    "native_no_tick": [
        ["classification"],
        ["pass"],
        ["no_tick_efficiency", "event_count"],
        ["no_tick_efficiency", "collapse_count"],
        ["no_tick_efficiency", "observe_count"],
        ["no_tick_efficiency", "block_count"],
        ["no_tick_efficiency", "suppressed_count"],
        ["no_tick_efficiency", "no_tick_suppression_ratio"],
        ["no_tick_efficiency", "proof_integrity_ratio"],
        ["no_tick_efficiency", "guard_consistency_ratio"],
    ],
    "native_emitter": [
        ["classification"],
        ["pass"],
        ["event_count"],
        ["entity_count"],
        ["native_event_count"],
        ["suppressed_count"],
        ["no_tick_suppression_ratio"],
    ],
    "policy": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "strong_decision_count"],
        ["summary", "low_authority_legacy_count"],
        ["summary", "entity_missing_count"],
        ["summary", "guard_policy_bad"],
        ["summary", "proof_policy_bad"],
        ["summary", "relation_policy_bad"],
    ],
    "native_policy": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "strong_decision_count"],
        ["summary", "low_authority_legacy_count"],
        ["summary", "entity_missing_count"],
        ["summary", "guard_policy_bad"],
        ["summary", "proof_policy_bad"],
        ["summary", "relation_policy_bad"],
    ],
    "proof_chain": [
        ["classification"],
        ["pass"],
        ["seal", "event_count"],
        ["seal", "unique_event_ids"],
        ["seal", "proof_bad"],
        ["seal", "final_chain_hash"],
    ],
    "native_proof_chain": [
        ["classification"],
        ["pass"],
        ["seal", "event_count"],
        ["seal", "unique_event_ids"],
        ["seal", "proof_bad"],
        ["seal", "final_chain_hash"],
    ],
    "causal_graph": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "catalog_entity_count"],
        ["summary", "observed_entity_count"],
        ["summary", "relation_edge_count"],
        ["summary", "chain_edge_count"],
        ["summary", "graph_hash"],
    ],
    "native_causal_graph": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "catalog_entity_count"],
        ["summary", "observed_entity_count"],
        ["summary", "relation_edge_count"],
        ["summary", "chain_edge_count"],
        ["summary", "graph_hash"],
    ],
    "schema_contract": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["entity_count"],
        ["relation_count"],
        ["heuristic_rule_count"],
        ["error_count"],
        ["warning_count"],
    ],
    "causal_chronology": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["chain_count"],
        ["global_backward_count"],
        ["error_count"],
        ["warning_count"],
        ["native_chronology_clean"],
    ],
    "tension_decision": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["error_count"],
        ["warning_count"],
        ["native_calibration_clean"],
        ["legacy_calibration_warning_count"],
    ],
    "decision_trace_index": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["traced_event_count"],
        ["trace_coverage_ratio"],
        ["entity_coverage_ratio"],
        ["proof_coverage_ratio"],
        ["heuristic_coverage_ratio"],
        ["warning_count"],
        ["native_trace_clean"],
    ],
    "heuristic_influence_map": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["heuristic_rule_count"],
        ["heuristic_coverage_ratio"],
        ["proof_event_coverage_ratio"],
        ["influence_edge_count"],
        ["hard_authority_edge_count"],
        ["low_authority_edge_count"],
        ["low_authority_strong_edge_count"],
        ["uncompensated_low_authority_strong_event_count"],
        ["warning_count"],
        ["native_influence_clean"],
    ],
    "entity_no_tick_matrix": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["entity_row_count"],
        ["observed_entity_row_count"],
        ["suppressed_count"],
        ["warning_count"],
        ["native_matrix_clean"],
        ["legacy_low_authority_warning_count"],
    ],
    "suppression_ledger": [
        ["classification"],
        ["pass"],
        ["scope_count"],
        ["event_count"],
        ["suppressed_count"],
        ["estimated_avoided_execution_count"],
        ["proof_coverage_ratio"],
        ["above_threshold_suppression_count"],
        ["warning_count"],
        ["native_suppression_clean"],
    ],
    "sovereign_robustness_gate": [
        ["classification"],
        ["pass"],
        ["readiness_level"],
        ["robustness_score"],
        ["max_score"],
        ["event_count"],
        ["suppressed_count"],
        ["no_tick_suppression_ratio"],
        ["native_clean_signal_count"],
        ["native_clean_signal_total"],
        ["legacy_debt_count"],
        ["blocker_count"],
        ["warning_count"],
        ["hard_authority_ratio"],
    ],
    "r3_migration_plan": [
        ["classification"],
        ["pass"],
        ["current_readiness_level"],
        ["target_readiness_level"],
        ["current_robustness_score"],
        ["target_robustness_score"],
        ["source_event_count"],
        ["native_clean_signal_count"],
        ["native_clean_signal_total"],
        ["primary_blocking_debt_count"],
        ["migration_action_count"],
        ["raw_migration_signal_count"],
        ["primary_required_remaining_count"],
        ["estimated_r3_candidate"],
        ["blocker_count"],
        ["warning_count"],
    ],
    "authority_migration_ledger": [
        ["classification"],
        ["pass"],
        ["source_event_count"],
        ["candidate_event_count"],
        ["canonical_low_authority_strong_count"],
        ["native_low_authority_strong_count"],
        ["r3_primary_blocking_debt_count"],
        ["candidate_event_count_matches_r3"],
        ["entity_candidate_count"],
        ["action_candidate_count"],
        ["event_type_candidate_count"],
        ["mapped_candidate_count"],
        ["unmapped_candidate_count"],
        ["migration_coverage_ratio"],
        ["proof_coverage_ratio"],
        ["warning_count"],
        ["error_count"],
    ],
    "r3_authority_projection": [
        ["classification"],
        ["pass"],
        ["source_candidate_count"],
        ["ledger_candidate_count"],
        ["candidate_count_matches_ledger"],
        ["projected_event_count"],
        ["projected_native_event_count"],
        ["projected_precheck_count"],
        ["projected_commit_count"],
        ["projected_strong_decision_count"],
        ["projected_low_authority_strong_count"],
        ["projected_no_tick_suppression_count"],
        ["projected_no_tick_suppression_ratio"],
        ["proof_valid_count"],
        ["proof_coverage_ratio"],
        ["entity_count"],
    ],
    "r3_authority_projection_replay": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "unique_event_ids"],
        ["summary", "proof_hash_ok"],
        ["summary", "proof_hash_bad"],
    ],
    "r3_authority_projection_policy": [
        ["classification"],
        ["pass"],
        ["summary", "event_count"],
        ["summary", "native_event_count"],
        ["summary", "strong_decision_count"],
        ["summary", "low_authority_legacy_count"],
        ["summary", "proof_policy_bad"],
        ["summary", "entity_missing_count"],
    ],
    "r3_authority_projection_no_tick": [
        ["classification"],
        ["pass"],
        ["no_tick_efficiency", "event_count"],
        ["no_tick_efficiency", "collapse_count"],
        ["no_tick_efficiency", "observe_count"],
        ["no_tick_efficiency", "suppressed_count"],
        ["no_tick_efficiency", "no_tick_suppression_ratio"],
        ["no_tick_efficiency", "proof_integrity_ratio"],
    ],
    "r3_cutover_gate": [
        ["classification"],
        ["pass"],
        ["contract_ready"],
        ["cutover_approved"],
        ["legacy_free_claim_allowed"],
        ["fresh_runtime_evidence_present"],
        ["authority_candidate_count"],
        ["projected_event_count"],
        ["projected_precheck_count"],
        ["projected_commit_count"],
        ["projected_low_authority_strong_count"],
        ["remaining_runtime_replacement_count"],
        ["runtime_replacement_coverage_ratio"],
        ["runtime_requirement_count"],
        ["runtime_blocker_count"],
        ["precondition_failure_count"],
        ["contract_score"],
    ],
    "r3_runtime_capture_matrix": [
        ["classification"],
        ["pass"],
        ["capture_contract_ready"],
        ["runtime_capture_complete"],
        ["runtime_capture_approved"],
        ["source_candidate_count"],
        ["capture_slot_count"],
        ["verified_runtime_slot_count"],
        ["pending_slot_count"],
        ["runtime_capture_coverage_ratio"],
        ["required_runtime_event_count"],
        ["required_no_tick_precheck_count"],
        ["required_collapse_commit_count"],
        ["projection_pair_count"],
        ["projection_pair_coverage_ratio"],
        ["entity_target_count"],
        ["action_target_count"],
        ["target_rule_count"],
    ],
    "r3_runtime_evidence_guard": [
        ["classification"],
        ["pass"],
        ["intake_guard_ready"],
        ["runtime_evidence_present"],
        ["runtime_evidence_approved"],
        ["runtime_acceptance_complete"],
        ["matrix_classification"],
        ["capture_slot_count"],
        ["required_runtime_event_count"],
        ["required_no_tick_precheck_count"],
        ["required_collapse_commit_count"],
        ["runtime_event_count"],
        ["accepted_slot_count"],
        ["pending_slot_count"],
        ["rejected_event_count"],
        ["negative_control_count"],
        ["negative_control_detected_count"],
        ["negative_controls_pass"],
    ],
    "r3_runtime_instrumentation_plan": [
        ["classification"],
        ["pass"],
        ["instrumentation_plan_ready"],
        ["runtime_evidence_present"],
        ["runtime_evidence_approved"],
        ["source_matrix_classification"],
        ["source_guard_classification"],
        ["capture_slot_count"],
        ["entity_target_count"],
        ["action_contract_count"],
        ["required_runtime_event_count"],
        ["required_no_tick_precheck_count"],
        ["required_collapse_commit_count"],
        ["event_template_count"],
        ["mandatory_field_count"],
        ["target_rule_count"],
        ["negative_control_count"],
        ["negative_control_detected_count"],
    ],
    "adversarial": [
        ["classification"],
        ["pass"],
        ["test_count"],
        ["detected_count"],
        ["failure_count"],
    ],
    "maturity": [
        ["classification"],
        ["pass"],
        ["maturity_score"],
        ["error_count"],
        ["warning_count"],
        ["summary", "total_event_count"],
        ["summary", "total_suppressed_count"],
        ["summary", "aggregate_no_tick_suppression_ratio"],
        ["summary", "aggregate_hard_authority_ratio"],
        ["summary", "canonical_low_authority_legacy_count"],
        ["summary", "native_low_authority_legacy_count"],
    ],
    "attestation": [
        ["classification"],
        ["pass"],
        ["artifact_count"],
        ["failure_count"],
        ["evidence_hash"],
    ],
    "semantic": [
        ["classification"],
        ["pass"],
        ["check_count"],
        ["error_count"],
        ["warning_count"],
        ["summary", "total_event_count"],
        ["summary", "total_suppressed_count"],
    ],
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dig(data: Any, path: list[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _path_label(path: list[str]) -> str:
    return ".".join(path)


def _redact(value: str) -> str:
    value = re.sub(r"/tmp/pnva-repro-[^/]+", "<TEMP>", value)
    value = re.sub(r"/tmp/tmp[^/]+", "<TEMP>", value)
    return value


def _same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=0.000001)
    return left == right


def _run(repo: Path, args: list[str], output: Path, *, write_flag: str | None = "--write") -> dict[str, Any]:
    final_args = list(args)
    if write_flag:
        final_args.extend([write_flag, str(output)])
    command = [sys.executable, *final_args]
    completed = subprocess.run(command, cwd=repo, check=False, text=True, capture_output=True)
    parsed: dict[str, Any] = {}
    parse_error = ""
    if output.exists():
        try:
            data = _read_json(output)
            if isinstance(data, dict):
                parsed = data
        except Exception as exc:
            parse_error = str(exc)
    return {
        "command": _redact(" ".join(final_args)),
        "exit_code": completed.returncode,
        "output": _redact(str(output)),
        "stdout_tail": _redact(completed.stdout[-1200:]),
        "stderr_tail": _redact(completed.stderr[-1200:]),
        "parse_error": parse_error,
        "report": parsed,
    }


def _compare_report(name: str, published: dict[str, Any], reproduced: dict[str, Any]) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    for path in STABLE_PATHS[name]:
        expected = _dig(published, path)
        observed = _dig(reproduced, path)
        comparisons.append(
            {
                "report": name,
                "field": _path_label(path),
                "pass": _same(expected, observed),
                "published": expected,
                "reproduced": observed,
            }
        )
    return comparisons


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    published = {name: _read_json(repo / rel) for name, rel in PUBLISHED_REPORTS.items()}
    commands: dict[str, dict[str, Any]] = {}
    comparisons: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="pnva-repro-") as tmp_raw:
        tmp = Path(tmp_raw)
        outputs = {
            "replay": tmp / "replay.json",
            "native_replay": tmp / "native-replay.json",
            "no_tick": tmp / "no-tick.json",
            "native_no_tick": tmp / "native-no-tick.json",
            "native_emitter": tmp / "native-emitter-summary.json",
            "native_emitter_events": tmp / "native-emitter-events.jsonl",
            "native_emitter_entities": tmp / "native-emitter-entities.json",
            "policy": tmp / "policy.json",
            "native_policy": tmp / "native-policy.json",
            "proof_chain": tmp / "proof-chain.json",
            "native_proof_chain": tmp / "native-proof-chain.json",
            "causal_graph": tmp / "causal-graph.json",
            "native_causal_graph": tmp / "native-causal-graph.json",
            "schema_contract": tmp / "schema-contract.json",
            "causal_chronology": tmp / "causal-chronology.json",
            "tension_decision": tmp / "tension-decision.json",
            "decision_trace_index": tmp / "decision-trace-index.json",
            "heuristic_influence_map": tmp / "heuristic-influence-map.json",
            "entity_no_tick_matrix": tmp / "entity-no-tick-matrix.json",
            "suppression_ledger": tmp / "suppression-ledger.json",
            "sovereign_robustness_gate": tmp / "sovereign-robustness-gate.json",
            "r3_migration_plan": tmp / "r3-migration-plan.json",
            "authority_migration_ledger": tmp / "authority-migration-ledger.json",
            "r3_authority_projection": tmp / "r3-authority-projection-summary.json",
            "r3_authority_projection_events": tmp / "r3-authority-projection-events.jsonl",
            "r3_authority_projection_entities": tmp / "r3-authority-projection-entities.json",
            "r3_authority_projection_replay": tmp / "r3-authority-projection-replay.json",
            "r3_authority_projection_policy": tmp / "r3-authority-projection-policy.json",
            "r3_authority_projection_no_tick": tmp / "r3-authority-projection-no-tick.json",
            "r3_cutover_gate": tmp / "r3-cutover-gate.json",
            "r3_runtime_capture_matrix": tmp / "r3-runtime-capture-matrix.json",
            "r3_runtime_evidence_guard": tmp / "r3-runtime-evidence-guard.json",
            "r3_runtime_instrumentation_plan": tmp / "r3-runtime-instrumentation-plan.json",
            "adversarial": tmp / "adversarial.json",
            "maturity": tmp / "maturity.json",
            "attestation": tmp / "attestation.json",
            "semantic": tmp / "semantic.json",
        }

        commands["replay"] = _run(repo, ["tools/pnva_replay_validator.py", "--events", CANONICAL_EVENTS, "--entity-catalog", CANONICAL_ENTITIES], outputs["replay"])
        commands["native_replay"] = _run(repo, ["tools/pnva_replay_validator.py", "--events", NATIVE_EVENTS, "--entity-catalog", NATIVE_ENTITIES], outputs["native_replay"])
        commands["no_tick"] = _run(repo, ["tools/pnva_no_tick_invariant_analyzer.py", "--events", CANONICAL_EVENTS, "--entity-catalog", CANONICAL_ENTITIES, "--replay-report", str(outputs["replay"])], outputs["no_tick"])
        commands["native_no_tick"] = _run(repo, ["tools/pnva_no_tick_invariant_analyzer.py", "--events", NATIVE_EVENTS, "--entity-catalog", NATIVE_ENTITIES, "--replay-report", str(outputs["native_replay"])], outputs["native_no_tick"])
        commands["native_emitter"] = _run(
            repo,
            [
                "tools/pnva_native_event_emitter.py",
                "--events",
                str(outputs["native_emitter_events"]),
                "--entity-catalog",
                str(outputs["native_emitter_entities"]),
                "--summary",
                str(outputs["native_emitter"]),
            ],
            outputs["native_emitter"],
            write_flag=None,
        )
        commands["policy"] = _run(repo, ["tools/pnva_sovereign_policy_validator.py", "--events", CANONICAL_EVENTS, "--entity-catalog", CANONICAL_ENTITIES], outputs["policy"])
        commands["native_policy"] = _run(repo, ["tools/pnva_sovereign_policy_validator.py", "--events", NATIVE_EVENTS, "--entity-catalog", NATIVE_ENTITIES], outputs["native_policy"])
        commands["proof_chain"] = _run(repo, ["tools/pnva_proof_chain_sealer.py", "--events", CANONICAL_EVENTS], outputs["proof_chain"])
        commands["native_proof_chain"] = _run(repo, ["tools/pnva_proof_chain_sealer.py", "--events", NATIVE_EVENTS], outputs["native_proof_chain"])
        commands["causal_graph"] = _run(repo, ["tools/pnva_causal_graph_auditor.py", "--events", CANONICAL_EVENTS, "--entity-catalog", CANONICAL_ENTITIES], outputs["causal_graph"])
        commands["native_causal_graph"] = _run(repo, ["tools/pnva_causal_graph_auditor.py", "--events", NATIVE_EVENTS, "--entity-catalog", NATIVE_ENTITIES], outputs["native_causal_graph"])
        commands["schema_contract"] = _run(repo, ["tools/pnva_schema_contract_validator.py"], outputs["schema_contract"])
        commands["causal_chronology"] = _run(repo, ["tools/pnva_causal_chronology_guard.py"], outputs["causal_chronology"])
        commands["tension_decision"] = _run(repo, ["tools/pnva_tension_decision_calibrator.py"], outputs["tension_decision"])
        commands["decision_trace_index"] = _run(repo, ["tools/pnva_decision_trace_index.py"], outputs["decision_trace_index"])
        commands["heuristic_influence_map"] = _run(repo, ["tools/pnva_heuristic_influence_map.py"], outputs["heuristic_influence_map"])
        commands["entity_no_tick_matrix"] = _run(repo, ["tools/pnva_entity_no_tick_matrix.py"], outputs["entity_no_tick_matrix"])
        commands["suppression_ledger"] = _run(repo, ["tools/pnva_suppression_ledger.py"], outputs["suppression_ledger"])
        commands["sovereign_robustness_gate"] = _run(repo, ["tools/pnva_sovereign_robustness_gate.py"], outputs["sovereign_robustness_gate"])
        commands["r3_migration_plan"] = _run(repo, ["tools/pnva_r3_migration_planner.py"], outputs["r3_migration_plan"])
        commands["authority_migration_ledger"] = _run(repo, ["tools/pnva_authority_migration_ledger.py"], outputs["authority_migration_ledger"])
        commands["r3_authority_projection"] = _run(
            repo,
            [
                "tools/pnva_r3_authority_projection.py",
                "--events",
                str(outputs["r3_authority_projection_events"]),
                "--entity-catalog",
                str(outputs["r3_authority_projection_entities"]),
                "--summary",
                str(outputs["r3_authority_projection"]),
            ],
            outputs["r3_authority_projection"],
            write_flag=None,
        )
        commands["r3_authority_projection_replay"] = _run(
            repo,
            [
                "tools/pnva_replay_validator.py",
                "--events",
                str(outputs["r3_authority_projection_events"]),
                "--entity-catalog",
                str(outputs["r3_authority_projection_entities"]),
            ],
            outputs["r3_authority_projection_replay"],
        )
        commands["r3_authority_projection_policy"] = _run(
            repo,
            [
                "tools/pnva_sovereign_policy_validator.py",
                "--events",
                str(outputs["r3_authority_projection_events"]),
                "--entity-catalog",
                str(outputs["r3_authority_projection_entities"]),
            ],
            outputs["r3_authority_projection_policy"],
        )
        commands["r3_authority_projection_no_tick"] = _run(
            repo,
            [
                "tools/pnva_no_tick_invariant_analyzer.py",
                "--events",
                str(outputs["r3_authority_projection_events"]),
                "--entity-catalog",
                str(outputs["r3_authority_projection_entities"]),
                "--replay-report",
                str(outputs["r3_authority_projection_replay"]),
            ],
            outputs["r3_authority_projection_no_tick"],
        )
        commands["r3_cutover_gate"] = _run(repo, ["tools/pnva_r3_cutover_gate.py"], outputs["r3_cutover_gate"])
        commands["r3_runtime_capture_matrix"] = _run(repo, ["tools/pnva_r3_runtime_capture_matrix.py"], outputs["r3_runtime_capture_matrix"])
        commands["r3_runtime_evidence_guard"] = _run(repo, ["tools/pnva_r3_runtime_evidence_guard.py"], outputs["r3_runtime_evidence_guard"])
        commands["r3_runtime_instrumentation_plan"] = _run(repo, ["tools/pnva_r3_runtime_instrumentation_plan.py"], outputs["r3_runtime_instrumentation_plan"])
        commands["adversarial"] = _run(repo, ["tools/pnva_adversarial_validator.py"], outputs["adversarial"])
        commands["maturity"] = _run(repo, ["tools/pnva_entity_heuristic_maturity.py"], outputs["maturity"])
        commands["attestation"] = _run(repo, ["tools/pnva_evidence_attestor.py"], outputs["attestation"])
        commands["semantic"] = _run(repo, ["tools/pnva_semantic_consistency_guard.py"], outputs["semantic"])

    command_failures = [
        {
            "report": name,
            "exit_code": item["exit_code"],
            "parse_error": item["parse_error"],
            "stderr_tail": item["stderr_tail"],
        }
        for name, item in commands.items()
        if item["exit_code"] != 0 or item["parse_error"] or not item["report"]
    ]
    for name, item in commands.items():
        if item["report"]:
            comparisons.extend(_compare_report(name, published[name], item["report"]))

    failed_comparisons = [item for item in comparisons if not item["pass"]]
    classification = "REPRODUCIBILITY_READY" if not command_failures and not failed_comparisons else "REPRODUCIBILITY_FAIL"
    command_summaries = {
        name: {
            "command": item["command"],
            "exit_code": item["exit_code"],
            "parse_error": item["parse_error"],
            "classification": item["report"].get("classification") if isinstance(item["report"], dict) else None,
            "pass": item["report"].get("pass") if isinstance(item["report"], dict) else None,
        }
        for name, item in commands.items()
    }
    return {
        "schema_version": "pnva.reproducibility_guard.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": classification == "REPRODUCIBILITY_READY",
        "command_count": len(commands),
        "comparison_count": len(comparisons),
        "failure_count": len(command_failures) + len(failed_comparisons),
        "command_failure_count": len(command_failures),
        "comparison_failure_count": len(failed_comparisons),
        "commands": command_summaries,
        "command_failures": command_failures,
        "comparison_failures": failed_comparisons,
        "comparisons": comparisons,
        "summary": {
            "reports_reproduced": sorted(commands),
            "stable_fields_compared": len(comparisons),
            "published_attestation_hash": published["attestation"].get("evidence_hash"),
            "reproduced_attestation_hash": commands["attestation"]["report"].get("evidence_hash") if commands["attestation"]["report"] else None,
        },
        "interpretation": {
            "purpose": "Regenerate PNVA evidence reports with current tools and compare stable fields against the published evidence package.",
            "sovereignty": "A public PNVA release is stronger when its claims are reproducible from source commands, not only stored as static JSON.",
            "boundary": "Generated timestamps, temporary paths and non-semantic ordering are intentionally excluded from comparison.",
        },
        "recommendations": [
            "Run reproducibility after semantic consistency and before checksums.",
            "Treat any command failure or stable-field drift as a release-blocking error.",
            "Keep reproducibility outside the evidence attestation hash seed because it consumes the attestation.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce PNVA public evidence reports and compare stable fields.")
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
