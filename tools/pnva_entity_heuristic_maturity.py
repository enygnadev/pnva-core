#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


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


def _load_events(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except Exception as exc:
                errors.append({"line": line_no, "code": "JSON_PARSE_ERROR", "message": str(exc)})
                continue
            if not isinstance(event, dict):
                errors.append({"line": line_no, "code": "EVENT_NOT_OBJECT"})
                continue
            event["_line"] = line_no
            events.append(event)
    return events, errors


def _load_entities(path: Path) -> dict[str, dict[str, Any]]:
    data = _load_json(path)
    entities = data.get("entities", []) if isinstance(data, dict) else []
    return {str(item["entity_id"]): item for item in entities if isinstance(item, dict) and item.get("entity_id")}


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    rules = heuristics.get("rules", [])
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _risk_flags(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    flags = heuristics.get("risk_flags", [])
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda level: AUTHORITY_ORDER[level])


def _decision_kind(event: dict[str, Any]) -> str:
    decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
    return str(decision.get("kind") or "unknown")


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
    return str(source.get("format") or "unknown")


def _is_native(event: dict[str, Any]) -> bool:
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    return _source_format(event) == "native_pnva_event_v1" or proof.get("native") is True


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    return proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:") and bool(proof.get("proof_ref"))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return float(default)
    if numeric != numeric:
        return float(default)
    return float(numeric)


def _mean(values: list[float]) -> float:
    return round(statistics.mean(values), 6) if values else 0.0


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _event_ref(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "entity_id": event.get("entity_id"),
        "event_type": event.get("event_type"),
        "decision_kind": _decision_kind(event),
    }


def _new_profile(entity_id: str, catalog: dict[str, Any] | None) -> dict[str, Any]:
    catalog = catalog or {}
    return {
        "entity_id": entity_id,
        "entity_type": str(catalog.get("entity_type") or "unknown"),
        "catalog_present": bool(catalog),
        "state": catalog.get("state"),
        "capabilities": catalog.get("capabilities", []) if isinstance(catalog.get("capabilities"), list) else [],
        "event_count": 0,
        "strong_decision_count": 0,
        "suppressed_count": 0,
        "proof_valid_count": 0,
        "relation_out_count": 0,
        "relation_in_count": 0,
        "chain_count": 0,
        "max_authority": "H0",
        "decision_mix": Counter(),
        "rules": Counter(),
        "risk_flags": Counter(),
        "chains": set(),
    }


def _score_entity(profile: dict[str, Any]) -> tuple[int, list[str]]:
    score = 100
    notes: list[str] = []
    if not profile["catalog_present"]:
        score -= 35
        notes.append("missing_catalog_entry")
    if not profile["capabilities"]:
        score -= 10
        notes.append("missing_capabilities")
    if profile["event_count"] and profile["proof_valid_count"] != profile["event_count"]:
        score -= 25
        notes.append("proof_coverage_gap")
    if profile["strong_decision_count"] and profile["max_authority"] not in HARD_AUTHORITIES:
        score -= 20
        notes.append("strong_decision_without_hard_authority")
    if profile["event_count"] and profile["chain_count"] == 0:
        score -= 10
        notes.append("missing_causal_chain")
    if profile["event_count"] and not profile["rules"]:
        score -= 10
        notes.append("missing_heuristic_rules")
    return max(0, score), notes


def _score_heuristic(profile: dict[str, Any]) -> tuple[int, list[str]]:
    score = 100
    notes: list[str] = []
    if profile["authority"] in {"H0", "H1"} and profile["strong_decision_count"]:
        score -= 30
        notes.append("low_authority_strong_decisions")
    if profile["proof_valid_count"] != profile["event_count"]:
        score -= 25
        notes.append("proof_coverage_gap")
    if profile["entity_count"] <= 0:
        score -= 10
        notes.append("no_entity_coverage")
    if profile["suppressed_count"] == 0 and profile["decision_mix"].get("collapse", 0) == 0:
        score -= 5
        notes.append("low_decision_signal")
    return max(0, score), notes


def analyze_scope(name: str, events_path: Path, entity_catalog_path: Path, *, legacy_tolerant: bool) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    entities = _load_entities(entity_catalog_path)
    errors: list[dict[str, Any]] = list(parse_errors)
    warnings: list[dict[str, Any]] = []
    entity_profiles: dict[str, dict[str, Any]] = {entity_id: _new_profile(entity_id, entity) for entity_id, entity in entities.items()}
    heuristic_profiles: dict[str, dict[str, Any]] = {}
    incoming_relations: Counter[str] = Counter()
    outgoing_relations: Counter[str] = Counter()
    decision_mix: Counter[str] = Counter()
    authority_mix: Counter[str] = Counter()
    source_mix: Counter[str] = Counter()
    risk_flags: Counter[str] = Counter()
    tension_scores: list[float] = []
    gate_deltas: list[float] = []
    strong_decision_count = 0
    strong_with_hard_authority = 0
    low_authority_legacy_count = 0
    native_event_count = 0
    proof_valid_count = 0
    suppressed_count = 0
    events_with_rules = 0

    def heuristic(rule: str) -> dict[str, Any]:
        if rule not in heuristic_profiles:
            heuristic_profiles[rule] = {
                "rule": rule,
                "authority": _authority(rule),
                "event_count": 0,
                "native_event_count": 0,
                "legacy_event_count": 0,
                "strong_decision_count": 0,
                "suppressed_count": 0,
                "proof_valid_count": 0,
                "entities": set(),
                "decision_mix": Counter(),
                "risk_flags": Counter(),
                "tension_scores": [],
                "gate_deltas": [],
            }
        return heuristic_profiles[rule]

    for event in events:
        entity_id = str(event.get("entity_id") or "entity_unknown")
        if entity_id not in entity_profiles:
            entity_profiles[entity_id] = _new_profile(entity_id, None)
            errors.append({**_event_ref(event), "code": "EVENT_ENTITY_NOT_IN_CATALOG"})
        profile = entity_profiles[entity_id]
        profile["event_count"] += 1
        profile["chains"].add(str(event.get("causal_chain_id") or "chain_unknown"))
        decision_kind = _decision_kind(event)
        decision_mix[decision_kind] += 1
        profile["decision_mix"][decision_kind] += 1
        source_mix[_source_format(event)] += 1
        native = _is_native(event)
        if native:
            native_event_count += 1
        proof_ok = _proof_ok(event)
        if proof_ok:
            proof_valid_count += 1
            profile["proof_valid_count"] += 1
        event_rules = _rules(event)
        if event_rules:
            events_with_rules += 1
        max_authority = _max_authority(event_rules)
        authority_mix[max_authority] += 1
        if AUTHORITY_ORDER[max_authority] > AUTHORITY_ORDER[profile["max_authority"]]:
            profile["max_authority"] = max_authority
        for flag in _risk_flags(event):
            risk_flags[flag] += 1
            profile["risk_flags"][flag] += 1
        tension = event.get("tension", {}) if isinstance(event.get("tension"), dict) else {}
        score = _safe_float(tension.get("score"))
        gate_delta = _safe_float(tension.get("gate_delta"))
        tension_scores.append(score)
        gate_deltas.append(gate_delta)
        if decision_kind in STRONG_DECISIONS:
            strong_decision_count += 1
            profile["strong_decision_count"] += 1
            if max_authority in HARD_AUTHORITIES:
                strong_with_hard_authority += 1
            else:
                item = {
                    **_event_ref(event),
                    "code": "LOW_AUTHORITY_STRONG_DECISION",
                    "rules": event_rules,
                    "max_authority": max_authority,
                    "source_format": _source_format(event),
                }
                if legacy_tolerant and not native:
                    low_authority_legacy_count += 1
                    warnings.append({**item, "legacy_tolerated": True})
                else:
                    errors.append(item)
        if decision_kind in SUPPRESSED_DECISIONS:
            suppressed_count += 1
            profile["suppressed_count"] += 1
        relations = event.get("relations", {}) if isinstance(event.get("relations"), dict) else {}
        target = str(relations.get("target_entity_id") or "")
        if target:
            outgoing_relations[entity_id] += 1
            profile["relation_out_count"] += 1
            incoming_relations[target] += 1

        for rule in event_rules:
            profile["rules"][rule] += 1
            hp = heuristic(rule)
            hp["event_count"] += 1
            hp["entities"].add(entity_id)
            hp["decision_mix"][decision_kind] += 1
            hp["tension_scores"].append(score)
            hp["gate_deltas"].append(gate_delta)
            if native:
                hp["native_event_count"] += 1
            else:
                hp["legacy_event_count"] += 1
            if decision_kind in STRONG_DECISIONS:
                hp["strong_decision_count"] += 1
            if decision_kind in SUPPRESSED_DECISIONS:
                hp["suppressed_count"] += 1
            if proof_ok:
                hp["proof_valid_count"] += 1
            for flag in _risk_flags(event):
                hp["risk_flags"][flag] += 1

    for entity_id, count in incoming_relations.items():
        if entity_id not in entity_profiles:
            errors.append({"code": "RELATION_TARGET_NOT_IN_CATALOG", "entity_id": entity_id, "count": count})
            entity_profiles[entity_id] = _new_profile(entity_id, None)
        entity_profiles[entity_id]["relation_in_count"] = count

    inactive_catalog_entities = [entity_id for entity_id, profile in entity_profiles.items() if profile["catalog_present"] and not profile["event_count"]]
    if inactive_catalog_entities:
        warnings.append({"code": "CATALOG_ENTITIES_WITHOUT_EVENTS", "entities": inactive_catalog_entities})

    entity_items: list[dict[str, Any]] = []
    for profile in entity_profiles.values():
        profile["chain_count"] = len(profile["chains"])
        maturity_score, notes = _score_entity(profile)
        entity_items.append(
            {
                "entity_id": profile["entity_id"],
                "entity_type": profile["entity_type"],
                "catalog_present": profile["catalog_present"],
                "state": profile["state"],
                "capabilities": profile["capabilities"],
                "event_count": profile["event_count"],
                "strong_decision_count": profile["strong_decision_count"],
                "suppressed_count": profile["suppressed_count"],
                "proof_valid_count": profile["proof_valid_count"],
                "chain_count": profile["chain_count"],
                "relation_in_count": profile["relation_in_count"],
                "relation_out_count": profile["relation_out_count"],
                "max_authority": profile["max_authority"],
                "maturity_score": maturity_score,
                "maturity_notes": notes,
                "decision_mix": profile["decision_mix"].most_common(),
                "rules": profile["rules"].most_common(),
                "risk_flags": profile["risk_flags"].most_common(),
            }
        )

    heuristic_items: list[dict[str, Any]] = []
    for profile in heuristic_profiles.values():
        profile["entity_count"] = len(profile["entities"])
        maturity_score, notes = _score_heuristic(profile)
        heuristic_items.append(
            {
                "rule": profile["rule"],
                "authority": profile["authority"],
                "event_count": profile["event_count"],
                "entity_count": profile["entity_count"],
                "native_event_count": profile["native_event_count"],
                "legacy_event_count": profile["legacy_event_count"],
                "strong_decision_count": profile["strong_decision_count"],
                "suppressed_count": profile["suppressed_count"],
                "proof_valid_count": profile["proof_valid_count"],
                "avg_tension_score": _mean(profile["tension_scores"]),
                "avg_gate_delta": _mean(profile["gate_deltas"]),
                "maturity_score": maturity_score,
                "maturity_notes": notes,
                "decision_mix": profile["decision_mix"].most_common(),
                "risk_flags": profile["risk_flags"].most_common(),
            }
        )

    entity_items.sort(key=lambda item: (-int(item["event_count"]), str(item["entity_id"])))
    heuristic_items.sort(key=lambda item: (-int(item["event_count"]), str(item["rule"])))
    observed_entities = sum(1 for item in entity_items if item["event_count"])
    entity_coverage_ratio = _ratio(observed_entities, len(entities))
    proof_integrity_ratio = _ratio(proof_valid_count, len(events))
    heuristic_visibility_ratio = _ratio(events_with_rules, len(events))
    hard_authority_ratio = _ratio(strong_with_hard_authority, strong_decision_count)
    no_tick_suppression_ratio = _ratio(suppressed_count, len(events))
    relation_coverage_ratio = _ratio(sum(1 for item in entity_items if item["relation_in_count"] or item["relation_out_count"]), observed_entities)
    maturity_score = round(
        100
        * (
            0.20 * proof_integrity_ratio
            + 0.18 * entity_coverage_ratio
            + 0.17 * heuristic_visibility_ratio
            + 0.17 * hard_authority_ratio
            + 0.13 * min(1.0, no_tick_suppression_ratio * 2)
            + 0.10 * relation_coverage_ratio
            + 0.05 * (1.0 if not parse_errors else 0.0)
        ),
        2,
    )
    classification = "ENTITY_HEURISTIC_MATURITY_READY"
    if errors:
        classification = "ENTITY_HEURISTIC_MATURITY_FAIL"
    elif low_authority_legacy_count:
        classification = "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS"
    return {
        "scope": name,
        "events_ref": str(events_path),
        "entity_catalog_ref": str(entity_catalog_path),
        "pass": not errors,
        "classification": classification,
        "maturity_score": maturity_score,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "event_count": len(events),
            "catalog_entity_count": len(entities),
            "observed_entity_count": observed_entities,
            "heuristic_count": len(heuristic_items),
            "native_event_count": native_event_count,
            "legacy_event_count": len(events) - native_event_count,
            "strong_decision_count": strong_decision_count,
            "strong_with_hard_authority": strong_with_hard_authority,
            "low_authority_legacy_count": low_authority_legacy_count,
            "suppressed_count": suppressed_count,
            "proof_valid_count": proof_valid_count,
            "proof_integrity_ratio": proof_integrity_ratio,
            "entity_coverage_ratio": entity_coverage_ratio,
            "heuristic_visibility_ratio": heuristic_visibility_ratio,
            "hard_authority_ratio": hard_authority_ratio,
            "no_tick_suppression_ratio": no_tick_suppression_ratio,
            "relation_coverage_ratio": relation_coverage_ratio,
            "avg_tension_score": _mean(tension_scores),
            "avg_gate_delta": _mean(gate_deltas),
            "decision_mix": decision_mix.most_common(),
            "authority_mix": authority_mix.most_common(),
            "source_mix": source_mix.most_common(),
            "risk_flags": risk_flags.most_common(),
        },
        "entity_profiles": entity_items,
        "heuristic_profiles": heuristic_items,
    }


def build_report(
    repo: Path,
    *,
    canonical_events: str = "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    canonical_entities: str = "reports/pnva-entity-catalog-2026-05-05.json",
    native_events: str = "reports/pnva-native-events-demo-2026-05-05.jsonl",
    native_entities: str = "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
) -> dict[str, Any]:
    repo = repo.resolve()
    canonical = analyze_scope("canonical_legacy_bridge", repo / canonical_events, repo / canonical_entities, legacy_tolerant=True)
    native = analyze_scope("native_runtime_demo", repo / native_events, repo / native_entities, legacy_tolerant=False)
    for scope in (canonical, native):
        for key in ("events_ref", "entity_catalog_ref"):
            path = Path(str(scope[key]))
            scope[key] = str(path.relative_to(repo)) if path.is_relative_to(repo) else path.name
    errors = []
    warnings = []
    for scope in (canonical, native):
        errors.extend({"scope": scope["scope"], **item} for item in scope["errors"])
        warnings.extend({"scope": scope["scope"], **item} for item in scope["warnings"])
    classification = "ENTITY_HEURISTIC_MATURITY_READY"
    if errors:
        classification = "ENTITY_HEURISTIC_MATURITY_FAIL"
    elif warnings:
        classification = "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS"
    total_events = canonical["summary"]["event_count"] + native["summary"]["event_count"]
    total_suppressed = canonical["summary"]["suppressed_count"] + native["summary"]["suppressed_count"]
    total_strong = canonical["summary"]["strong_decision_count"] + native["summary"]["strong_decision_count"]
    total_hard = canonical["summary"]["strong_with_hard_authority"] + native["summary"]["strong_with_hard_authority"]
    return {
        "schema_version": "pnva.entity_heuristic_maturity.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "maturity_score": round(statistics.mean([canonical["maturity_score"], native["maturity_score"]]), 2),
        "error_count": len(errors),
        "warning_count": len(warnings),
        "summary": {
            "total_event_count": total_events,
            "total_suppressed_count": total_suppressed,
            "total_strong_decision_count": total_strong,
            "total_strong_with_hard_authority": total_hard,
            "aggregate_no_tick_suppression_ratio": _ratio(total_suppressed, total_events),
            "aggregate_hard_authority_ratio": _ratio(total_hard, total_strong),
            "canonical_maturity_score": canonical["maturity_score"],
            "native_maturity_score": native["maturity_score"],
            "canonical_low_authority_legacy_count": canonical["summary"]["low_authority_legacy_count"],
            "native_low_authority_legacy_count": native["summary"]["low_authority_legacy_count"],
        },
        "scopes": [canonical, native],
        "interpretation": {
            "purpose": "Measure PNVA maturity across entities, heuristic rules, no-tick suppression, proof coverage and authority.",
            "legacy_policy": "Legacy low-authority strong decisions are warnings when preserved from old sanitized logs, not hidden failures.",
            "native_policy": "Native events must carry H2/H3/H4 authority for strong decisions.",
            "sovereignty": "Every important entity and heuristic should be visible, proof-backed, entity-cataloged and connected to causal chains.",
        },
        "recommendations": [
            "Move future strong decisions away from legacy_observer authority.",
            "Keep emitting native pnva.event.v1 events with H2/H3 authority.",
            "Use entity maturity scores to choose the next runtime hardening target.",
            "Track no-tick suppression per entity so non-execution remains a first-class proof.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PNVA entity and heuristic maturity across canonical and native evidence.")
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
