#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


REPORTS = {
    "robustness_gate": "reports/pnva-sovereign-robustness-gate-2026-05-05.json",
    "heuristic_influence_map": "reports/pnva-heuristic-influence-map-2026-05-05.json",
    "entity_no_tick_matrix": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
    "suppression_ledger": "reports/pnva-suppression-ledger-2026-05-05.json",
    "schema_contract": "reports/pnva-schema-contract-validation-2026-05-05.json",
    "maturity": "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
    "decision_trace_index": "reports/pnva-decision-trace-index-2026-05-05.json",
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


def _action(
    *,
    action_id: str,
    title: str,
    current_count: int,
    target_count: int,
    priority: str,
    source: str,
    required_for_r3: bool,
    recommended_change: str,
    validation_command: str,
    success_metric: str,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "title": title,
        "current_count": int(current_count),
        "target_count": int(target_count),
        "remaining_count": max(0, int(current_count) - int(target_count)),
        "priority": priority,
        "source": source,
        "required_for_r3": bool(required_for_r3),
        "recommended_change": recommended_change,
        "validation_command": validation_command,
        "success_metric": success_metric,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    data = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    blockers: list[dict[str, Any]] = []

    robustness = data["robustness_gate"]
    influence = data["heuristic_influence_map"]
    matrix = data["entity_no_tick_matrix"]
    suppression = data["suppression_ledger"]
    schema = data["schema_contract"]
    maturity = data["maturity"]
    trace = data["decision_trace_index"]

    source_event_count = int(robustness.get("event_count", 0))
    native_clean_count = int(robustness.get("native_clean_signal_count", 0))
    native_clean_total = int(robustness.get("native_clean_signal_total", 0))
    primary_debt = int(robustness.get("legacy_debt_count", 0))
    low_authority_edges = int(influence.get("low_authority_strong_edge_count", 0))
    above_threshold_suppression = int(suppression.get("above_threshold_suppression_count", 0))
    schema_warnings = int(schema.get("warning_count", 0))
    trace_low_authority = int(trace.get("low_authority_trace_count", 0))
    matrix_legacy = int(matrix.get("legacy_low_authority_warning_count", 0))

    if robustness.get("pass") is not True:
        blockers.append({"code": "ROBUSTNESS_GATE_NOT_PASSING"})
    if native_clean_count != native_clean_total:
        blockers.append(
            {
                "code": "NATIVE_PATH_NOT_CLEAN",
                "native_clean_signal_count": native_clean_count,
                "native_clean_signal_total": native_clean_total,
            }
        )

    actions = [
        _action(
            action_id="R3-A1",
            title="Replace H0 strong legacy decisions with native H2/H3 authority",
            current_count=primary_debt,
            target_count=0,
            priority="critical",
            source="robustness_gate.legacy_debt_count",
            required_for_r3=True,
            recommended_change="Future strong decisions must be emitted by native pnva.event.v1 runtime rules such as adaptive_threshold, field_scheduler or etev_guard instead of legacy_observer.",
            validation_command="python3 tools/pnva_sovereign_policy_validator.py --events reports/pnva-native-events-demo-2026-05-05.jsonl --entity-catalog reports/pnva-native-entity-catalog-demo-2026-05-05.json",
            success_metric="canonical_low_authority_legacy_count=0 and native_low_authority_legacy_count=0",
        ),
        _action(
            action_id="R3-A2",
            title="Migrate low-authority strong heuristic influence edges",
            current_count=low_authority_edges,
            target_count=0,
            priority="high",
            source="heuristic_influence_map.low_authority_strong_edge_count",
            required_for_r3=True,
            recommended_change="Strong influence edges should be covered by H2/H3/H4 rules; H0/H1 may remain contextual but not decisive.",
            validation_command="python3 tools/pnva_heuristic_influence_map.py --write /tmp/pnva-heuristic-influence-map.json",
            success_metric="low_authority_strong_edge_count=0 and native_influence_clean=true",
        ),
        _action(
            action_id="R3-A3",
            title="Re-emit above-threshold suppressions through native calibrated thresholds",
            current_count=above_threshold_suppression,
            target_count=0,
            priority="high",
            source="suppression_ledger.above_threshold_suppression_count",
            required_for_r3=True,
            recommended_change="Future suppression events should carry calibrated gate_delta/threshold semantics so non-execution remains proof-backed and below-threshold in native scope.",
            validation_command="python3 tools/pnva_suppression_ledger.py --write /tmp/pnva-suppression-ledger.json",
            success_metric="above_threshold_suppression_count=0 for new native evidence and native_suppression_clean=true",
        ),
        _action(
            action_id="R3-A4",
            title="Emit pnva.event.v1 directly instead of relying on bridge normalization",
            current_count=schema_warnings,
            target_count=0,
            priority="medium",
            source="schema_contract.warning_count",
            required_for_r3=True,
            recommended_change="Runtime emitters should write schema_version, event_id, entity_id, causal_chain_id, decision, tension, heuristics and proof directly.",
            validation_command="python3 tools/pnva_schema_contract_validator.py --write /tmp/pnva-schema-contract-validation.json",
            success_metric="schema_contract warning_count=0 for new native packages",
        ),
        _action(
            action_id="R3-A5",
            title="Reduce low-authority trace debt in public decision index",
            current_count=trace_low_authority,
            target_count=0,
            priority="medium",
            source="decision_trace_index.low_authority_trace_count",
            required_for_r3=False,
            recommended_change="Keep legacy trace debt visible, but use native H2/H3 traces as the forward path for every new production sample.",
            validation_command="python3 tools/pnva_decision_trace_index.py --write /tmp/pnva-decision-trace-index.json",
            success_metric="low_authority_trace_count=0 for new native packages and trace_coverage_ratio=1.0",
        ),
        _action(
            action_id="R3-A6",
            title="Keep entity no-tick migration debt bounded by actor",
            current_count=matrix_legacy,
            target_count=0,
            priority="medium",
            source="entity_no_tick_matrix.legacy_low_authority_warning_count",
            required_for_r3=False,
            recommended_change="Every future suppression/execution row should remain attributable to a cataloged entity and a hard-authority rule.",
            validation_command="python3 tools/pnva_entity_no_tick_matrix.py --write /tmp/pnva-entity-no-tick-matrix.json",
            success_metric="legacy_low_authority_warning_count=0 for new native packages and native_matrix_clean=true",
        ),
    ]

    required_actions = [item for item in actions if item["required_for_r3"]]
    completed_required = [item for item in required_actions if item["remaining_count"] == 0]
    raw_migration_signal_count = sum(int(item["remaining_count"]) for item in actions)
    primary_required_remaining = sum(int(item["remaining_count"]) for item in required_actions)
    estimated_r3_candidate = not blockers and primary_required_remaining == 0

    hard_authority_ratio = float(_dig(maturity, ["summary", "aggregate_hard_authority_ratio"], 0.0))
    suppression_ratio = float(_dig(maturity, ["summary", "aggregate_no_tick_suppression_ratio"], 0.0))
    classification = "R3_MIGRATION_PLAN_READY" if not blockers else "R3_MIGRATION_PLAN_FAIL"

    return {
        "schema_version": "pnva.r3_migration_plan.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not blockers,
        "current_readiness_level": robustness.get("readiness_level"),
        "target_readiness_level": "R3_NATIVE_CLEAN_LEGACY_FREE",
        "current_robustness_score": int(robustness.get("robustness_score", 0)),
        "target_robustness_score": 100,
        "source_event_count": source_event_count,
        "native_clean_signal_count": native_clean_count,
        "native_clean_signal_total": native_clean_total,
        "primary_blocking_debt_count": primary_debt,
        "required_action_count": len(required_actions),
        "completed_required_action_count": len(completed_required),
        "migration_action_count": len(actions),
        "raw_migration_signal_count": raw_migration_signal_count,
        "primary_required_remaining_count": primary_required_remaining,
        "estimated_r3_candidate": estimated_r3_candidate,
        "blocker_count": len(blockers),
        "warning_count": 0 if estimated_r3_candidate else 1,
        "actions": actions,
        "blockers": blockers,
        "summary": {
            "source_event_count": source_event_count,
            "current_readiness_level": robustness.get("readiness_level"),
            "target_readiness_level": "R3_NATIVE_CLEAN_LEGACY_FREE",
            "current_robustness_score": int(robustness.get("robustness_score", 0)),
            "target_robustness_score": 100,
            "native_clean_signal_count": native_clean_count,
            "native_clean_signal_total": native_clean_total,
            "primary_blocking_debt_count": primary_debt,
            "low_authority_strong_edge_count": low_authority_edges,
            "above_threshold_suppression_count": above_threshold_suppression,
            "schema_contract_warning_count": schema_warnings,
            "raw_migration_signal_count": raw_migration_signal_count,
            "primary_required_remaining_count": primary_required_remaining,
            "aggregate_hard_authority_ratio": hard_authority_ratio,
            "aggregate_no_tick_suppression_ratio": suppression_ratio,
            "estimated_r3_candidate": estimated_r3_candidate,
        },
        "reports_checked": REPORTS,
        "interpretation": {
            "purpose": "Turn PNVA R2 legacy debt into a measurable migration backlog for R3 readiness.",
            "sovereignty": "A stronger PNVA release should expose not only what passes, but exactly what remains to become legacy-free.",
            "boundary": "Counts are migration signals across overlapping reports; raw_migration_signal_count is not a de-duplicated event count.",
        },
        "recommendations": [
            "Treat R3-A1 as the release-critical migration target.",
            "Do not erase legacy evidence; replace future runtime emissions with native H2/H3 authority.",
            "Use this report as the engineering backlog before claiming R3_NATIVE_CLEAN_LEGACY_FREE.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA R3 migration plan from published robustness evidence.")
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
