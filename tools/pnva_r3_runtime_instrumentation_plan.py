#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
PRECHECK_REASON = "native_authority_precheck_no_tick"
COMMIT_REASON = "native_runtime_commit"

R3_RUNTIME_CAPTURE_MATRIX = "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json"
R3_RUNTIME_EVIDENCE_GUARD = "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json"

MANDATORY_EVENT_FIELDS = [
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

VALIDATION_COMMANDS = [
    "python3 tools/pnva_r3_runtime_evidence_guard.py --runtime-events <fresh-runtime-events.jsonl> --write /tmp/pnva-r3-runtime-evidence-guard.json",
    "python3 tools/pnva_replay_validator.py --events <fresh-runtime-events.jsonl> --entity-catalog <fresh-runtime-entities.json> --write /tmp/pnva-r3-runtime-replay.json",
    "python3 tools/pnva_sovereign_policy_validator.py --events <fresh-runtime-events.jsonl> --entity-catalog <fresh-runtime-entities.json> --write /tmp/pnva-r3-runtime-policy.json",
    "python3 tools/pnva_no_tick_invariant_analyzer.py --events <fresh-runtime-events.jsonl> --entity-catalog <fresh-runtime-entities.json> --replay-report /tmp/pnva-r3-runtime-replay.json --write /tmp/pnva-r3-runtime-no-tick.json",
    "python3 tools/pnva_proof_chain_sealer.py --events <fresh-runtime-events.jsonl> --write /tmp/pnva-r3-runtime-proof-chain.json",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _slot_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = matrix.get("capture_slots")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _action_contracts(slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for slot in slots:
        key = (str(slot.get("entity_id") or "unknown"), str(slot.get("decision_action") or "unknown"))
        grouped.setdefault(key, []).append(slot)

    contracts: list[dict[str, Any]] = []
    for (entity_id, action), action_slots in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0][0], item[0][1])):
        target_rules = Counter()
        risk_flags = Counter()
        event_types = Counter()
        for slot in action_slots:
            for rule in slot.get("target_rules", []) if isinstance(slot.get("target_rules"), list) else []:
                target_rules[str(rule)] += 1
            for flag in slot.get("risk_flags", []) if isinstance(slot.get("risk_flags"), list) else []:
                risk_flags[str(flag)] += 1
            event_types[str(slot.get("event_type") or "unknown")] += 1

        first = action_slots[0]
        rules = [rule for rule, _count in target_rules.most_common()]
        contracts.append(
            {
                "contract_id": f"r3-runtime-instrument-{entity_id}-{action.lower()}",
                "entity_id": entity_id,
                "entity_type": str(first.get("entity_type") or "unknown"),
                "decision_action": action,
                "slot_count": len(action_slots),
                "required_precheck_count": len(action_slots),
                "required_commit_count": len(action_slots),
                "required_runtime_event_count": len(action_slots) * 2,
                "event_type_mix": event_types.most_common(),
                "target_rules": rules,
                "risk_flags": risk_flags.most_common(),
                "pairing_policy": {
                    "timestamp_iso8601_required": True,
                    "duplicate_event_id_forbidden": True,
                    "same_causal_chain_id_required": True,
                    "commit_timestamp_after_precheck_required": True,
                    "exactly_one_precheck_per_slot_required": True,
                    "exactly_one_commit_per_slot_required": True,
                    "runtime_event_count_must_equal_required": True,
                },
                "event_type_policy": {
                    "precheck_event_type_must_equal_slot_event_type_plus_authority_precheck": True,
                    "commit_event_type_must_equal_slot_event_type": True,
                },
                "tension_policy": {
                    "gate_delta_must_equal_score_minus_threshold": True,
                    "precheck_gate_delta_nonpositive_required": True,
                    "commit_gate_delta_nonnegative_required": True,
                },
                "decision_reason_policy": {
                    "precheck_reason_required": PRECHECK_REASON,
                    "commit_reason_required": COMMIT_REASON,
                },
                "proof_policy": {
                    "proof_hash_sha256_format_required": True,
                    "proof_hash_binds_event_identity": True,
                    "proof_hash_binds_source_location": True,
                    "proof_hash_unique_required": True,
                    "proof_ref_unique_required": True,
                    "proof_ref_runtime_slot_role_required": True,
                },
                "heuristic_policy": {
                    "known_rules_only": True,
                    "duplicate_rules_forbidden": True,
                    "risk_flags_list_required": True,
                    "known_risk_flags_only": True,
                    "duplicate_risk_flags_forbidden": True,
                    "precheck_target_risk_flags_required": True,
                    "commit_target_risk_flags_required": True,
                },
                "precheck_template": {
                    "schema_version": "pnva.event.v1",
                    "event_type": f"{first.get('event_type')}_authority_precheck",
                    "decision": {
                        "kind": "observe",
                        "action": "NO_ACTION",
                        "reason": PRECHECK_REASON,
                    },
                    "proof": {
                        "projection": False,
                        "native": True,
                        "valid": True,
                        "proof_hash": "sha256:<runtime-proof-hash>",
                        "proof_ref": "runtime:<slot-id>:precheck",
                    },
                    "source": {
                        "file_name": "<runtime-emitter-name>",
                        "format": "native_pnva_event_v1",
                        "line": "<runtime-event-sequence>",
                        "sanitized": True,
                    },
                    "required_rules": sorted(set(["native_event_emitter", *rules])),
                    "required_risk_flags": [flag for flag, _count in risk_flags.most_common()],
                    "required_components": [
                        "tension.components.original_event_id",
                        "tension.components.r3_runtime_slot_id",
                    ],
                },
                "commit_template": {
                    "schema_version": "pnva.event.v1",
                    "event_type": str(first.get("event_type") or "unknown"),
                    "decision": {
                        "kind": str(first.get("decision_kind") or "collapse"),
                        "action": action,
                        "reason": COMMIT_REASON,
                    },
                    "proof": {
                        "projection": False,
                        "native": True,
                        "valid": True,
                        "proof_hash": "sha256:<runtime-proof-hash>",
                        "proof_ref": "runtime:<slot-id>:commit",
                    },
                    "source": {
                        "file_name": "<runtime-emitter-name>",
                        "format": "native_pnva_event_v1",
                        "line": "<runtime-event-sequence>",
                        "sanitized": True,
                    },
                    "min_authority": "H2",
                    "required_rules": rules,
                    "required_risk_flags": [flag for flag, _count in risk_flags.most_common()],
                    "required_components": [
                        "tension.components.original_event_id",
                        "tension.components.r3_runtime_slot_id",
                    ],
                },
                "slot_ids": [str(slot.get("slot_id") or "") for slot in action_slots],
                "original_event_ids": [str(slot.get("original_event_id") or "") for slot in action_slots],
            }
        )
    return contracts


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    matrix = _read_json(repo / R3_RUNTIME_CAPTURE_MATRIX)
    guard = _read_json(repo / R3_RUNTIME_EVIDENCE_GUARD)
    slots = _slot_rows(matrix)
    contracts = _action_contracts(slots)
    contract_runtime_events = sum(int(item["required_runtime_event_count"]) for item in contracts)
    contract_prechecks = sum(int(item["required_precheck_count"]) for item in contracts)
    contract_commits = sum(int(item["required_commit_count"]) for item in contracts)
    entity_count = len({str(slot.get("entity_id") or "") for slot in slots})
    target_rules = sorted({rule for contract in contracts for rule in contract["target_rules"]})

    plan_ready = (
        matrix.get("pass") is True
        and matrix.get("classification") == "R3_RUNTIME_CAPTURE_MATRIX_READY_PENDING_RUNTIME"
        and guard.get("pass") is True
        and guard.get("classification") == "R3_RUNTIME_EVIDENCE_GUARD_READY_AWAITING_CAPTURE"
        and int(matrix.get("capture_slot_count", 0)) == len(slots)
        and int(matrix.get("required_runtime_event_count", 0)) == contract_runtime_events
        and int(guard.get("required_runtime_event_count", 0)) == contract_runtime_events
        and int(guard.get("negative_control_detected_count", -1)) == int(guard.get("negative_control_count", 0))
        and int(guard.get("positive_control_passed_count", -1)) == int(guard.get("positive_control_count", 0))
    )
    classification = "R3_RUNTIME_INSTRUMENTATION_PLAN_READY" if plan_ready else "R3_RUNTIME_INSTRUMENTATION_PLAN_FAIL"

    return {
        "schema_version": "pnva.r3_runtime_instrumentation_plan.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": plan_ready,
        "instrumentation_plan_ready": plan_ready,
        "runtime_evidence_present": False,
        "runtime_evidence_approved": False,
        "source_matrix_classification": matrix.get("classification"),
        "source_guard_classification": guard.get("classification"),
        "capture_slot_count": len(slots),
        "entity_target_count": entity_count,
        "action_contract_count": len(contracts),
        "required_runtime_event_count": contract_runtime_events,
        "required_no_tick_precheck_count": contract_prechecks,
        "required_collapse_commit_count": contract_commits,
        "event_template_count": len(contracts) * 2,
        "mandatory_field_count": len(MANDATORY_EVENT_FIELDS),
        "target_rule_count": len(target_rules),
        "target_rules": target_rules,
        "negative_control_count": int(guard.get("negative_control_count", 0)),
        "negative_control_detected_count": int(guard.get("negative_control_detected_count", 0)),
        "positive_control_count": int(guard.get("positive_control_count", 0)),
        "positive_control_passed_count": int(guard.get("positive_control_passed_count", 0)),
        "action_contracts": contracts,
        "mandatory_event_fields": MANDATORY_EVENT_FIELDS,
        "validation_commands": VALIDATION_COMMANDS,
        "runtime_capture_phases": [
            {
                "phase": 1,
                "name": "instrument_native_emitters",
                "exit_criteria": "Every target action can emit pnva.event.v1 precheck and commit events with original_event_id.",
            },
            {
                "phase": 2,
                "name": "capture_fresh_runtime_jsonl",
                "exit_criteria": "Collect exactly 70 fresh events covering 35 slots with source.file_name, source.line and without proof.projection=true.",
            },
            {
                "phase": 3,
                "name": "run_runtime_evidence_guard",
                "exit_criteria": "R3_RUNTIME_EVIDENCE_ACCEPTED with 35 accepted slots and 0 rejected events.",
            },
            {
                "phase": 4,
                "name": "run_runtime_validators",
                "exit_criteria": "Replay, policy, no-tick and proof-chain validation pass over the fresh runtime sample.",
            },
            {
                "phase": 5,
                "name": "request_cutover",
                "exit_criteria": "Only after fresh runtime evidence replaces projection evidence.",
            },
        ],
        "reports_checked": {
            "r3_runtime_capture_matrix": R3_RUNTIME_CAPTURE_MATRIX,
            "r3_runtime_evidence_guard": R3_RUNTIME_EVIDENCE_GUARD,
        },
        "summary": {
            "instrumentation_plan_ready": plan_ready,
            "capture_slot_count": len(slots),
            "entity_target_count": entity_count,
            "action_contract_count": len(contracts),
            "required_runtime_event_count": contract_runtime_events,
            "event_template_count": len(contracts) * 2,
            "mandatory_field_count": len(MANDATORY_EVENT_FIELDS),
            "negative_control_detected_count": int(guard.get("negative_control_detected_count", 0)),
            "positive_control_passed_count": int(guard.get("positive_control_passed_count", 0)),
        },
        "interpretation": {
            "purpose": "Convert R3 runtime capture slots into concrete emitter contracts, required fields and validation commands.",
            "sovereignty": "PNVA becomes easier to execute safely when the next runtime step is an explicit instrumentation plan instead of an informal instruction.",
            "boundary": "This plan is not runtime evidence and does not approve R3 cutover; it defines how fresh runtime evidence must be emitted and validated.",
        },
        "recommendations": [
            "Implement one emitter path per action contract before collecting final R3 runtime evidence.",
            "Keep proof.projection=false on all final runtime prechecks and commits.",
            "Emit original_event_id in tension.components so each runtime event maps back to a capture slot.",
            "Emit fixed decision.reason values so no-tick prechecks and runtime commits remain semantically distinct.",
            "Run the runtime evidence guard before replay, policy, no-tick and proof-chain validators.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA R3 runtime instrumentation plan.")
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
