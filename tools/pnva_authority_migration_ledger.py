#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


CANONICAL_EVENTS = "reports/pnva-canonical-events-sample-2026-05-05.jsonl"
NATIVE_EVENTS = "reports/pnva-native-events-demo-2026-05-05.jsonl"
R3_REPORT = "reports/pnva-r3-migration-plan-2026-05-05.json"
POLICY_REPORT = "reports/pnva-sovereign-policy-2026-05-05.json"
INFLUENCE_REPORT = "reports/pnva-heuristic-influence-map-2026-05-05.json"

RULE_AUTHORITY = {
    "legacy_observer": "H0",
    "veonic_layer": "H1",
    "memory4d": "H1",
    "native_event_emitter": "H2",
    "adaptive_threshold": "H2",
    "affinity_router": "H2",
    "field_scheduler": "H2",
    "power_orchestrator": "H2",
    "etev_guard": "H3",
}

AUTHORITY_ORDER = {"H0": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4}
HARD_AUTHORITIES = {"H2", "H3", "H4"}
STRONG_DECISIONS = {"collapse", "block", "prove", "reclassify"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path, scope: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"{scope}:{line_no}: event is not an object")
            event["_line"] = line_no
            event["_scope"] = scope
            events.append(event)
    return events


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    rules = heuristics.get("rules")
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _risk_flags(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    flags = heuristics.get("risk_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _decision_kind(event: dict[str, Any]) -> str:
    return str(_decision(event).get("kind") or "unknown")


def _decision_action(event: dict[str, Any]) -> str:
    return str(_decision(event).get("action") or "unknown")


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda level: AUTHORITY_ORDER[level])


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    if not isinstance(proof, dict):
        return False
    return (
        proof.get("valid") is True
        and str(proof.get("proof_hash") or "").startswith("sha256:")
        and bool(proof.get("proof_ref"))
    )


def _safe_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except Exception:
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _tension(event: dict[str, Any], key: str) -> float | None:
    tension = event.get("tension")
    if not isinstance(tension, dict):
        return None
    return _safe_float(tension.get(key))


def _components(event: dict[str, Any]) -> dict[str, Any]:
    tension = event.get("tension")
    if not isinstance(tension, dict):
        return {}
    components = tension.get("components")
    return components if isinstance(components, dict) else {}


def _source_file(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        return ""
    return str(source.get("file_name") or "")


def _mean(values: list[float]) -> float:
    return round(statistics.mean(values), 6) if values else 0.0


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _coverage(part: int | float, total: int | float) -> float:
    if float(total) == 0.0:
        return 1.0
    return _ratio(part, total)


def _recommendation_for(event: dict[str, Any]) -> dict[str, Any]:
    action = _decision_action(event)
    risk_flags = set(_risk_flags(event))
    event_type = str(event.get("event_type") or "")
    base_rules = ["adaptive_threshold", "field_scheduler"]
    reason = "calibrate_threshold_and_schedule_by_field_state"

    if action == "COOLDOWN_GPU" or any("THERMAL" in flag or "COOLDOWN" in flag for flag in risk_flags):
        base_rules = ["power_orchestrator", "field_scheduler", "adaptive_threshold"]
        reason = "route_cooling_through_power_and_scheduler_authority"
    elif action == "EXECUTE":
        base_rules = ["adaptive_threshold", "field_scheduler"]
        reason = "execute_only_when_native_threshold_and_scheduler_agree"
    elif action == "RESIZE_BATCH":
        base_rules = ["adaptive_threshold", "field_scheduler"]
        if "RESIZE_BATCH_PRESSURE" in risk_flags:
            reason = "replace_resize_pressure_observation_with_native_threshold_scheduler_pair"

    if event_type.upper().startswith("ETEV_GUARD"):
        base_rules = ["etev_guard", "adaptive_threshold", "field_scheduler"]
        reason = "guard_events_require_h3_etev_authority"

    target_authorities = [_authority(rule) for rule in base_rules]
    return {
        "target_rules": base_rules,
        "target_max_authority": _max_authority(base_rules),
        "target_authorities": target_authorities,
        "native_event_requirement": "emit pnva.event.v1 directly with hard-authority rules, proof hash and causal_chain_id",
        "reason": reason,
    }


def _is_low_authority_strong(event: dict[str, Any]) -> bool:
    return _decision_kind(event) in STRONG_DECISIONS and _max_authority(_rules(event)) not in HARD_AUTHORITIES


def _candidate_ref(event: dict[str, Any]) -> dict[str, Any]:
    recommendation = _recommendation_for(event)
    components = _components(event)
    return {
        "event_id": event.get("event_id"),
        "line": int(event.get("_line", 0)),
        "entity_id": event.get("entity_id"),
        "entity_type": event.get("entity_type"),
        "event_type": event.get("event_type"),
        "source_file": _source_file(event),
        "decision_kind": _decision_kind(event),
        "decision_action": _decision_action(event),
        "risk_flags": _risk_flags(event),
        "current_rules": _rules(event),
        "current_max_authority": _max_authority(_rules(event)),
        "target_rules": recommendation["target_rules"],
        "target_max_authority": recommendation["target_max_authority"],
        "score": _tension(event, "score"),
        "threshold": _tension(event, "threshold"),
        "gate_delta": _tension(event, "gate_delta"),
        "hash4d_score": _safe_float(components.get("hash4d_score")),
        "raw_mhs": _safe_float(components.get("raw_mhs")),
        "proof_valid": _proof_ok(event),
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    canonical_events = _load_jsonl(repo / CANONICAL_EVENTS, "canonical")
    native_events = _load_jsonl(repo / NATIVE_EVENTS, "native")
    r3 = _read_json(repo / R3_REPORT)
    policy = _read_json(repo / POLICY_REPORT)
    influence = _read_json(repo / INFLUENCE_REPORT)

    canonical_candidates = [event for event in canonical_events if _is_low_authority_strong(event)]
    native_candidates = [event for event in native_events if _is_low_authority_strong(event)]
    candidate_refs = [_candidate_ref(event) for event in canonical_candidates]

    by_entity: dict[str, dict[str, Any]] = {}
    entity_action_counter: Counter[tuple[str, str]] = Counter()
    action_counter: Counter[str] = Counter()
    event_type_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    target_rule_counter: Counter[str] = Counter()
    gate_deltas: list[float] = []
    scores: list[float] = []

    for event in canonical_candidates:
        entity_id = str(event.get("entity_id") or "unknown")
        action = _decision_action(event)
        event_type = str(event.get("event_type") or "unknown")
        source_file = _source_file(event) or "unknown"
        recommendation = _recommendation_for(event)
        row = by_entity.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "candidate_count": 0,
                "event_types": Counter(),
                "decision_actions": Counter(),
                "source_files": Counter(),
                "risk_flags": Counter(),
                "target_rules": Counter(),
                "proof_valid_count": 0,
                "gate_deltas": [],
                "scores": [],
            },
        )
        row["candidate_count"] += 1
        row["event_types"][event_type] += 1
        row["decision_actions"][action] += 1
        row["source_files"][source_file] += 1
        if _proof_ok(event):
            row["proof_valid_count"] += 1
        for flag in _risk_flags(event):
            row["risk_flags"][flag] += 1
            risk_counter[flag] += 1
        for rule in recommendation["target_rules"]:
            row["target_rules"][rule] += 1
            target_rule_counter[rule] += 1
        entity_action_counter[(entity_id, action)] += 1
        action_counter[action] += 1
        event_type_counter[event_type] += 1
        source_counter[source_file] += 1
        gate_delta = _tension(event, "gate_delta")
        score = _tension(event, "score")
        if gate_delta is not None:
            row["gate_deltas"].append(gate_delta)
            gate_deltas.append(gate_delta)
        if score is not None:
            row["scores"].append(score)
            scores.append(score)

    entity_rows = []
    for row in by_entity.values():
        count = int(row["candidate_count"])
        entity_rows.append(
            {
                "entity_id": row["entity_id"],
                "candidate_count": count,
                "proof_valid_count": int(row["proof_valid_count"]),
                "proof_coverage_ratio": _coverage(int(row["proof_valid_count"]), count),
                "event_types": row["event_types"].most_common(),
                "decision_actions": row["decision_actions"].most_common(),
                "source_files": row["source_files"].most_common(),
                "risk_flags": row["risk_flags"].most_common(),
                "target_rules": row["target_rules"].most_common(),
                "gate_delta_mean": _mean(row["gate_deltas"]),
                "score_mean": _mean(row["scores"]),
            }
        )
    entity_rows.sort(key=lambda item: (-int(item["candidate_count"]), str(item["entity_id"])))

    action_rows = []
    for (entity_id, action), count in entity_action_counter.most_common():
        matching = [event for event in canonical_candidates if str(event.get("entity_id")) == entity_id and _decision_action(event) == action]
        target_rules = Counter(rule for event in matching for rule in _recommendation_for(event)["target_rules"])
        action_rows.append(
            {
                "entity_id": entity_id,
                "decision_action": action,
                "candidate_count": count,
                "event_types": Counter(str(event.get("event_type") or "unknown") for event in matching).most_common(),
                "risk_flags": Counter(flag for event in matching for flag in _risk_flags(event)).most_common(),
                "target_rules": target_rules.most_common(),
                "target_max_authority": _max_authority(list(target_rules)),
                "implementation_target": "native pnva.event.v1 emission with calibrated threshold, entity_id, causal_chain_id and proof hash",
            }
        )

    proof_valid_count = sum(1 for event in canonical_candidates if _proof_ok(event))
    unmapped_count = sum(1 for ref in candidate_refs if not ref["target_rules"] or ref["target_max_authority"] not in HARD_AUTHORITIES)
    r3_primary = int(r3.get("primary_blocking_debt_count", 0))
    policy_low = int(policy.get("summary", {}).get("low_authority_legacy_count", 0))
    influence_uncompensated = int(influence.get("uncompensated_low_authority_strong_event_count", 0))
    candidate_count = len(canonical_candidates)
    native_candidate_count = len(native_candidates)
    errors: list[dict[str, Any]] = []

    if candidate_count != r3_primary:
        errors.append({"code": "CANDIDATE_COUNT_MISMATCH_R3", "candidate_count": candidate_count, "r3_primary_blocking_debt_count": r3_primary})
    if candidate_count != policy_low:
        errors.append({"code": "CANDIDATE_COUNT_MISMATCH_POLICY", "candidate_count": candidate_count, "policy_low_authority_legacy_count": policy_low})
    if candidate_count != influence_uncompensated:
        errors.append({"code": "CANDIDATE_COUNT_MISMATCH_INFLUENCE", "candidate_count": candidate_count, "influence_uncompensated_count": influence_uncompensated})
    if native_candidate_count:
        errors.append({"code": "NATIVE_LOW_AUTHORITY_STRONG_DEBT", "native_low_authority_strong_count": native_candidate_count})
    if unmapped_count:
        errors.append({"code": "UNMAPPED_AUTHORITY_MIGRATION_CANDIDATES", "unmapped_candidate_count": unmapped_count})
    if proof_valid_count != candidate_count:
        errors.append({"code": "CANDIDATE_PROOF_COVERAGE_GAP", "proof_valid_count": proof_valid_count, "candidate_count": candidate_count})

    classification = "AUTHORITY_MIGRATION_LEDGER_READY_WITH_LEGACY_WARNINGS"
    if errors:
        classification = "AUTHORITY_MIGRATION_LEDGER_FAIL"
    elif candidate_count == 0:
        classification = "AUTHORITY_MIGRATION_LEDGER_READY"

    return {
        "schema_version": "pnva.authority_migration_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "source_event_count": len(canonical_events) + len(native_events),
        "canonical_event_count": len(canonical_events),
        "native_event_count": len(native_events),
        "candidate_event_count": candidate_count,
        "canonical_low_authority_strong_count": candidate_count,
        "native_low_authority_strong_count": native_candidate_count,
        "r3_primary_blocking_debt_count": r3_primary,
        "policy_low_authority_legacy_count": policy_low,
        "influence_uncompensated_low_authority_strong_event_count": influence_uncompensated,
        "candidate_event_count_matches_r3": candidate_count == r3_primary,
        "entity_candidate_count": len(by_entity),
        "action_candidate_count": len(action_counter),
        "event_type_candidate_count": len(event_type_counter),
        "source_file_candidate_count": len(source_counter),
        "mapped_candidate_count": candidate_count - unmapped_count,
        "unmapped_candidate_count": unmapped_count,
        "migration_coverage_ratio": _coverage(candidate_count - unmapped_count, candidate_count),
        "proof_valid_count": proof_valid_count,
        "proof_coverage_ratio": _coverage(proof_valid_count, candidate_count),
        "warning_count": candidate_count,
        "error_count": len(errors),
        "errors": errors,
        "summary": {
            "candidate_event_count": candidate_count,
            "native_low_authority_strong_count": native_candidate_count,
            "entity_candidate_count": len(by_entity),
            "action_candidate_count": len(action_counter),
            "dominant_entity": entity_rows[0]["entity_id"] if entity_rows else "",
            "dominant_entity_candidate_count": entity_rows[0]["candidate_count"] if entity_rows else 0,
            "dominant_action": action_counter.most_common(1)[0][0] if action_counter else "",
            "dominant_action_count": action_counter.most_common(1)[0][1] if action_counter else 0,
            "dominant_event_type": event_type_counter.most_common(1)[0][0] if event_type_counter else "",
            "dominant_event_type_count": event_type_counter.most_common(1)[0][1] if event_type_counter else 0,
            "migration_coverage_ratio": _coverage(candidate_count - unmapped_count, candidate_count),
            "proof_coverage_ratio": _coverage(proof_valid_count, candidate_count),
            "gate_delta_mean": _mean(gate_deltas),
            "score_mean": _mean(scores),
        },
        "entity_rows": entity_rows,
        "action_rows": action_rows,
        "candidate_samples": candidate_refs[:12],
        "top_decision_actions": action_counter.most_common(),
        "top_event_types": event_type_counter.most_common(),
        "top_source_files": source_counter.most_common(),
        "top_risk_flags": risk_counter.most_common(),
        "target_rule_mix": target_rule_counter.most_common(),
        "reports_checked": {
            "canonical_events": CANONICAL_EVENTS,
            "native_events": NATIVE_EVENTS,
            "r3_migration_plan": R3_REPORT,
            "sovereign_policy": POLICY_REPORT,
            "heuristic_influence_map": INFLUENCE_REPORT,
        },
        "interpretation": {
            "purpose": "Convert PNVA low-authority strong legacy decisions into entity/action-specific native authority migration targets.",
            "sovereignty": "A no-tick system becomes more robust when every remaining H0 strong decision has a hard-authority replacement path.",
            "boundary": "This ledger does not rewrite historical evidence; it defines the exact native emission targets for future R3 evidence.",
        },
        "recommendations": [
            "Migrate the dominant entity/action pair first because it carries the entire primary R3 authority debt.",
            "For future native runtime samples, emit RESIZE_BATCH through adaptive_threshold plus field_scheduler instead of legacy_observer.",
            "Keep legacy evidence preserved, but require H2/H3 authority and proof hash for every new strong decision.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an authority migration ledger for PNVA R3 hardening.")
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
