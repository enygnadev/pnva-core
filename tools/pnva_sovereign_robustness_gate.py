#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


REPORTS = {
    "replay": "reports/pnva-replay-validation-2026-05-05.json",
    "no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
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
    "adversarial": "reports/pnva-adversarial-validation-2026-05-05.json",
    "maturity": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "replay": "REPLAY_VALID",
    "no_tick": "SOVEREIGN_NO_TICK_READY",
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
    "adversarial": "ADVERSARIAL_VALIDATION_PASS",
    "maturity": "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS",
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


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _criterion(name: str, passed: bool, points: int, max_points: int, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "points": int(points if passed else 0),
        "max_points": int(max_points),
        "evidence": evidence,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    data = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}

    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for key, expected in EXPECTED_CLASSIFICATIONS.items():
        observed = data[key].get("classification")
        reported_pass = data[key].get("pass", True)
        if observed != expected or reported_pass is False:
            blockers.append(
                {
                    "code": "REPORT_NOT_READY",
                    "report": key,
                    "expected": expected,
                    "observed": observed,
                    "reported_pass": reported_pass,
                }
            )

    canonical_events = int(_dig(data["no_tick"], ["no_tick_efficiency", "event_count"], 0))
    native_events = int(_dig(data["native_no_tick"], ["no_tick_efficiency", "event_count"], 0))
    total_events = canonical_events + native_events
    canonical_suppressed = int(_dig(data["no_tick"], ["no_tick_efficiency", "suppressed_count"], 0))
    native_suppressed = int(_dig(data["native_no_tick"], ["no_tick_efficiency", "suppressed_count"], 0))
    total_suppressed = canonical_suppressed + native_suppressed

    maturity_summary = data["maturity"].get("summary", {})
    canonical_legacy_debt = int(maturity_summary.get("canonical_low_authority_legacy_count", 0))
    native_legacy_debt = int(maturity_summary.get("native_low_authority_legacy_count", 0))
    total_strong = int(maturity_summary.get("total_strong_decision_count", 0))
    total_hard = int(maturity_summary.get("total_strong_with_hard_authority", 0))
    hard_authority_ratio = float(maturity_summary.get("aggregate_hard_authority_ratio", 0.0))
    suppression_ratio = _ratio(total_suppressed, total_events)

    native_clean_signals = {
        "native_policy_clean": int(_dig(data["native_policy"], ["summary", "low_authority_legacy_count"], 1)) == 0,
        "native_trace_clean": data["decision_trace_index"].get("native_trace_clean") is True,
        "native_influence_clean": data["heuristic_influence_map"].get("native_influence_clean") is True,
        "native_matrix_clean": data["entity_no_tick_matrix"].get("native_matrix_clean") is True,
        "native_suppression_clean": data["suppression_ledger"].get("native_suppression_clean") is True,
        "native_calibration_clean": data["tension_decision"].get("native_calibration_clean") is True,
        "native_chronology_clean": data["causal_chronology"].get("native_chronology_clean") is True,
        "native_proof_chain_clean": int(_dig(data["native_proof_chain"], ["seal", "proof_bad"], 1)) == 0,
    }
    native_clean_count = sum(1 for value in native_clean_signals.values() if value)
    if native_clean_count != len(native_clean_signals):
        blockers.append({"code": "NATIVE_PATH_NOT_CLEAN", "signals": native_clean_signals})

    coverage_signals = {
        "trace_coverage_ratio": data["decision_trace_index"].get("trace_coverage_ratio"),
        "entity_coverage_ratio": data["decision_trace_index"].get("entity_coverage_ratio"),
        "decision_proof_coverage_ratio": data["decision_trace_index"].get("proof_coverage_ratio"),
        "decision_heuristic_coverage_ratio": data["decision_trace_index"].get("heuristic_coverage_ratio"),
        "influence_proof_coverage_ratio": data["heuristic_influence_map"].get("proof_event_coverage_ratio"),
        "suppression_proof_coverage_ratio": data["suppression_ledger"].get("proof_coverage_ratio"),
    }
    coverage_clean = all(float(value or 0.0) >= 1.0 for value in coverage_signals.values())
    if not coverage_clean:
        blockers.append({"code": "COVERAGE_NOT_COMPLETE", "signals": coverage_signals})

    causal_signals = {
        "replay_errors": int(data["replay"].get("error_count", 0)),
        "canonical_proof_bad": int(_dig(data["proof_chain"], ["seal", "proof_bad"], 0)),
        "native_proof_bad": int(_dig(data["native_proof_chain"], ["seal", "proof_bad"], 0)),
        "schema_errors": int(data["schema_contract"].get("error_count", 0)),
        "chronology_errors": int(data["causal_chronology"].get("error_count", 0)),
        "graph_errors": len(data["causal_graph"].get("errors", [])),
        "adversarial_failures": int(data["adversarial"].get("failure_count", 0)),
    }
    causal_clean = all(value == 0 for value in causal_signals.values())
    if not causal_clean:
        blockers.append({"code": "CAUSAL_INTEGRITY_BLOCKED", "signals": causal_signals})

    no_tick_signals = {
        "canonical_suppressed_count": canonical_suppressed,
        "native_suppressed_count": native_suppressed,
        "total_suppressed_count": total_suppressed,
        "aggregate_no_tick_suppression_ratio": suppression_ratio,
        "ledger_suppressed_count": data["suppression_ledger"].get("suppressed_count"),
        "ledger_avoided_execution_count": data["suppression_ledger"].get("estimated_avoided_execution_count"),
    }
    no_tick_clean = (
        total_events == int(data["suppression_ledger"].get("event_count", 0))
        and total_suppressed == int(data["suppression_ledger"].get("suppressed_count", -1))
        and total_suppressed == int(data["suppression_ledger"].get("estimated_avoided_execution_count", -1))
        and suppression_ratio >= 0.40
    )
    if not no_tick_clean:
        blockers.append({"code": "NO_TICK_SUPPRESSION_NOT_STABLE", "signals": no_tick_signals})

    authority_signals = {
        "total_strong_decision_count": total_strong,
        "total_strong_with_hard_authority": total_hard,
        "aggregate_hard_authority_ratio": hard_authority_ratio,
        "heuristic_hard_authority_edge_ratio": data["heuristic_influence_map"].get("hard_authority_edge_ratio"),
        "legacy_uncompensated_strong_events": data["heuristic_influence_map"].get("uncompensated_low_authority_strong_event_count"),
    }
    authority_clean = (
        total_strong > 0
        and total_hard == total_strong - canonical_legacy_debt
        and hard_authority_ratio >= 0.85
        and float(data["heuristic_influence_map"].get("hard_authority_edge_ratio", 0.0)) >= 0.65
    )
    if not authority_clean:
        blockers.append({"code": "AUTHORITY_GOVERNANCE_WEAK", "signals": authority_signals})

    legacy_warning_sources = {
        "schema_contract_warning_count": int(data["schema_contract"].get("warning_count", 0)),
        "chronology_warning_count": int(data["causal_chronology"].get("warning_count", 0)),
        "tension_decision_warning_count": int(data["tension_decision"].get("warning_count", 0)),
        "decision_trace_warning_count": int(data["decision_trace_index"].get("warning_count", 0)),
        "heuristic_influence_warning_count": int(data["heuristic_influence_map"].get("warning_count", 0)),
        "entity_no_tick_warning_count": int(data["entity_no_tick_matrix"].get("warning_count", 0)),
        "suppression_ledger_warning_count": int(data["suppression_ledger"].get("warning_count", 0)),
        "maturity_warning_count": int(data["maturity"].get("warning_count", 0)),
    }
    legacy_warning_total = sum(legacy_warning_sources.values())
    if canonical_legacy_debt:
        warnings.append(
            {
                "code": "CANONICAL_LEGACY_DEBT_QUARANTINED",
                "canonical_low_authority_legacy_count": canonical_legacy_debt,
                "native_low_authority_legacy_count": native_legacy_debt,
                "legacy_warning_total": legacy_warning_total,
            }
        )
    if native_legacy_debt:
        blockers.append({"code": "NATIVE_LOW_AUTHORITY_DEBT", "native_low_authority_legacy_count": native_legacy_debt})

    criteria = [
        _criterion(
            "complete_decision_and_proof_coverage",
            coverage_clean,
            15,
            15,
            coverage_signals,
        ),
        _criterion(
            "no_tick_suppression_stability",
            no_tick_clean,
            15,
            15,
            no_tick_signals,
        ),
        _criterion(
            "native_runtime_cleanliness",
            native_clean_count == len(native_clean_signals),
            20,
            20,
            {**native_clean_signals, "clean_count": native_clean_count, "signal_count": len(native_clean_signals)},
        ),
        _criterion(
            "causal_integrity",
            causal_clean,
            15,
            15,
            causal_signals,
        ),
        _criterion(
            "authority_governance",
            authority_clean,
            15,
            15,
            authority_signals,
        ),
        _criterion(
            "legacy_debt_containment",
            canonical_legacy_debt >= 0 and native_legacy_debt == 0 and not blockers,
            7 if canonical_legacy_debt else 10,
            10,
            {
                "canonical_low_authority_legacy_count": canonical_legacy_debt,
                "native_low_authority_legacy_count": native_legacy_debt,
                "legacy_warning_total": legacy_warning_total,
                "policy": "canonical warnings are migration evidence; native debt is a blocker",
            },
        ),
        _criterion(
            "adversarial_detection",
            int(data["adversarial"].get("failure_count", 1)) == 0 and int(data["adversarial"].get("detected_count", 0)) >= 7,
            10,
            10,
            {
                "test_count": data["adversarial"].get("test_count"),
                "detected_count": data["adversarial"].get("detected_count"),
                "failure_count": data["adversarial"].get("failure_count"),
            },
        ),
    ]

    score = sum(int(item["points"]) for item in criteria)
    max_score = sum(int(item["max_points"]) for item in criteria)
    migration_targets = [
        {
            "target": "legacy_observer_h0_strong_decisions",
            "count": canonical_legacy_debt,
            "priority": "high",
            "action": "replace future H0 strong decisions with H2/H3 native authority",
        },
        {
            "target": "low_authority_strong_influence_edges",
            "count": data["heuristic_influence_map"].get("low_authority_strong_edge_count"),
            "priority": "high",
            "action": "migrate legacy strong influence edges to adaptive_threshold, field_scheduler or etev_guard authority",
        },
        {
            "target": "above_threshold_suppression_events",
            "count": data["suppression_ledger"].get("above_threshold_suppression_count"),
            "priority": "medium",
            "action": "re-emit future suppressions through native calibrated tension thresholds",
        },
        {
            "target": "legacy_schema_contract_warnings",
            "count": data["schema_contract"].get("warning_count"),
            "priority": "medium",
            "action": "emit pnva.event.v1 directly instead of relying on bridge normalization",
        },
    ]

    if blockers:
        classification = "SOVEREIGN_ROBUSTNESS_GATE_FAIL"
    elif canonical_legacy_debt or warnings:
        classification = "SOVEREIGN_ROBUSTNESS_GATE_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "SOVEREIGN_ROBUSTNESS_GATE_READY"

    return {
        "schema_version": "pnva.sovereign_robustness_gate.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not blockers,
        "readiness_level": "R2_NATIVE_CLEAN_LEGACY_QUARANTINED" if canonical_legacy_debt else "R3_NATIVE_CLEAN_LEGACY_FREE",
        "robustness_score": score,
        "max_score": max_score,
        "event_count": total_events,
        "suppressed_count": total_suppressed,
        "no_tick_suppression_ratio": suppression_ratio,
        "native_clean_signal_count": native_clean_count,
        "native_clean_signal_total": len(native_clean_signals),
        "legacy_debt_count": canonical_legacy_debt,
        "legacy_warning_total": legacy_warning_total,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "hard_authority_ratio": hard_authority_ratio,
        "criteria": criteria,
        "native_clean_signals": native_clean_signals,
        "legacy_warning_sources": legacy_warning_sources,
        "migration_targets": migration_targets,
        "blockers": blockers,
        "warnings": warnings,
        "reports_checked": REPORTS,
        "summary": {
            "total_event_count": total_events,
            "total_suppressed_count": total_suppressed,
            "aggregate_no_tick_suppression_ratio": suppression_ratio,
            "total_strong_decision_count": total_strong,
            "total_strong_with_hard_authority": total_hard,
            "aggregate_hard_authority_ratio": hard_authority_ratio,
            "native_clean_signal_count": native_clean_count,
            "native_clean_signal_total": len(native_clean_signals),
            "canonical_low_authority_legacy_count": canonical_legacy_debt,
            "native_low_authority_legacy_count": native_legacy_debt,
            "robustness_score": score,
            "max_score": max_score,
        },
        "interpretation": {
            "purpose": "Collapse PNVA no-tick, entities, heuristics, proofs and legacy debt into one production-readiness gate.",
            "sovereignty": "A PNVA runtime is stronger when native execution is clean and legacy risk is explicit, bounded and measurable.",
            "boundary": "This gate validates the published evidence package; it does not claim universal behavior for unmeasured deployments.",
        },
        "recommendations": [
            "Keep this gate after suppression/influence/entity analysis and before evidence attestation.",
            "Treat native cleanliness regressions as blockers, not warnings.",
            "Use migration_targets as the next hardening backlog before claiming legacy-free production status.",
            "Keep no-tick suppression proof-backed and entity-attributed in every new runtime event.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA sovereign robustness gate.")
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
