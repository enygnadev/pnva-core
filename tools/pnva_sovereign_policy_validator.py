#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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

STRONG_DECISIONS = {"collapse", "block", "prove", "reclassify"}
HARD_AUTHORITIES = {"H2", "H3", "H4"}
REQUIRED_EVENT_KEYS = {
    "schema_version",
    "event_id",
    "timestamp",
    "causal_chain_id",
    "entity_id",
    "event_type",
    "field",
    "tension",
    "decision",
    "proof",
}


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


def _load_entity_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    data = _load_json(path)
    entities = data.get("entities", []) if isinstance(data, dict) else []
    return {str(item.get("entity_id")) for item in entities if isinstance(item, dict) and item.get("entity_id")}


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics", {}) if isinstance(event.get("heuristics"), dict) else {}
    rules = heuristics.get("rules", [])
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    order = {"H0": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4}
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda level: order[level])


def _decision_kind(event: dict[str, Any]) -> str:
    decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
    return str(decision.get("kind") or "unknown")


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
    return str(source.get("format") or "")


def _is_native(event: dict[str, Any]) -> bool:
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    return _source_format(event) == "native_pnva_event_v1" or proof.get("native") is True


def _has_valid_proof(event: dict[str, Any]) -> bool:
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    proof_hash = str(proof.get("proof_hash") or "")
    proof_ref = str(proof.get("proof_ref") or "")
    return proof.get("valid") is True and proof_hash.startswith("sha256:") and bool(proof_ref)


def _event_ref(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "entity_id": event.get("entity_id"),
        "decision_kind": _decision_kind(event),
    }


def validate_policy(events: list[dict[str, Any]], entity_ids: set[str], *, legacy_tolerant: bool) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    rules_counter: Counter[str] = Counter()
    authority_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    native_count = 0
    strong_decision_count = 0
    low_authority_legacy_count = 0
    entity_missing_count = 0
    guard_policy_ok = 0
    guard_policy_bad = 0
    proof_policy_ok = 0
    proof_policy_bad = 0
    entity_policy_ok = 0
    relation_policy_ok = 0
    relation_policy_bad = 0
    by_authority_decision: dict[str, Counter[str]] = defaultdict(Counter)

    for event in events:
        line = int(event.get("_line", 0))
        missing = sorted(REQUIRED_EVENT_KEYS.difference(event))
        if missing:
            errors.append({**_event_ref(event), "code": "MISSING_REQUIRED_KEYS", "missing": missing})
            continue
        event_rules = _rules(event)
        for rule in event_rules:
            rules_counter[rule] += 1
        authority = _max_authority(event_rules)
        authority_counter[authority] += 1
        decision_kind = _decision_kind(event)
        decision_counter[decision_kind] += 1
        by_authority_decision[authority][decision_kind] += 1
        source_counter[_source_format(event) or "unknown"] += 1
        native = _is_native(event)
        if native:
            native_count += 1

        if str(event.get("entity_id") or "") in entity_ids:
            entity_policy_ok += 1
        else:
            entity_missing_count += 1
            errors.append({**_event_ref(event), "code": "ENTITY_NOT_IN_CATALOG"})

        source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
        file_name = str(source.get("file_name") or "")
        if "/" in file_name:
            errors.append({**_event_ref(event), "code": "RAW_SOURCE_PATH_PUBLISHED", "source_file_name": file_name})

        relations = event.get("relations", {}) if isinstance(event.get("relations"), dict) else {}
        target = str(relations.get("target_entity_id") or "")
        if target:
            if target in entity_ids:
                relation_policy_ok += 1
            else:
                relation_policy_bad += 1
                warnings.append({**_event_ref(event), "code": "RELATION_TARGET_NOT_IN_ENTITY_CATALOG", "target_entity_id": target})

        proof_ok = _has_valid_proof(event)
        if decision_kind in STRONG_DECISIONS:
            strong_decision_count += 1
            if proof_ok:
                proof_policy_ok += 1
            else:
                proof_policy_bad += 1
                errors.append({**_event_ref(event), "code": "STRONG_DECISION_WITHOUT_VALID_PROOF"})

            has_hard_authority = authority in HARD_AUTHORITIES
            if not has_hard_authority:
                item = {
                    **_event_ref(event),
                    "code": "LOW_AUTHORITY_STRONG_DECISION",
                    "rules": event_rules,
                    "max_authority": authority,
                    "source_format": _source_format(event),
                }
                if legacy_tolerant and not native:
                    low_authority_legacy_count += 1
                    warnings.append({**item, "legacy_tolerated": True})
                else:
                    errors.append(item)

        event_type = str(event.get("event_type") or "").upper()
        if event_type.startswith("ETEV_GUARD"):
            if "etev_guard" in event_rules and authority in HARD_AUTHORITIES:
                guard_policy_ok += 1
            else:
                guard_policy_bad += 1
                errors.append({**_event_ref(event), "code": "GUARD_EVENT_WITHOUT_GUARD_AUTHORITY", "rules": event_rules})

    return {
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "event_count": len(events),
            "native_event_count": native_count,
            "strong_decision_count": strong_decision_count,
            "low_authority_legacy_count": low_authority_legacy_count,
            "entity_policy_ok": entity_policy_ok,
            "entity_missing_count": entity_missing_count,
            "guard_policy_ok": guard_policy_ok,
            "guard_policy_bad": guard_policy_bad,
            "proof_policy_ok": proof_policy_ok,
            "proof_policy_bad": proof_policy_bad,
            "relation_policy_ok": relation_policy_ok,
            "relation_policy_bad": relation_policy_bad,
            "decision_mix": decision_counter.most_common(),
            "authority_mix": authority_counter.most_common(),
            "rules": rules_counter.most_common(),
            "source_formats": source_counter.most_common(),
            "decisions_by_authority": {level: counter.most_common() for level, counter in sorted(by_authority_decision.items())},
        },
    }


def build_report(events_path: Path, entity_catalog_path: Path, *, legacy_tolerant: bool = True) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    entity_ids = _load_entity_ids(entity_catalog_path)
    validation = validate_policy(events, entity_ids, legacy_tolerant=legacy_tolerant)
    errors = list(parse_errors) + validation["errors"]
    summary = validation["summary"]
    classification = "SOVEREIGN_POLICY_READY"
    if errors:
        classification = "SOVEREIGN_POLICY_FAIL"
    elif summary["low_authority_legacy_count"]:
        classification = "SOVEREIGN_POLICY_READY_WITH_LEGACY_WARNINGS"
    return {
        "schema_version": "pnva.sovereign_policy.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "events_ref": str(events_path),
        "entity_catalog_ref": str(entity_catalog_path),
        "legacy_tolerant": bool(legacy_tolerant),
        "pass": not errors,
        "classification": classification,
        "errors": errors,
        "warnings": validation["warnings"],
        "summary": summary,
        "policy": {
            "H0": "Observation only; strong decisions are warnings only for legacy evidence when legacy_tolerant is true.",
            "H1": "Advisory signal or memory; not enough alone for new strong actions.",
            "H2": "Guarded threshold, routing, native emission or runtime action.",
            "H3": "Sovereign guard authority.",
            "strong_decisions": sorted(STRONG_DECISIONS),
        },
        "interpretation": {
            "native_rule": "Native events must carry H2/H3 authority for collapse, block, prove or reclassify decisions.",
            "legacy_rule": "Legacy weak-authority strong decisions are preserved as warnings so historical evidence is not rewritten.",
            "sovereignty": "Authority, entity, proof and relation policies are checked before an event is treated as production-grade evidence.",
        },
        "recommendations": [
            "Move new runtime strong decisions to native pnva.event.v1 emission with H2/H3 authority.",
            "Keep legacy low-authority strong decisions visible as warnings until the source runtime is upgraded.",
            "Require etev_guard on every ETEV_GUARD_PASS and ETEV_GUARD_BLOCK event.",
            "Require valid proof_hash and proof_ref for every collapse, block, prove or reclassify decision.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA sovereign heuristic authority, entity and proof policies.")
    parser.add_argument("--events", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-entity-catalog-2026-05-05.json")
    parser.add_argument("--write", default="")
    parser.add_argument("--strict-authority", action="store_true", help="Treat legacy low-authority strong decisions as errors.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_catalog_path = Path(args.entity_catalog)
    if not entity_catalog_path.is_absolute():
        entity_catalog_path = repo / entity_catalog_path
    report = build_report(events_path, entity_catalog_path, legacy_tolerant=not bool(args.strict_authority))
    for key in ("events_ref", "entity_catalog_ref"):
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
