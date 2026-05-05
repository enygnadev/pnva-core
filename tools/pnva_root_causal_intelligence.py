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

REPORTS = {
    "canonical_no_tick": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native_no_tick": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "runtime_no_tick": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
    "entity_no_tick_matrix": "reports/pnva-entity-no-tick-matrix-2026-05-05.json",
    "heuristic_influence_map": "reports/pnva-heuristic-influence-map-2026-05-05.json",
    "decision_trace_index": "reports/pnva-decision-trace-index-2026-05-05.json",
    "suppression_ledger": "reports/pnva-suppression-ledger-2026-05-05.json",
    "runtime_policy": "reports/pnva-r3-runtime-policy-2026-05-05.json",
    "runtime_events": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
    "runtime_entities": "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json",
    "runtime_capture_matrix": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
    "runtime_evidence_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "sovereign_evolution_ledger": "reports/pnva-sovereign-evolution-ledger-2026-05-05.json",
    "root_sovereignty_guard": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "sovereign_audit": "reports/pnva-sovereign-audit-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "canonical_no_tick": "SOVEREIGN_NO_TICK_READY",
    "native_no_tick": "SOVEREIGN_NO_TICK_READY",
    "runtime_no_tick": "SOVEREIGN_NO_TICK_READY",
    "entity_no_tick_matrix": "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS",
    "heuristic_influence_map": "HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS",
    "decision_trace_index": "DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS",
    "suppression_ledger": "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS",
    "runtime_policy": "SOVEREIGN_POLICY_READY",
    "runtime_capture_matrix": "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE",
    "runtime_evidence_guard": "R3_RUNTIME_EVIDENCE_ACCEPTED",
    "sovereign_evolution_ledger": "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY",
    "root_sovereignty_guard": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                events.append(item)
    return events


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _ratio(part: int | float, total: int | float, digits: int = 6) -> float:
    return round(float(part) / max(1.0, float(total)), digits)


def _classification_ok(data: dict[str, Any], name: str) -> bool:
    expected = EXPECTED_CLASSIFICATIONS[name]
    return data.get("classification") == expected and data.get("pass", True) is not False


def build_report(repo: Path) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for name, rel in REPORTS.items():
        path = repo / rel
        loaded[name] = _read_jsonl(path) if rel.endswith(".jsonl") else _read_json(path)

    runtime_events: list[dict[str, Any]] = loaded["runtime_events"]
    runtime_entities = loaded["runtime_entities"]
    runtime_policy = loaded["runtime_policy"]
    root_guard = loaded["root_sovereignty_guard"]
    audit = loaded["sovereign_audit"]
    ledger = loaded["sovereign_evolution_ledger"]

    classification_checks = {
        name: _classification_ok(loaded[name], name)
        for name in EXPECTED_CLASSIFICATIONS
    }

    no_tick_layers = {
        "canonical": loaded["canonical_no_tick"].get("no_tick_efficiency", {}),
        "native_demo": loaded["native_no_tick"].get("no_tick_efficiency", {}),
        "r3_runtime": loaded["runtime_no_tick"].get("no_tick_efficiency", {}),
    }
    no_tick_event_count = sum(_safe_int(layer.get("event_count")) for layer in no_tick_layers.values())
    no_tick_suppressed_count = sum(_safe_int(layer.get("suppressed_count")) for layer in no_tick_layers.values())
    no_tick_collapse_count = sum(_safe_int(layer.get("collapse_count")) for layer in no_tick_layers.values())
    no_tick_observe_count = sum(_safe_int(layer.get("observe_count")) for layer in no_tick_layers.values())
    no_tick_block_count = sum(_safe_int(layer.get("block_count")) for layer in no_tick_layers.values())

    decision_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    rule_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    entity_counter: Counter[str] = Counter()
    positive_gate_delta = 0
    negative_gate_delta = 0
    native_proof_count = 0
    projected_proof_count = 0

    for event in runtime_events:
        decision_counter[str(_dig(event, ["decision", "kind"], ""))] += 1
        action_counter[str(_dig(event, ["decision", "action"], ""))] += 1
        entity_counter[str(event.get("entity_id", ""))] += 1
        rule_counter.update(str(rule) for rule in _dig(event, ["heuristics", "rules"], []) or [])
        risk_counter.update(str(flag) for flag in _dig(event, ["heuristics", "risk_flags"], []) or [])
        gate_delta = _safe_float(_dig(event, ["tension", "gate_delta"], 0.0))
        positive_gate_delta += 1 if gate_delta > 0 else 0
        negative_gate_delta += 1 if gate_delta < 0 else 0
        native_proof_count += 1 if _dig(event, ["proof", "native"]) is True else 0
        projected_proof_count += 1 if _dig(event, ["proof", "projection"]) is True else 0

    runtime_event_count = len(runtime_events)
    runtime_slot_count = _safe_int(loaded["runtime_capture_matrix"].get("capture_slot_count"))
    runtime_verified_slot_count = _safe_int(loaded["runtime_capture_matrix"].get("verified_runtime_slot_count"))
    runtime_pending_slot_count = _safe_int(loaded["runtime_capture_matrix"].get("pending_slot_count"))
    runtime_no_tick_pair_count = _safe_int(loaded["runtime_evidence_guard"].get("no_tick_pair_integrity_count"))

    runtime_entity_count = _safe_int(runtime_entities.get("entity_count"))
    runtime_observed_entity_count = len([entity for entity in entity_counter if entity])
    runtime_low_authority_legacy_count = _safe_int(_dig(runtime_policy, ["summary", "low_authority_legacy_count"]))
    runtime_strong_decision_count = _safe_int(_dig(runtime_policy, ["summary", "strong_decision_count"]))
    runtime_proof_policy_bad = _safe_int(_dig(runtime_policy, ["summary", "proof_policy_bad"]))
    controlled_warning_count = _safe_int(ledger.get("controlled_warning_count"))

    signals = {
        "classifications_ok": all(classification_checks.values()),
        "root_guard_ready": root_guard.get("classification") == "PNVA_ROOT_SOVEREIGNTY_GUARD_READY" and root_guard.get("pass") is True,
        "runtime_slots_closed": runtime_slot_count == runtime_verified_slot_count == runtime_no_tick_pair_count == 35 and runtime_pending_slot_count == 0,
        "runtime_events_native_non_projected": runtime_event_count == 70 and native_proof_count == 70 and projected_proof_count == 0,
        "runtime_policy_hard_authority_clean": runtime_low_authority_legacy_count == 0 and runtime_strong_decision_count == 35 and runtime_proof_policy_bad == 0,
        "runtime_entity_coverage_clean": runtime_entity_count == runtime_observed_entity_count == 1,
        "runtime_gate_shape_clean": positive_gate_delta == 35 and negative_gate_delta == 35,
        "audit_hygiene_clean": _dig(audit, ["score", "classification"]) == "SOVEREIGN_READY" and _dig(audit, ["score", "total"]) == 100 and not _dig(audit, ["sovereignty", "path_leaks"], []),
    }

    score_parts = {
        "classification_agreement": 15.0 if signals["classifications_ok"] else 0.0,
        "root_guard": 15.0 if signals["root_guard_ready"] else 0.0,
        "no_tick_runtime_pairs": 20.0 if signals["runtime_slots_closed"] else 0.0,
        "native_non_projected_proof": 15.0 if signals["runtime_events_native_non_projected"] else 0.0,
        "heuristic_authority": 15.0 if signals["runtime_policy_hard_authority_clean"] else 0.0,
        "entity_coverage": 10.0 if signals["runtime_entity_coverage_clean"] else 0.0,
        "publication_hygiene": 10.0 if signals["audit_hygiene_clean"] else 0.0,
    }
    root_causal_intelligence_score = round(sum(score_parts.values()), 2)
    failures = [name for name, ok in signals.items() if not ok]
    classification = "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY" if not failures else "PNVA_ROOT_CAUSAL_INTELLIGENCE_NEEDS_HARDENING"

    return {
        "schema_version": "pnva.root_causal_intelligence.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "root_causal_intelligence_score": root_causal_intelligence_score,
        "failure_count": len(failures),
        "failures": failures,
        "score_parts": score_parts,
        "signals": signals,
        "classification_checks": classification_checks,
        "no_tick_aggregate": {
            "event_count": no_tick_event_count,
            "suppressed_count": no_tick_suppressed_count,
            "collapse_count": no_tick_collapse_count,
            "observe_count": no_tick_observe_count,
            "block_count": no_tick_block_count,
            "suppression_ratio": _ratio(no_tick_suppressed_count, no_tick_event_count),
            "causal_execution_ratio": _ratio(no_tick_collapse_count, no_tick_event_count),
            "layers": no_tick_layers,
        },
        "runtime_entity_intelligence": {
            "catalog_entity_count": runtime_entity_count,
            "observed_entity_count": runtime_observed_entity_count,
            "entity_event_mix": sorted(entity_counter.items()),
            "entity_catalog_state": [
                {
                    "entity_id": item.get("entity_id"),
                    "entity_type": item.get("entity_type"),
                    "state": item.get("state"),
                    "capabilities": item.get("capabilities", []),
                    "event_count": _dig(item, ["stats", "event_count"]),
                    "decision_mix": _dig(item, ["stats", "decision_mix"], []),
                    "top_actions": _dig(item, ["stats", "top_actions"], []),
                    "top_rules": _dig(item, ["stats", "top_rules"], []),
                }
                for item in runtime_entities.get("entities", [])
            ],
        },
        "runtime_heuristic_intelligence": {
            "rule_mix": sorted(rule_counter.items()),
            "risk_flag_mix": sorted(risk_counter.items()),
            "strong_decision_count": runtime_strong_decision_count,
            "low_authority_legacy_count": runtime_low_authority_legacy_count,
            "proof_policy_bad": runtime_proof_policy_bad,
            "decision_mix": sorted(decision_counter.items()),
            "action_mix": sorted(action_counter.items()),
            "positive_gate_delta_count": positive_gate_delta,
            "negative_gate_delta_count": negative_gate_delta,
        },
        "controlled_legacy_context": {
            "historical_controlled_warning_count": controlled_warning_count,
            "legacy_debt_count": _safe_int(ledger.get("legacy_debt_count")),
            "low_authority_legacy_count": _safe_int(ledger.get("low_authority_legacy_count")),
            "low_authority_influence_edge_count": _safe_int(ledger.get("low_authority_influence_edge_count")),
            "above_threshold_suppression_count": _safe_int(ledger.get("above_threshold_suppression_count")),
            "boundary": "Historical canonical warnings remain visible as migration context; the R3 runtime path is measured separately and is native-clean.",
        },
        "root_next_actions": [
            "Keep R3 runtime events emitted as one native no-tick precheck plus one native commit per slot.",
            "Keep source.file_name sanitized as a public basename and keep proof.projection=false for runtime evidence.",
            "For future live deployments, add CPU, wakeup and latency counters before claiming hardware-level efficiency gains.",
            "Do not delete historical legacy warnings; replace future weak-authority decisions with native H2/H3 evidence.",
        ],
        "evidence_refs": REPORTS,
        "interpretation": {
            "purpose": "Turn PNVA no-tick logs, heuristic authority and entity coverage into one deterministic root intelligence score.",
            "sovereignty": "The package is more robust when root readiness includes causal efficiency, entity binding, heuristic authority, proof integrity and publication hygiene.",
            "boundary": "This is a deterministic evidence analyzer, not an autonomous AI claim and not a measurement of private deployments outside the public artifacts.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root causal intelligence report.")
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
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
