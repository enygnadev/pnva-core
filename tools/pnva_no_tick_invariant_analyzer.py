#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HEURISTIC_CLASSES = {
    "legacy_observer": "H0_OBSERVATION_ONLY",
    "veonic_layer": "H1_ADVISORY_SIGNAL",
    "memory4d": "H1_ADVISORY_MEMORY",
    "adaptive_threshold": "H2_GUARDED_THRESHOLD",
    "affinity_router": "H2_GUARDED_ROUTING",
    "field_scheduler": "H2_GUARDED_ACTION",
    "power_orchestrator": "H2_GUARDED_ACTION",
    "etev_guard": "H3_SOVEREIGN_GUARD",
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def _ratio(part: int | float, total: int | float) -> float:
    return _round(float(part) / max(1.0, float(total)))


def _load_events(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except Exception as exc:
                errors.append({"line": line_no, "code": "JSON_PARSE_ERROR", "message": str(exc)})
                continue
            if not isinstance(data, dict):
                errors.append({"line": line_no, "code": "EVENT_NOT_OBJECT"})
                continue
            data["_line"] = line_no
            events.append(data)
    return events, errors


def _load_entities(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    data = _load_json(path)
    entities = data.get("entities", []) if isinstance(data, dict) else []
    result: dict[str, dict[str, Any]] = {}
    for item in entities:
        if isinstance(item, dict) and item.get("entity_id"):
            result[str(item["entity_id"])] = item
    return result


def _load_replay_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "pass": False,
            "classification": "REPLAY_REPORT_MISSING",
            "errors": ["missing replay report"],
            "warnings": [],
            "summary": {},
        }
    data = _load_json(path)
    if not isinstance(data, dict):
        return {
            "pass": False,
            "classification": "REPLAY_REPORT_INVALID",
            "errors": ["invalid replay report"],
            "warnings": [],
            "summary": {},
        }
    return data


def _decision_kind(event: dict[str, Any]) -> str:
    decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
    return str(decision.get("kind") or "unknown")


def _decision_action(event: dict[str, Any]) -> str:
    decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
    return str(decision.get("action") or "")


def _event_rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    rules = heuristics.get("rules", [])
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _event_risks(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    flags = heuristics.get("risk_flags", [])
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _entity_health(events: list[dict[str, Any]], entity_catalog: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        grouped[str(event.get("entity_id") or "unknown")].append(event)

    health: list[dict[str, Any]] = []
    for entity_id, entity_events in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        decisions = Counter(_decision_kind(event) for event in entity_events)
        actions = Counter(_decision_action(event) for event in entity_events)
        risks = Counter(flag for event in entity_events for flag in _event_risks(event))
        rules = Counter(rule for event in entity_events for rule in _event_rules(event))
        event_count = len(entity_events)
        block_ratio = _ratio(decisions.get("block", 0), event_count)
        risk_ratio = _ratio(sum(risks.values()), event_count)
        status = "sovereign_active" if event_count >= 10 else "observed"
        attention: list[str] = []
        if block_ratio >= 0.35:
            status = "guarded"
            attention.append("HIGH_BLOCK_RATIO")
        if risk_ratio >= 0.75:
            status = "pressure_visible"
            attention.append("HIGH_RISK_FLAG_DENSITY")
        if entity_id not in entity_catalog:
            status = "catalog_missing"
            attention.append("MISSING_ENTITY_CATALOG_ENTRY")
        health.append(
            {
                "entity_id": entity_id,
                "entity_type": str(entity_catalog.get(entity_id, {}).get("entity_type") or "unknown"),
                "status": status,
                "event_count": event_count,
                "decision_mix": decisions.most_common(),
                "top_actions": actions.most_common(8),
                "top_rules": rules.most_common(8),
                "risk_flags": risks.most_common(8),
                "block_ratio": block_ratio,
                "risk_flag_density": risk_ratio,
                "attention": attention,
            }
        )
    return health


def _invariant(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "evidence": evidence,
    }


def build_report(events_path: Path, entity_catalog_path: Path, replay_report_path: Path) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    entity_catalog = _load_entities(entity_catalog_path)
    replay = _load_replay_summary(replay_report_path)
    replay_summary = replay.get("summary", {}) if isinstance(replay.get("summary"), dict) else {}
    event_count = len(events)
    decision_kinds = Counter(_decision_kind(event) for event in events)
    actions = Counter(_decision_action(event) for event in events)
    event_types = Counter(str(event.get("event_type") or "") for event in events)
    chains = Counter(str(event.get("causal_chain_id") or "") for event in events)
    entity_ids = {str(event.get("entity_id") or "") for event in events}
    missing_entities = sorted(entity_id for entity_id in entity_ids if entity_id and entity_id not in entity_catalog)
    rules = Counter(rule for event in events for rule in _event_rules(event))
    risks = Counter(flag for event in events for flag in _event_risks(event))

    collapse_count = decision_kinds.get("collapse", 0)
    observe_count = decision_kinds.get("observe", 0)
    block_count = decision_kinds.get("block", 0)
    suppressed_count = observe_count + block_count
    guard_event_count = sum(count for event_type, count in event_types.items() if "ETEV_GUARD" in event_type)
    guard_ok = int(replay_summary.get("guard_pass_ok", 0)) + int(replay_summary.get("guard_block_ok", 0))
    proof_hash_bad = int(replay_summary.get("proof_hash_bad", 0))
    proof_hash_ok = int(replay_summary.get("proof_hash_ok", 0))

    classified_rules = {
        rule: {
            "class": HEURISTIC_CLASSES.get(rule, "H1_ADVISORY_SIGNAL"),
            "count": count,
        }
        for rule, count in sorted(rules.items())
    }

    invariants = [
        _invariant(
            "CANONICAL_SCHEMA_REPLAYED",
            replay.get("pass") is True and not parse_errors and event_count > 0,
            {"replay_classification": replay.get("classification"), "parse_errors": len(parse_errors), "event_count": event_count},
        ),
        _invariant(
            "PROOF_HASH_STABLE",
            proof_hash_bad == 0 and proof_hash_ok == event_count,
            {"proof_hash_ok": proof_hash_ok, "proof_hash_bad": proof_hash_bad},
        ),
        _invariant(
            "NO_TICK_SUPPRESSION_OBSERVED",
            suppressed_count > 0 and _ratio(suppressed_count, event_count) >= 0.10,
            {"suppressed_count": suppressed_count, "suppression_ratio": _ratio(suppressed_count, event_count)},
        ),
        _invariant(
            "GUARD_COLLAPSE_BLOCK_CONSISTENT",
            guard_event_count > 0 and guard_ok == guard_event_count,
            {"guard_event_count": guard_event_count, "guard_validated": guard_ok},
        ),
        _invariant(
            "ENTITY_CATALOG_COVERS_EVENTS",
            not missing_entities and len(entity_catalog) > 0,
            {"catalog_entity_count": len(entity_catalog), "observed_entity_count": len(entity_ids), "missing_entities": missing_entities},
        ),
        _invariant(
            "HEURISTIC_VISIBILITY_PRESENT",
            bool(rules) and bool(risks),
            {"rule_count": sum(rules.values()), "risk_flag_count": sum(risks.values()), "top_rules": rules.most_common(8), "top_risks": risks.most_common(8)},
        ),
        _invariant(
            "PUBLIC_SAFE_EVENT_REFERENCES",
            all(str(event.get("source", {}).get("file_name", "")).find("/") == -1 for event in events if isinstance(event.get("source"), dict)),
            {"checked_events": event_count, "policy": "source.file_name must be basename only"},
        ),
    ]

    failed = [item["name"] for item in invariants if not item["pass"]]
    no_tick_efficiency = {
        "event_count": event_count,
        "collapse_count": collapse_count,
        "observe_count": observe_count,
        "block_count": block_count,
        "suppressed_count": suppressed_count,
        "causal_execution_ratio": _ratio(collapse_count, event_count),
        "no_tick_suppression_ratio": _ratio(suppressed_count, event_count),
        "guard_consistency_ratio": _ratio(guard_ok, guard_event_count),
        "proof_integrity_ratio": _ratio(proof_hash_ok, event_count),
    }

    return {
        "schema_version": "pnva.no_tick_invariants.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "events_ref": str(events_path),
        "entity_catalog_ref": str(entity_catalog_path),
        "replay_report_ref": str(replay_report_path),
        "pass": not failed,
        "classification": "SOVEREIGN_NO_TICK_READY" if not failed else "NO_TICK_NEEDS_HARDENING",
        "failed_invariants": failed,
        "parse_errors": parse_errors,
        "invariants": invariants,
        "no_tick_efficiency": no_tick_efficiency,
        "heuristic_classes": classified_rules,
        "entity_health": _entity_health(events, entity_catalog),
        "summary": {
            "event_count": event_count,
            "entity_count_catalog": len(entity_catalog),
            "entity_count_observed": len(entity_ids),
            "causal_chain_count": len(chains),
            "top_chains": chains.most_common(8),
            "top_event_types": event_types.most_common(12),
            "top_decisions": decision_kinds.most_common(8),
            "top_actions": actions.most_common(12),
            "top_risk_flags": risks.most_common(12),
            "top_heuristic_rules": rules.most_common(12),
        },
        "interpretation": {
            "no_tick": "Observe and block decisions are counted as causal suppression because the runtime records why it did not execute.",
            "heuristics": "Heuristics are not treated as magic intelligence; each rule is classified by allowed authority level.",
            "entities": "Entity health is derived from canonical event evidence and does not expose raw local identifiers.",
        },
        "recommendations": [
            "Emit pnva.event.v1 directly from the runtime so replay validation does not depend on a legacy bridge.",
            "Promote guard and thermal pressure into explicit runtime entities when sensor provenance is available.",
            "Keep observe/block records; they are the audit trail that proves no-tick suppression without hiding decisions.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze PNVA no-tick invariants over canonical events, entities and replay proof.")
    parser.add_argument("--events", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-entity-catalog-2026-05-05.json")
    parser.add_argument("--replay-report", default="reports/pnva-replay-validation-2026-05-05.json")
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_catalog_path = Path(args.entity_catalog)
    if not entity_catalog_path.is_absolute():
        entity_catalog_path = repo / entity_catalog_path
    replay_report_path = Path(args.replay_report)
    if not replay_report_path.is_absolute():
        replay_report_path = repo / replay_report_path

    report = build_report(events_path, entity_catalog_path, replay_report_path)
    for key in ("events_ref", "entity_catalog_ref", "replay_report_ref"):
        path = Path(str(report[key]))
        report[key] = str(path.relative_to(repo)) if path.is_relative_to(repo) else path.name
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
