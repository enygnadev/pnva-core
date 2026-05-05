#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SCOPES = {
    "canonical": {
        "events": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
        "entities": "reports/pnva-entity-catalog-2026-05-05.json",
        "legacy_tolerant": True,
    },
    "native": {
        "events": "reports/pnva-native-events-demo-2026-05-05.jsonl",
        "entities": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
        "legacy_tolerant": False,
    },
}

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
SUPPRESSED_DECISIONS = {"observe", "block"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_entities(path: Path, scope: str) -> tuple[set[str], list[dict[str, Any]]]:
    if not path.exists():
        return set(), [{"code": "ENTITY_CATALOG_MISSING", "scope": scope, "path": str(path)}]
    data = _load_json(path)
    if not isinstance(data, dict):
        return set(), [{"code": "ENTITY_CATALOG_INVALID", "scope": scope, "path": str(path)}]
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return set(), [{"code": "ENTITY_LIST_INVALID", "scope": scope, "path": str(path)}]
    ids = {str(item.get("entity_id")) for item in entities if isinstance(item, dict) and item.get("entity_id")}
    return ids, []


def _load_events(path: Path, scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if not path.exists():
        return events, [{"code": "EVENT_FILE_MISSING", "scope": scope, "path": str(path)}]
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except Exception as exc:
                errors.append({"code": "JSON_PARSE_ERROR", "scope": scope, "line": line_no, "message": str(exc)})
                continue
            if not isinstance(event, dict):
                errors.append({"code": "EVENT_NOT_OBJECT", "scope": scope, "line": line_no})
                continue
            event["_line"] = line_no
            events.append(event)
    return events, errors


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


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


def _decision_kind(event: dict[str, Any]) -> str:
    decision = event.get("decision")
    if not isinstance(decision, dict):
        return "unknown"
    return str(decision.get("kind") or "unknown")


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


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda item: AUTHORITY_ORDER[item])


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    if not isinstance(proof, dict):
        return False
    return (
        proof.get("valid") is True
        and str(proof.get("proof_hash") or "").startswith("sha256:")
        and bool(proof.get("proof_ref"))
    )


def _issue(code: str, scope: str, event: dict[str, Any], detail: str = "") -> dict[str, Any]:
    return {
        "code": code,
        "scope": scope,
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "entity_id": event.get("entity_id"),
        "event_type": event.get("event_type"),
        "decision_kind": _decision_kind(event),
        "detail": detail,
    }


def _rule_profile(rule: str) -> dict[str, Any]:
    return {
        "rule": rule,
        "authority": _authority(rule),
        "event_count": 0,
        "strong_decision_count": 0,
        "suppressed_count": 0,
        "proof_valid_count": 0,
        "entity_count": 0,
        "decision_mix": Counter(),
        "entity_counts": Counter(),
        "risk_flags": Counter(),
        "score_sum": 0.0,
        "score_count": 0,
        "gate_delta_sum": 0.0,
        "gate_delta_count": 0,
    }


def _finalize_rule(profile: dict[str, Any]) -> dict[str, Any]:
    event_count = int(profile["event_count"])
    strong = int(profile["strong_decision_count"])
    suppressed = int(profile["suppressed_count"])
    proof_valid = int(profile["proof_valid_count"])
    score_mean = round(profile["score_sum"] / max(1, profile["score_count"]), 6)
    gate_delta_mean = round(profile["gate_delta_sum"] / max(1, profile["gate_delta_count"]), 6)
    return {
        "rule": profile["rule"],
        "authority": profile["authority"],
        "event_count": event_count,
        "strong_decision_count": strong,
        "suppressed_count": suppressed,
        "proof_valid_count": proof_valid,
        "proof_coverage_ratio": _ratio(proof_valid, event_count),
        "strong_decision_ratio": _ratio(strong, event_count),
        "suppression_ratio": _ratio(suppressed, event_count),
        "entity_count": int(profile["entity_count"]),
        "score_mean": score_mean,
        "gate_delta_mean": gate_delta_mean,
        "decision_mix": profile["decision_mix"].most_common(),
        "top_entities": profile["entity_counts"].most_common(10),
        "risk_flags": profile["risk_flags"].most_common(),
    }


def analyze_scope(scope: str, repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    events_rel = str(spec["events"])
    entities_rel = str(spec["entities"])
    legacy_tolerant = bool(spec.get("legacy_tolerant"))
    events, event_errors = _load_events(repo / events_rel, scope)
    entity_ids, entity_errors = _load_entities(repo / entities_rel, scope)
    errors: list[dict[str, Any]] = [*event_errors, *entity_errors]
    warnings: list[dict[str, Any]] = []
    rule_profiles: dict[str, dict[str, Any]] = defaultdict(dict)
    entity_rule_counts: Counter[tuple[str, str]] = Counter()
    rule_decision_counts: Counter[tuple[str, str]] = Counter()
    authority_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    event_with_rules = 0
    proof_valid_events = 0
    influence_edge_count = 0
    hard_authority_edge_count = 0
    low_authority_edge_count = 0
    low_authority_strong_edge_count = 0
    uncompensated_low_authority_strong_event_count = 0
    native_event_with_hard_authority_count = 0
    entity_valid_count = 0

    for event in events:
        decision = _decision_kind(event)
        decision_counts[decision] += 1
        entity_id = str(event.get("entity_id") or "")
        rules = _rules(event)
        max_authority = _max_authority(rules)
        proof_ok = _proof_ok(event)
        tension = event.get("tension") if isinstance(event.get("tension"), dict) else {}
        score = _safe_float(tension.get("score"))
        gate_delta = _safe_float(tension.get("gate_delta"))
        strong = decision in STRONG_DECISIONS
        suppressed = decision in SUPPRESSED_DECISIONS

        if not entity_id or entity_id not in entity_ids:
            errors.append(_issue("EVENT_ENTITY_NOT_IN_CATALOG", scope, event))
        else:
            entity_valid_count += 1
        if not rules:
            errors.append(_issue("HEURISTIC_RULES_MISSING", scope, event))
            continue
        event_with_rules += 1
        if proof_ok:
            proof_valid_events += 1
        if strong and max_authority not in HARD_AUTHORITIES:
            uncompensated_low_authority_strong_event_count += 1
            item = _issue("LOW_AUTHORITY_STRONG_EVENT", scope, event, f"max_authority={max_authority}")
            if legacy_tolerant:
                warnings.append({**item, "legacy_tolerated": True})
            else:
                errors.append(item)
        if max_authority in HARD_AUTHORITIES:
            native_event_with_hard_authority_count += 1
        for flag in _risk_flags(event):
            risk_counts[flag] += 1
        for rule in rules:
            authority = _authority(rule)
            if not rule_profiles.get(rule):
                rule_profiles[rule] = _rule_profile(rule)
            profile = rule_profiles[rule]
            profile["event_count"] += 1
            profile["decision_mix"][decision] += 1
            profile["entity_counts"][entity_id] += 1
            profile["entity_count"] = len(profile["entity_counts"])
            if strong:
                profile["strong_decision_count"] += 1
            if suppressed:
                profile["suppressed_count"] += 1
            if proof_ok:
                profile["proof_valid_count"] += 1
            if score is not None:
                profile["score_sum"] += score
                profile["score_count"] += 1
            if gate_delta is not None:
                profile["gate_delta_sum"] += gate_delta
                profile["gate_delta_count"] += 1
            for flag in _risk_flags(event):
                profile["risk_flags"][flag] += 1
            influence_edge_count += 1
            authority_counts[authority] += 1
            entity_rule_counts[(entity_id, rule)] += 1
            rule_decision_counts[(rule, decision)] += 1
            if authority in HARD_AUTHORITIES:
                hard_authority_edge_count += 1
            else:
                low_authority_edge_count += 1
                if strong:
                    low_authority_strong_edge_count += 1
                    if legacy_tolerant and max_authority not in HARD_AUTHORITIES:
                        warnings.append({**_issue("LOW_AUTHORITY_STRONG_RULE", scope, event, f"rule={rule}"), "legacy_tolerated": True})

    rule_rows = [_finalize_rule(profile) for profile in rule_profiles.values()]
    rule_rows.sort(key=lambda item: (-int(item["event_count"]), str(item["rule"])))
    scope_clean = not errors and not warnings and int(uncompensated_low_authority_strong_event_count) == 0
    return {
        "scope": scope,
        "events_ref": events_rel,
        "entity_catalog_ref": entities_rel,
        "legacy_tolerant": legacy_tolerant,
        "classification": "HEURISTIC_INFLUENCE_MAP_READY" if not errors else "HEURISTIC_INFLUENCE_MAP_FAIL",
        "pass": not errors,
        "event_count": len(events),
        "entity_valid_count": entity_valid_count,
        "heuristic_rule_count": len(rule_rows),
        "event_with_rules_count": event_with_rules,
        "heuristic_coverage_ratio": _ratio(event_with_rules, len(events)),
        "proof_valid_event_count": proof_valid_events,
        "proof_event_coverage_ratio": _ratio(proof_valid_events, len(events)),
        "influence_edge_count": influence_edge_count,
        "hard_authority_edge_count": hard_authority_edge_count,
        "low_authority_edge_count": low_authority_edge_count,
        "low_authority_strong_edge_count": low_authority_strong_edge_count,
        "uncompensated_low_authority_strong_event_count": uncompensated_low_authority_strong_event_count,
        "hard_authority_edge_ratio": _ratio(hard_authority_edge_count, influence_edge_count),
        "event_with_hard_authority_ratio": _ratio(native_event_with_hard_authority_count, len(events)),
        "scope_influence_clean": scope_clean,
        "decision_mix": decision_counts.most_common(),
        "authority_mix": authority_counts.most_common(),
        "risk_flags": risk_counts.most_common(),
        "rule_profiles": rule_rows,
        "top_entity_rule_edges": [
            {"entity_id": entity, "rule": rule, "count": count}
            for (entity, rule), count in entity_rule_counts.most_common(24)
        ],
        "top_rule_decision_edges": [
            {"rule": rule, "decision_kind": decision, "count": count}
            for (rule, decision), count in rule_decision_counts.most_common(24)
        ],
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    scopes = [analyze_scope(scope, repo, spec) for scope, spec in DEFAULT_SCOPES.items()]
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for scope in scopes:
        errors.extend(scope["errors"])
        warnings.extend(scope["warnings"])

    event_count = sum(int(scope["event_count"]) for scope in scopes)
    rule_names = sorted({row["rule"] for scope in scopes for row in scope["rule_profiles"]})
    influence_edge_count = sum(int(scope["influence_edge_count"]) for scope in scopes)
    hard_edges = sum(int(scope["hard_authority_edge_count"]) for scope in scopes)
    low_edges = sum(int(scope["low_authority_edge_count"]) for scope in scopes)
    low_strong_edges = sum(int(scope["low_authority_strong_edge_count"]) for scope in scopes)
    uncompensated_low_strong = sum(int(scope["uncompensated_low_authority_strong_event_count"]) for scope in scopes)
    event_with_rules = sum(int(scope["event_with_rules_count"]) for scope in scopes)
    proof_valid_events = sum(int(scope["proof_valid_event_count"]) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope["scope"] == "native"), {})
    native_clean = bool(native_scope.get("scope_influence_clean"))
    if errors:
        classification = "HEURISTIC_INFLUENCE_MAP_FAIL"
    elif warnings:
        classification = "HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "HEURISTIC_INFLUENCE_MAP_READY"

    return {
        "schema_version": "pnva.heuristic_influence_map.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "scope_count": len(scopes),
        "event_count": event_count,
        "heuristic_rule_count": len(rule_names),
        "heuristic_rules": rule_names,
        "event_with_rules_count": event_with_rules,
        "heuristic_coverage_ratio": _ratio(event_with_rules, event_count),
        "proof_valid_event_count": proof_valid_events,
        "proof_event_coverage_ratio": _ratio(proof_valid_events, event_count),
        "influence_edge_count": influence_edge_count,
        "hard_authority_edge_count": hard_edges,
        "low_authority_edge_count": low_edges,
        "low_authority_strong_edge_count": low_strong_edges,
        "uncompensated_low_authority_strong_event_count": uncompensated_low_strong,
        "hard_authority_edge_ratio": _ratio(hard_edges, influence_edge_count),
        "native_influence_clean": native_clean,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "scopes": scopes,
        "summary": {
            "total_event_count": event_count,
            "heuristic_rule_count": len(rule_names),
            "heuristic_coverage_ratio": _ratio(event_with_rules, event_count),
            "proof_event_coverage_ratio": _ratio(proof_valid_events, event_count),
            "influence_edge_count": influence_edge_count,
            "hard_authority_edge_count": hard_edges,
            "low_authority_edge_count": low_edges,
            "low_authority_strong_edge_count": low_strong_edges,
            "uncompensated_low_authority_strong_event_count": uncompensated_low_strong,
            "hard_authority_edge_ratio": _ratio(hard_edges, influence_edge_count),
            "native_influence_clean": native_clean,
        },
        "errors": errors,
        "warnings": warnings,
        "interpretation": {
            "purpose": "Map how PNVA heuristic rules influence decisions, entities, suppression and proof-backed execution.",
            "sovereignty": "A no-tick runtime is stronger when each rule's authority, decision mix and entity reach are measurable.",
            "boundary": "Low-authority canonical influence is preserved as migration evidence; native strong events must be covered by hard authority.",
        },
        "recommendations": [
            "Use the highest low-authority strong edge counts as migration targets.",
            "Keep native influence clean: every native strong decision should include H2/H3/H4 coverage.",
            "Use rule profiles to decide which heuristics deserve production authority and which should remain observer-only.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA heuristic influence map.")
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
