#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

REPORTS = {
    "no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native_no_tick": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "policy": "reports/pnva-sovereign-policy-2026-05-05.json",
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
    "r3_cutover_gate": "reports/pnva-r3-cutover-gate-2026-05-05.json",
    "r3_runtime_capture_matrix": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
    "r3_runtime_evidence_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "r3_runtime_instrumentation_plan": "reports/pnva-r3-runtime-instrumentation-plan-2026-05-05.json",
    "r3_runtime_contract_validation": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
    "maturity": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
    "attestation": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
    "semantic": "reports/pnva-semantic-consistency-2026-05-05.json",
    "reproducibility": "reports/pnva-reproducibility-2026-05-05.json",
    "audit": "reports/pnva-sovereign-audit-2026-05-05.json",
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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _ratio(part: int | float, total: int | float, digits: int = 6) -> float:
    return round(float(part) / max(1.0, float(total)), digits)


def _pct(value: float, digits: int = 2) -> float:
    return round(float(value) * 100.0, digits)


def _weighted_score(parts: dict[str, float]) -> float:
    weights = {
        "robustness": 0.22,
        "maturity": 0.18,
        "publication_integrity": 0.18,
        "semantic_reproducibility": 0.14,
        "r3_preparation": 0.18,
        "r3_runtime_completion": 0.10,
    }
    score = sum(float(parts[name]) * weight for name, weight in weights.items())
    return round(score, 2)


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    data = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}

    no_tick_event_count = _safe_int(_dig(data["no_tick"], ["no_tick_efficiency", "event_count"]))
    no_tick_suppressed = _safe_int(_dig(data["no_tick"], ["no_tick_efficiency", "suppressed_count"]))
    native_suppressed = _safe_int(_dig(data["native_no_tick"], ["no_tick_efficiency", "suppressed_count"]))
    total_suppressed = no_tick_suppressed + native_suppressed
    aggregate_suppression_ratio = _safe_float(_dig(data["maturity"], ["summary", "aggregate_no_tick_suppression_ratio"]))

    schema_warning_count = _safe_int(data["schema_contract"].get("warning_count"))
    chronology_warning_count = _safe_int(data["causal_chronology"].get("warning_count"))
    tension_warning_count = _safe_int(data["tension_decision"].get("warning_count"))
    decision_trace_warning_count = _safe_int(data["decision_trace_index"].get("warning_count"))
    heuristic_warning_count = _safe_int(data["heuristic_influence_map"].get("warning_count"))
    entity_warning_count = _safe_int(data["entity_no_tick_matrix"].get("warning_count"))
    suppression_warning_count = _safe_int(data["suppression_ledger"].get("warning_count"))
    maturity_warning_count = _safe_int(data["maturity"].get("warning_count"))
    authority_warning_count = _safe_int(data["authority_migration_ledger"].get("warning_count"))

    controlled_warning_count = (
        schema_warning_count
        + chronology_warning_count
        + tension_warning_count
        + decision_trace_warning_count
        + heuristic_warning_count
        + entity_warning_count
        + suppression_warning_count
        + maturity_warning_count
        + authority_warning_count
        + _safe_int(data["sovereign_robustness_gate"].get("warning_count"))
        + _safe_int(data["r3_migration_plan"].get("warning_count"))
    )

    capture_slots = _safe_int(data["r3_runtime_capture_matrix"].get("capture_slot_count"))
    verified_slots = _safe_int(data["r3_runtime_capture_matrix"].get("verified_runtime_slot_count"))
    pending_slots = _safe_int(data["r3_runtime_capture_matrix"].get("pending_slot_count"))
    required_runtime_events = _safe_int(data["r3_runtime_capture_matrix"].get("required_runtime_event_count"))
    runtime_coverage_ratio = _safe_float(data["r3_runtime_capture_matrix"].get("runtime_capture_coverage_ratio"))
    guard_positive_control_count = _safe_int(data["r3_runtime_evidence_guard"].get("positive_control_count"))
    guard_positive_control_passed_count = _safe_int(data["r3_runtime_evidence_guard"].get("positive_control_passed_count"))
    guard_positive_controls_ok = (
        guard_positive_control_count > 0
        and guard_positive_control_passed_count == guard_positive_control_count
        and data["r3_runtime_evidence_guard"].get("positive_controls_pass") is True
        and data["r3_runtime_evidence_guard"].get("positive_controls_fixture_only") is True
    )
    instrumentation_positive_control_count = _safe_int(data["r3_runtime_instrumentation_plan"].get("positive_control_count"))
    instrumentation_positive_control_passed_count = _safe_int(data["r3_runtime_instrumentation_plan"].get("positive_control_passed_count"))
    instrumentation_positive_controls_ok = (
        instrumentation_positive_control_count > 0
        and instrumentation_positive_control_passed_count == instrumentation_positive_control_count
    )
    contract_positive_control_count = _safe_int(data["r3_runtime_contract_validation"].get("positive_control_count"))
    contract_positive_control_passed_count = _safe_int(data["r3_runtime_contract_validation"].get("positive_control_passed_count"))
    contract_positive_controls_ok = (
        contract_positive_control_count > 0
        and contract_positive_control_passed_count == contract_positive_control_count
        and data["r3_runtime_contract_validation"].get("positive_controls_fixture_only") is True
    )

    r3_contract_ready = (
        data["r3_runtime_capture_matrix"].get("capture_contract_ready") is True
        and data["r3_runtime_evidence_guard"].get("intake_guard_ready") is True
        and data["r3_runtime_instrumentation_plan"].get("instrumentation_plan_ready") is True
        and data["r3_runtime_contract_validation"].get("contract_validation_ready") is True
        and _safe_int(data["r3_runtime_contract_validation"].get("failure_count"), -1) == 0
        and guard_positive_controls_ok
        and instrumentation_positive_controls_ok
        and contract_positive_controls_ok
    )
    runtime_approved = data["r3_runtime_evidence_guard"].get("runtime_evidence_approved") is True
    cutover_approved = data["r3_cutover_gate"].get("cutover_approved") is True

    publication_integrity_ready = (
        data["attestation"].get("pass") is True
        and data["semantic"].get("pass") is True
        and _safe_int(data["attestation"].get("failure_count")) == 0
        and _safe_int(data["semantic"].get("error_count")) == 0
        and _safe_int(data["semantic"].get("warning_count")) == 0
    )
    native_clean_path = (
        data["native_no_tick"].get("pass") is True
        and _safe_int(_dig(data["maturity"], ["summary", "native_low_authority_legacy_count"])) == 0
        and data["tension_decision"].get("native_calibration_clean") is True
        and data["decision_trace_index"].get("native_trace_clean") is True
        and data["heuristic_influence_map"].get("native_influence_clean") is True
        and data["entity_no_tick_matrix"].get("native_matrix_clean") is True
        and data["suppression_ledger"].get("native_suppression_clean") is True
    )
    no_tick_ready = data["no_tick"].get("pass") is True and data["native_no_tick"].get("pass") is True

    blockers = []
    if not runtime_approved:
        blockers.append(
            {
                "id": "R3_RUNTIME_EVIDENCE_MISSING",
                "severity": "P0",
                "detail": f"{pending_slots} runtime slots remain pending; {required_runtime_events} native events are required.",
                "next_command": "python3 tools/pnva_r3_runtime_evidence_guard.py --runtime-events <fresh-runtime.jsonl> --write reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
            }
        )
    if not cutover_approved:
        blockers.append(
            {
                "id": "R3_CUTOVER_BLOCKED_BY_RUNTIME",
                "severity": "P0",
                "detail": "R3 cutover intentionally remains blocked until fresh native runtime evidence replaces projection evidence.",
                "next_command": "python3 tools/pnva_r3_cutover_gate.py --write reports/pnva-r3-cutover-gate-2026-05-05.json",
            }
        )
    if not r3_contract_ready:
        blockers.append(
            {
                "id": "R3_CONTRACT_NOT_READY",
                "severity": "P0",
                "detail": "Capture matrix, evidence guard, instrumentation plan and contract validator must all be ready before runtime intake.",
                "next_command": "python3 tools/pnva_r3_runtime_contract_validator.py --write reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
            }
        )

    warning_domains = [
        {
            "id": "SCHEMA_CONTRACT_LEGACY_WARNINGS",
            "count": schema_warning_count,
            "meaning": "Bridge-normalized canonical events still carry schema warnings; native scope must remain clean.",
            "next_action": "Keep future runtime events emitted directly as pnva.event.v1.",
        },
        {
            "id": "TENSION_DECISION_LEGACY_WARNINGS",
            "count": tension_warning_count,
            "meaning": "Legacy threshold/decision drift remains visible instead of hidden.",
            "next_action": "Re-emit future suppressions and commits through native calibrated thresholds.",
        },
        {
            "id": "DECISION_TRACE_LOW_AUTHORITY_WARNINGS",
            "count": decision_trace_warning_count,
            "meaning": "Historical decisions with weak authority remain traceable.",
            "next_action": "Require H2/H3 rules for every future collapse/block/prove decision.",
        },
        {
            "id": "HEURISTIC_INFLUENCE_LOW_AUTHORITY_WARNINGS",
            "count": heuristic_warning_count,
            "meaning": "Legacy heuristic edges are mapped and bounded.",
            "next_action": "Use native_event_emitter, adaptive_threshold and field_scheduler on every R3 commit.",
        },
        {
            "id": "ENTITY_NO_TICK_LEGACY_WARNINGS",
            "count": entity_warning_count,
            "meaning": "Entity-level low-authority legacy debt is isolated.",
            "next_action": "Capture one native no-tick precheck and one native commit per pending slot.",
        },
        {
            "id": "SUPPRESSION_LEDGER_LEGACY_WARNINGS",
            "count": suppression_warning_count,
            "meaning": "Above-threshold suppressions are preserved as migration evidence.",
            "next_action": "Use native threshold policy so future suppressions are below-threshold or explicitly blocked.",
        },
    ]

    priority_actions = [
        {
            "order": 1,
            "id": "CAPTURE_R3_RUNTIME_JSONL",
            "status": "pending",
            "target": {
                "slot_count": capture_slots,
                "required_prechecks": capture_slots,
                "required_commits": capture_slots,
                "required_events": required_runtime_events,
            },
            "acceptance": [
                "schema_version=pnva.event.v1",
                "proof.native=true",
                "proof.projection=false",
                "source.format=native_pnva_event_v1",
                "tension.components.original_event_id present",
                "tension.components.r3_runtime_slot_id present",
                "commit max authority >= H2",
            ],
        },
        {
            "order": 2,
            "id": "RUN_RUNTIME_EVIDENCE_GUARD",
            "status": "blocked_until_capture",
            "command": "python3 tools/pnva_r3_runtime_evidence_guard.py --runtime-events <fresh-runtime.jsonl> --write reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
        },
        {
            "order": 3,
            "id": "REGENERATE_DOWNSTREAM_EVIDENCE",
            "status": "blocked_until_guard_accepts",
            "command": "python3 tools/pnva_r3_cutover_gate.py --write reports/pnva-r3-cutover-gate-2026-05-05.json && python3 tools/pnva_semantic_consistency_guard.py --write reports/pnva-semantic-consistency-2026-05-05.json",
        },
        {
            "order": 4,
            "id": "PUBLISH_NEW_ATTESTATION",
            "status": "blocked_until_downstream_passes",
            "command": "python3 tools/pnva_evidence_attestor.py --write reports/pnva-sovereign-evidence-attestation-2026-05-05.json && python3 tools/pnva_reproducibility_guard.py --write reports/pnva-reproducibility-2026-05-05.json",
        },
    ]

    score_parts = {
        "robustness": _safe_float(data["sovereign_robustness_gate"].get("robustness_score")),
        "maturity": _safe_float(data["maturity"].get("maturity_score")),
        "publication_integrity": 100.0 if publication_integrity_ready else 0.0,
        "semantic_reproducibility": 100.0 if data["semantic"].get("pass") else 0.0,
        "r3_preparation": 100.0 if r3_contract_ready else 0.0,
        "r3_runtime_completion": _pct(runtime_coverage_ratio),
    }
    sovereign_evolution_score = _weighted_score(score_parts)

    if not publication_integrity_ready or not no_tick_ready or not r3_contract_ready:
        classification = "PNVA_SOVEREIGN_EVOLUTION_LEDGER_FAIL"
    elif runtime_approved and cutover_approved:
        classification = "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY"
    else:
        classification = "PNVA_SOVEREIGN_EVOLUTION_LEDGER_READY_R3_RUNTIME_REQUIRED"

    return {
        "schema_version": "pnva.sovereign_evolution_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": classification != "PNVA_SOVEREIGN_EVOLUTION_LEDGER_FAIL",
        "current_readiness_level": data["r3_migration_plan"].get("current_readiness_level"),
        "target_readiness_level": data["r3_migration_plan"].get("target_readiness_level"),
        "evidence_integrity_ready": publication_integrity_ready,
        "no_tick_ready": no_tick_ready,
        "native_clean_path": native_clean_path,
        "r3_preparation_ready": r3_contract_ready,
        "r3_runtime_evidence_present": bool(data["r3_runtime_evidence_guard"].get("runtime_evidence_present", False)),
        "r3_runtime_evidence_approved": runtime_approved,
        "r3_cutover_approved": cutover_approved,
        "r3_runtime_capture_coverage_ratio": runtime_coverage_ratio,
        "r3_runtime_capture_coverage_percent": _pct(runtime_coverage_ratio),
        "runtime_required_slot_count": capture_slots,
        "runtime_verified_slot_count": verified_slots,
        "runtime_pending_slot_count": pending_slots,
        "runtime_required_event_count": required_runtime_events,
        "runtime_required_precheck_count": _safe_int(data["r3_runtime_capture_matrix"].get("required_no_tick_precheck_count")),
        "runtime_required_commit_count": _safe_int(data["r3_runtime_capture_matrix"].get("required_collapse_commit_count")),
        "runtime_contract_check_count": _safe_int(data["r3_runtime_contract_validation"].get("contract_check_count")),
        "runtime_contract_failure_count": _safe_int(data["r3_runtime_contract_validation"].get("failure_count")),
        "runtime_negative_control_count": _safe_int(data["r3_runtime_evidence_guard"].get("negative_control_count")),
        "runtime_negative_control_detected_count": _safe_int(data["r3_runtime_evidence_guard"].get("negative_control_detected_count")),
        "runtime_positive_control_count": guard_positive_control_count,
        "runtime_positive_control_passed_count": guard_positive_control_passed_count,
        "runtime_mandatory_field_count": _safe_int(data["r3_runtime_contract_validation"].get("mandatory_field_count")),
        "runtime_enforced_control_count": _safe_int(data["r3_runtime_contract_validation"].get("enforced_control_count")),
        "legacy_debt_count": _safe_int(data["sovereign_robustness_gate"].get("legacy_debt_count")),
        "low_authority_legacy_count": _safe_int(data["policy"].get("canonical_low_authority_legacy_count", _dig(data["policy"], ["summary", "low_authority_legacy_count"]))),
        "low_authority_influence_edge_count": _safe_int(data["heuristic_influence_map"].get("low_authority_strong_edge_count")),
        "above_threshold_suppression_count": _safe_int(data["suppression_ledger"].get("above_threshold_suppression_count")),
        "schema_warning_count": schema_warning_count,
        "chronology_warning_count": chronology_warning_count,
        "tension_warning_count": tension_warning_count,
        "decision_trace_warning_count": decision_trace_warning_count,
        "heuristic_warning_count": heuristic_warning_count,
        "entity_warning_count": entity_warning_count,
        "suppression_warning_count": suppression_warning_count,
        "controlled_warning_count": controlled_warning_count,
        "maturity_score": _safe_float(data["maturity"].get("maturity_score")),
        "robustness_score": _safe_float(data["sovereign_robustness_gate"].get("robustness_score")),
        "publication_integrity_score": score_parts["publication_integrity"],
        "semantic_reproducibility_score": score_parts["semantic_reproducibility"],
        "r3_preparation_score": score_parts["r3_preparation"],
        "r3_runtime_completion_score": score_parts["r3_runtime_completion"],
        "sovereign_evolution_score": sovereign_evolution_score,
        "aggregate_no_tick_suppression_ratio": aggregate_suppression_ratio,
        "aggregate_no_tick_suppression_percent": _pct(aggregate_suppression_ratio),
        "proof_backed_suppression_count": total_suppressed,
        "canonical_no_tick_event_count": no_tick_event_count,
        "priority_action_count": len(priority_actions),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "controlled_warning_domains": warning_domains,
        "priority_actions": priority_actions,
        "score_components": score_parts,
        "reports_checked": REPORTS,
        "summary": {
            "classification": classification,
            "sovereign_evolution_score": sovereign_evolution_score,
            "current_readiness_level": data["r3_migration_plan"].get("current_readiness_level"),
            "target_readiness_level": data["r3_migration_plan"].get("target_readiness_level"),
            "r3_preparation_ready": r3_contract_ready,
            "r3_runtime_capture_coverage_percent": _pct(runtime_coverage_ratio),
            "runtime_pending_slot_count": pending_slots,
            "runtime_required_event_count": required_runtime_events,
            "controlled_warning_count": controlled_warning_count,
            "blocker_count": len(blockers),
            "priority_action_count": len(priority_actions),
        },
        "interpretation": {
            "purpose": "Unify PNVA no-tick, log integrity, heuristic influence, entity coverage and R3 runtime readiness into one evolution ledger.",
            "sovereignty": "The system becomes more robust when every remaining warning is classified as controlled legacy evidence or a runtime blocker with a next command.",
            "boundary": "This ledger does not approve R3. It proves the preparation layer is coherent and names the missing runtime evidence explicitly.",
        },
        "recommendations": [
            "Treat R3 runtime capture as the next P0 production task.",
            "Do not reduce legacy warning counts by deletion; replace them with fresh native evidence.",
            "Keep no-tick prechecks paired with commits so non-execution remains auditable.",
            "Use this ledger as the release dashboard before public claims about R3 readiness.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA sovereign evolution ledger.")
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
