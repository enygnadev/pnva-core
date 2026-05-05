#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
PRECHECK_REASON = "native_authority_precheck_no_tick"
COMMIT_REASON = "native_runtime_commit"
PRECHECK_STATE_AFTER = "suppressed"
COMMIT_STATE_AFTER = "committed"

R3_RUNTIME_CAPTURE_MATRIX = "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json"
R3_RUNTIME_EVIDENCE_GUARD = "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json"
R3_RUNTIME_INSTRUMENTATION_PLAN = "reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json"

REQUIRED_MANDATORY_FIELDS = [
    "schema_version",
    "event_id",
    "timestamp",
    "entity_id",
    "entity_type",
    "causal_chain_id",
    "event_type",
    "field.state_before",
    "field.state_after",
    "decision.kind",
    "decision.action",
    "decision.reason",
    "heuristics.rules",
    "heuristics.risk_flags",
    "tension.score",
    "tension.threshold",
    "tension.gate_delta",
    "tension.components.original_event_id",
    "tension.components.r3_runtime_slot_id",
    "proof.valid",
    "proof.projection",
    "proof.native",
    "proof.proof_hash",
    "proof.proof_ref",
    "source.file_name",
    "source.format",
    "source.line",
    "source.sanitized",
]

REQUIRED_COMPONENTS = [
    "tension.components.original_event_id",
    "tension.components.r3_runtime_slot_id",
]

REQUIRED_ENFORCED_CONTROLS = {
    "schema_version_required": "pnva.event.v1",
    "timestamp_required": True,
    "timestamp_iso8601_required": True,
    "duplicate_event_id_forbidden": True,
    "field_state_required": True,
    "event_type_must_match_slot": True,
    "entity_id_required": True,
    "entity_type_required": True,
    "entity_type_must_match_slot": True,
    "causal_chain_id_required": True,
    "causal_chain_unique_per_slot_required": True,
    "tension_gate_delta_required": True,
    "tension_gate_delta_consistency_required": True,
    "precheck_gate_delta_nonpositive_required": True,
    "commit_gate_delta_nonnegative_required": True,
    "proof_hash_required": True,
    "proof_hash_sha256_format_required": True,
    "proof_hash_binds_event_identity": True,
    "proof_hash_binds_source_location": True,
    "proof_hash_unique_required": True,
    "proof_ref_unique_required": True,
    "proof_ref_runtime_slot_role_required": True,
    "proof_native_required": True,
    "proof_projection_forbidden": True,
    "source_format_required": "native_pnva_event_v1",
    "source_file_name_required": True,
    "source_file_name_public_basename_required": True,
    "source_line_required": True,
    "source_location_unique_required": True,
    "source_line_monotonic_per_file_required": True,
    "source_sanitized_required": True,
    "r3_runtime_slot_id_required": True,
    "commit_min_authority": "H2",
    "precheck_must_be_no_tick": True,
    "precheck_reason_required": PRECHECK_REASON,
    "commit_reason_required": COMMIT_REASON,
    "field_state_transition_required": True,
    "precheck_state_after_required": PRECHECK_STATE_AFTER,
    "commit_state_after_required": COMMIT_STATE_AFTER,
    "no_tick_pair_causal_chain_required": True,
    "no_tick_pair_commit_after_precheck_required": True,
    "no_tick_pair_commit_strictly_after_precheck_required": True,
    "no_tick_pair_log_line_order_required": True,
    "no_tick_pair_same_source_file_required": True,
    "no_tick_pair_state_continuity_required": True,
    "no_tick_pair_source_line_order_required": True,
    "no_tick_pair_exactly_one_precheck_commit_required": True,
    "runtime_event_count_exact_required": True,
    "commit_must_match_slot_action": True,
    "target_rules_required_on_commit": True,
    "target_rules_required_on_precheck": True,
    "legacy_heuristic_rule_forbidden": True,
    "heuristic_rules_known_required": True,
    "heuristic_rules_unique_required": True,
    "risk_flags_list_required": True,
    "risk_flags_known_required": True,
    "risk_flags_unique_required": True,
    "target_risk_flags_required_on_precheck": True,
    "target_risk_flags_required_on_commit": True,
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


def _slot_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = matrix.get("capture_slots")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _failures(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in checks if not item["pass"]]


def _add_check(checks: list[dict[str, Any]], group: str, name: str, left: Any, right: Any, *, left_ref: str = "", right_ref: str = "expected") -> None:
    checks.append(
        {
            "group": group,
            "name": name,
            "pass": left == right,
            "left": left,
            "right": right,
            "left_ref": left_ref or name,
            "right_ref": right_ref,
        }
    )


def _template_checks(checks: list[dict[str, Any]], contract: dict[str, Any]) -> None:
    contract_id = str(contract.get("contract_id") or "unknown_contract")
    action = str(contract.get("decision_action") or "")
    slot_count = int(contract.get("slot_count", 0))
    precheck = contract.get("precheck_template") if isinstance(contract.get("precheck_template"), dict) else {}
    commit = contract.get("commit_template") if isinstance(contract.get("commit_template"), dict) else {}
    pairing = contract.get("pairing_policy") if isinstance(contract.get("pairing_policy"), dict) else {}
    event_type_policy = contract.get("event_type_policy") if isinstance(contract.get("event_type_policy"), dict) else {}
    tension_policy = contract.get("tension_policy") if isinstance(contract.get("tension_policy"), dict) else {}
    decision_reason_policy = contract.get("decision_reason_policy") if isinstance(contract.get("decision_reason_policy"), dict) else {}
    field_state_policy = contract.get("field_state_policy") if isinstance(contract.get("field_state_policy"), dict) else {}
    proof_policy = contract.get("proof_policy") if isinstance(contract.get("proof_policy"), dict) else {}
    heuristic_policy = contract.get("heuristic_policy") if isinstance(contract.get("heuristic_policy"), dict) else {}
    slot_ids = contract.get("slot_ids") if isinstance(contract.get("slot_ids"), list) else []
    original_ids = contract.get("original_event_ids") if isinstance(contract.get("original_event_ids"), list) else []
    event_type_mix = contract.get("event_type_mix") if isinstance(contract.get("event_type_mix"), list) else []
    target_event_types = sorted(str(item[0]) for item in event_type_mix if isinstance(item, list) and item and str(item[0]))
    risk_flag_mix = contract.get("risk_flags") if isinstance(contract.get("risk_flags"), list) else []
    target_risk_flags = sorted(str(item[0]) for item in risk_flag_mix if isinstance(item, list) and item and str(item[0]))

    _add_check(checks, "contract", f"{contract_id}_precheck_count", int(contract.get("required_precheck_count", 0)), slot_count)
    _add_check(checks, "contract", f"{contract_id}_commit_count", int(contract.get("required_commit_count", 0)), slot_count)
    _add_check(checks, "contract", f"{contract_id}_runtime_event_count", int(contract.get("required_runtime_event_count", 0)), slot_count * 2)
    _add_check(checks, "contract", f"{contract_id}_slot_ids_count", len(slot_ids), slot_count)
    _add_check(checks, "contract", f"{contract_id}_original_ids_count", len(original_ids), slot_count)

    for template_name, template in (("precheck", precheck), ("commit", commit)):
        _add_check(checks, "template", f"{contract_id}_{template_name}_schema", template.get("schema_version"), "pnva.event.v1")
        _add_check(checks, "template", f"{contract_id}_{template_name}_proof_projection", _dig(template, ["proof", "projection"]), False)
        _add_check(checks, "template", f"{contract_id}_{template_name}_proof_native", _dig(template, ["proof", "native"]), True)
        _add_check(checks, "template", f"{contract_id}_{template_name}_proof_valid", _dig(template, ["proof", "valid"]), True)
        _add_check(checks, "template", f"{contract_id}_{template_name}_source_file_name_present", bool(_dig(template, ["source", "file_name"])), True)
        _add_check(checks, "template", f"{contract_id}_{template_name}_source_format", _dig(template, ["source", "format"]), "native_pnva_event_v1")
        _add_check(checks, "template", f"{contract_id}_{template_name}_source_line_present", bool(_dig(template, ["source", "line"])), True)
        _add_check(checks, "template", f"{contract_id}_{template_name}_source_sanitized", _dig(template, ["source", "sanitized"]), True)
        _add_check(checks, "template", f"{contract_id}_{template_name}_components", sorted(template.get("required_components", [])), sorted(REQUIRED_COMPONENTS))
        _add_check(checks, "template", f"{contract_id}_{template_name}_risk_flags", sorted(template.get("required_risk_flags", [])), target_risk_flags)

    _add_check(checks, "template", f"{contract_id}_precheck_kind", _dig(precheck, ["decision", "kind"]), "observe")
    _add_check(checks, "template", f"{contract_id}_precheck_action", _dig(precheck, ["decision", "action"]), "NO_ACTION")
    _add_check(checks, "template", f"{contract_id}_precheck_reason", _dig(precheck, ["decision", "reason"]), PRECHECK_REASON)
    _add_check(checks, "template", f"{contract_id}_precheck_state_after", _dig(precheck, ["field", "state_after"]), PRECHECK_STATE_AFTER)
    _add_check(checks, "template", f"{contract_id}_commit_action", _dig(commit, ["decision", "action"]), action)
    _add_check(checks, "template", f"{contract_id}_commit_reason", _dig(commit, ["decision", "reason"]), COMMIT_REASON)
    _add_check(checks, "template", f"{contract_id}_commit_state_after", _dig(commit, ["field", "state_after"]), COMMIT_STATE_AFTER)
    _add_check(checks, "event_type_policy", f"{contract_id}_commit_event_type_in_matrix", commit.get("event_type") in set(target_event_types), True)
    _add_check(checks, "event_type_policy", f"{contract_id}_precheck_event_type_binding", precheck.get("event_type"), f"{commit.get('event_type')}_authority_precheck")
    _add_check(checks, "template", f"{contract_id}_commit_min_authority", commit.get("min_authority"), "H2")
    _add_check(checks, "template", f"{contract_id}_precheck_native_rule", "native_event_emitter" in set(precheck.get("required_rules", [])), True)
    _add_check(checks, "template", f"{contract_id}_commit_rules_nonempty", bool(commit.get("required_rules")), True)
    _add_check(checks, "pairing", f"{contract_id}_timestamp_iso8601_required", pairing.get("timestamp_iso8601_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_duplicate_event_id_forbidden", pairing.get("duplicate_event_id_forbidden"), True)
    _add_check(checks, "pairing", f"{contract_id}_causal_chain_unique_per_slot_required", pairing.get("causal_chain_unique_per_slot_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_source_file_name_public_basename_required", pairing.get("source_file_name_public_basename_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_source_location_unique_required", pairing.get("source_location_unique_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_source_line_monotonic_per_file_required", pairing.get("source_line_monotonic_per_file_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_same_causal_chain_id_required", pairing.get("same_causal_chain_id_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_commit_timestamp_after_precheck_required", pairing.get("commit_timestamp_after_precheck_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_commit_timestamp_strictly_after_precheck_required", pairing.get("commit_timestamp_strictly_after_precheck_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_commit_log_line_after_precheck_required", pairing.get("commit_log_line_after_precheck_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_same_source_file_name_required", pairing.get("same_source_file_name_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_commit_state_before_equals_precheck_state_after_required", pairing.get("commit_state_before_equals_precheck_state_after_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_commit_source_line_after_precheck_required", pairing.get("commit_source_line_after_precheck_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_exactly_one_precheck_per_slot", pairing.get("exactly_one_precheck_per_slot_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_exactly_one_commit_per_slot", pairing.get("exactly_one_commit_per_slot_required"), True)
    _add_check(checks, "pairing", f"{contract_id}_runtime_event_count_exact", pairing.get("runtime_event_count_must_equal_required"), True)
    _add_check(checks, "event_type_policy", f"{contract_id}_precheck_event_type_policy", event_type_policy.get("precheck_event_type_must_equal_slot_event_type_plus_authority_precheck"), True)
    _add_check(checks, "event_type_policy", f"{contract_id}_commit_event_type_policy", event_type_policy.get("commit_event_type_must_equal_slot_event_type"), True)
    _add_check(checks, "tension_policy", f"{contract_id}_gate_delta_consistency", tension_policy.get("gate_delta_must_equal_score_minus_threshold"), True)
    _add_check(checks, "tension_policy", f"{contract_id}_precheck_gate_delta_nonpositive", tension_policy.get("precheck_gate_delta_nonpositive_required"), True)
    _add_check(checks, "tension_policy", f"{contract_id}_commit_gate_delta_nonnegative", tension_policy.get("commit_gate_delta_nonnegative_required"), True)
    _add_check(checks, "decision_reason_policy", f"{contract_id}_precheck_reason_required", decision_reason_policy.get("precheck_reason_required"), PRECHECK_REASON)
    _add_check(checks, "decision_reason_policy", f"{contract_id}_commit_reason_required", decision_reason_policy.get("commit_reason_required"), COMMIT_REASON)
    _add_check(checks, "field_state_policy", f"{contract_id}_state_transition_required", field_state_policy.get("state_transition_required"), True)
    _add_check(checks, "field_state_policy", f"{contract_id}_precheck_state_after_required", field_state_policy.get("precheck_state_after_required"), PRECHECK_STATE_AFTER)
    _add_check(checks, "field_state_policy", f"{contract_id}_commit_state_after_required", field_state_policy.get("commit_state_after_required"), COMMIT_STATE_AFTER)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_hash_sha256_format_required", proof_policy.get("proof_hash_sha256_format_required"), True)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_hash_binds_event_identity", proof_policy.get("proof_hash_binds_event_identity"), True)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_hash_binds_source_location", proof_policy.get("proof_hash_binds_source_location"), True)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_hash_unique_required", proof_policy.get("proof_hash_unique_required"), True)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_ref_unique_required", proof_policy.get("proof_ref_unique_required"), True)
    _add_check(checks, "proof_policy", f"{contract_id}_proof_ref_runtime_slot_role_required", proof_policy.get("proof_ref_runtime_slot_role_required"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_known_rules_only", heuristic_policy.get("known_rules_only"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_legacy_observer_forbidden", heuristic_policy.get("legacy_observer_forbidden"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_duplicate_rules_forbidden", heuristic_policy.get("duplicate_rules_forbidden"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_risk_flags_list_required", heuristic_policy.get("risk_flags_list_required"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_known_risk_flags_only", heuristic_policy.get("known_risk_flags_only"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_duplicate_risk_flags_forbidden", heuristic_policy.get("duplicate_risk_flags_forbidden"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_precheck_target_rules_required", heuristic_policy.get("precheck_target_rules_required"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_precheck_target_risk_flags_required", heuristic_policy.get("precheck_target_risk_flags_required"), True)
    _add_check(checks, "heuristic_policy", f"{contract_id}_commit_target_risk_flags_required", heuristic_policy.get("commit_target_risk_flags_required"), True)


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    matrix = _read_json(repo / R3_RUNTIME_CAPTURE_MATRIX)
    guard = _read_json(repo / R3_RUNTIME_EVIDENCE_GUARD)
    plan = _read_json(repo / R3_RUNTIME_INSTRUMENTATION_PLAN)
    slots = _slot_rows(matrix)
    contracts = plan.get("action_contracts") if isinstance(plan.get("action_contracts"), list) else []
    checks: list[dict[str, Any]] = []
    runtime_present = guard.get("runtime_evidence_present") is True
    runtime_approved = guard.get("runtime_evidence_approved") is True

    _add_check(checks, "source", "matrix_classification", matrix.get("classification") in {"R3_RUNTIME_CAPTURE_MATRIX_READY_PENDING_RUNTIME", "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE"}, True)
    _add_check(checks, "source", "guard_classification", guard.get("classification") in {"R3_RUNTIME_EVIDENCE_GUARD_READY_AWAITING_CAPTURE", "R3_RUNTIME_EVIDENCE_ACCEPTED"}, True)
    _add_check(checks, "source", "plan_classification", plan.get("classification"), "R3_RUNTIME_INSTRUMENTATION_PLAN_READY")
    _add_check(checks, "boundary", "guard_runtime_approval_matches_presence", guard.get("runtime_evidence_approved"), runtime_present)
    _add_check(checks, "boundary", "plan_runtime_approval_matches_guard", plan.get("runtime_evidence_approved"), runtime_approved)
    _add_check(checks, "counts", "capture_slot_count_matches_matrix", int(plan.get("capture_slot_count", 0)), int(matrix.get("capture_slot_count", 0)))
    _add_check(checks, "counts", "capture_slots_match_rows", int(matrix.get("capture_slot_count", 0)), len(slots))
    _add_check(checks, "counts", "required_runtime_events_match", int(plan.get("required_runtime_event_count", 0)), int(matrix.get("required_runtime_event_count", 0)))
    _add_check(checks, "counts", "runtime_events_are_pairs", int(plan.get("required_runtime_event_count", 0)), int(plan.get("capture_slot_count", 0)) * 2)
    _add_check(checks, "counts", "event_templates_are_pairs", int(plan.get("event_template_count", 0)), int(plan.get("action_contract_count", 0)) * 2)
    _add_check(checks, "controls", "negative_controls_complete", int(guard.get("negative_control_detected_count", 0)), int(guard.get("negative_control_count", -1)))
    _add_check(checks, "controls", "negative_controls_strong_enough", int(guard.get("negative_control_count", 0)) >= 10, True)
    _add_check(checks, "controls", "positive_controls_complete", int(guard.get("positive_control_passed_count", 0)), int(guard.get("positive_control_count", -1)))
    _add_check(checks, "controls", "positive_controls_strong_enough", int(guard.get("positive_control_count", 0)) >= 6, True)
    _add_check(checks, "controls", "positive_controls_fixture_only", guard.get("positive_controls_fixture_only"), True)
    _add_check(checks, "fields", "mandatory_field_count", int(plan.get("mandatory_field_count", 0)), len(REQUIRED_MANDATORY_FIELDS))
    _add_check(checks, "fields", "mandatory_fields_complete", sorted(plan.get("mandatory_event_fields", [])), sorted(REQUIRED_MANDATORY_FIELDS))

    enforced_controls = guard.get("enforced_controls") if isinstance(guard.get("enforced_controls"), dict) else {}
    for key, expected in REQUIRED_ENFORCED_CONTROLS.items():
        _add_check(checks, "enforced_controls", f"enforced_{key}", enforced_controls.get(key), expected)

    contract_slot_sum = 0
    contract_runtime_sum = 0
    contract_original_ids: set[str] = set()
    contract_slot_ids: set[str] = set()
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        contract_slot_sum += int(contract.get("slot_count", 0))
        contract_runtime_sum += int(contract.get("required_runtime_event_count", 0))
        contract_original_ids.update(str(item) for item in contract.get("original_event_ids", []) if str(item))
        contract_slot_ids.update(str(item) for item in contract.get("slot_ids", []) if str(item))
        _template_checks(checks, contract)

    matrix_original_ids = {str(slot.get("original_event_id") or "") for slot in slots if slot.get("original_event_id")}
    matrix_slot_ids = {str(slot.get("slot_id") or "") for slot in slots if slot.get("slot_id")}
    _add_check(checks, "contract", "contract_count", len(contracts), int(plan.get("action_contract_count", 0)))
    _add_check(checks, "contract", "contract_slot_sum", contract_slot_sum, len(slots))
    _add_check(checks, "contract", "contract_runtime_event_sum", contract_runtime_sum, int(plan.get("required_runtime_event_count", 0)))
    _add_check(checks, "contract", "contract_original_ids_cover_matrix", sorted(contract_original_ids), sorted(matrix_original_ids))
    _add_check(checks, "contract", "contract_slot_ids_cover_matrix", sorted(contract_slot_ids), sorted(matrix_slot_ids))

    failures = _failures(checks)
    ready = not failures
    classification = "R3_RUNTIME_CONTRACT_VALIDATED_READY" if ready else "R3_RUNTIME_CONTRACT_VALIDATION_FAIL"

    return {
        "schema_version": "pnva.r3_runtime_contract_validation.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": ready,
        "contract_validation_ready": ready,
        "runtime_evidence_present": runtime_present,
        "runtime_evidence_approved": runtime_approved,
        "source_matrix_classification": matrix.get("classification"),
        "source_guard_classification": guard.get("classification"),
        "source_plan_classification": plan.get("classification"),
        "capture_slot_count": len(slots),
        "action_contract_count": len(contracts),
        "required_runtime_event_count": int(plan.get("required_runtime_event_count", 0)),
        "event_template_count": int(plan.get("event_template_count", 0)),
        "mandatory_field_count": int(plan.get("mandatory_field_count", 0)),
        "required_component_count": len(REQUIRED_COMPONENTS),
        "enforced_control_count": len(REQUIRED_ENFORCED_CONTROLS),
        "negative_control_count": int(guard.get("negative_control_count", 0)),
        "negative_control_detected_count": int(guard.get("negative_control_detected_count", 0)),
        "positive_control_count": int(guard.get("positive_control_count", 0)),
        "positive_control_passed_count": int(guard.get("positive_control_passed_count", 0)),
        "positive_controls_fixture_only": bool(guard.get("positive_controls_fixture_only", False)),
        "contract_check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "reports_checked": {
            "r3_runtime_capture_matrix": R3_RUNTIME_CAPTURE_MATRIX,
            "r3_runtime_evidence_guard": R3_RUNTIME_EVIDENCE_GUARD,
            "r3_runtime_instrumentation_plan": R3_RUNTIME_INSTRUMENTATION_PLAN,
        },
        "summary": {
            "contract_validation_ready": ready,
            "capture_slot_count": len(slots),
            "action_contract_count": len(contracts),
            "required_runtime_event_count": int(plan.get("required_runtime_event_count", 0)),
            "mandatory_field_count": int(plan.get("mandatory_field_count", 0)),
            "negative_control_detected_count": int(guard.get("negative_control_detected_count", 0)),
            "positive_control_passed_count": int(guard.get("positive_control_passed_count", 0)),
            "contract_check_count": len(checks),
            "failure_count": len(failures),
        },
        "interpretation": {
            "purpose": "Validate that the R3 runtime capture matrix, evidence guard and instrumentation plan form one coherent runtime contract.",
            "sovereignty": "The final runtime path becomes harder to mislabel because the contract itself is checked before fresh runtime evidence is accepted.",
            "boundary": "This is a contract validator. Runtime approval is accepted only when the guard has accepted slot-bound native events.",
        },
        "recommendations": [
            "Run this contract validator after changing any R3 capture, guard or instrumentation logic.",
            "Do not accept final runtime JSONL unless this contract validation remains ready.",
            "Keep R3 runtime events slot-bound through tension.components.r3_runtime_slot_id.",
            "Keep final runtime events native through proof.native=true and source.format=native_pnva_event_v1.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the PNVA R3 runtime contract before fresh evidence capture.")
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
