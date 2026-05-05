#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
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
ALLOWED_DECISIONS = {"collapse", "observe", "block", "prove"}


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


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _decision_kind(event: dict[str, Any]) -> str:
    return str(_decision(event).get("kind") or "unknown")


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tension")
    return value if isinstance(value, dict) else {}


def _heuristics(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("heuristics")
    return value if isinstance(value, dict) else {}


def _rules(event: dict[str, Any]) -> list[str]:
    rules = _heuristics(event).get("rules")
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _risk_flags(event: dict[str, Any]) -> list[str]:
    flags = _heuristics(event).get("risk_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


def _proof(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("proof")
    return value if isinstance(value, dict) else {}


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = _proof(event)
    return (
        proof.get("valid") is True
        and str(proof.get("proof_hash") or "").startswith("sha256:")
        and bool(proof.get("proof_ref"))
    )


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda item: AUTHORITY_ORDER[item])


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


def _trace_entry(scope: str, event: dict[str, Any], rules: list[str], max_authority: str) -> dict[str, Any]:
    tension = _tension(event)
    decision = _decision(event)
    proof = _proof(event)
    return {
        "scope": scope,
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "entity_id": event.get("entity_id"),
        "causal_chain_id": event.get("causal_chain_id"),
        "decision_kind": str(decision.get("kind") or ""),
        "decision_action": str(decision.get("action") or ""),
        "score": tension.get("score"),
        "threshold": tension.get("threshold"),
        "gate_delta": tension.get("gate_delta"),
        "rules": rules,
        "max_authority": max_authority,
        "risk_flags": _risk_flags(event),
        "proof_hash": proof.get("proof_hash"),
        "proof_ref": proof.get("proof_ref"),
    }


def analyze_scope(scope: str, repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    events_rel = str(spec["events"])
    entities_rel = str(spec["entities"])
    legacy_tolerant = bool(spec.get("legacy_tolerant"))
    events, event_errors = _load_events(repo / events_rel, scope)
    entity_ids, entity_errors = _load_entities(repo / entities_rel, scope)
    errors: list[dict[str, Any]] = [*event_errors, *entity_errors]
    warnings: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    entity_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    chain_counts: Counter[str] = Counter()
    trace_complete_count = 0
    proof_valid_count = 0
    heuristic_visible_count = 0
    entity_valid_count = 0
    chain_valid_count = 0
    tension_valid_count = 0
    hard_authority_count = 0
    low_authority_trace_count = 0

    for event in events:
        rules = _rules(event)
        max_authority = _max_authority(rules)
        decision_kind = _decision_kind(event)
        entity_id = str(event.get("entity_id") or "")
        chain_id = str(event.get("causal_chain_id") or "")
        tension = _tension(event)
        score = _safe_float(tension.get("score"))
        threshold = _safe_float(tension.get("threshold"))
        gate_delta = _safe_float(tension.get("gate_delta"))
        trace_errors = 0

        decision_counts[decision_kind] += 1
        entity_counts[entity_id] += 1
        chain_counts[chain_id] += 1
        authority_counts[max_authority] += 1
        for rule in rules:
            rule_counts[rule] += 1
        for flag in _risk_flags(event):
            risk_counts[flag] += 1

        if not event.get("event_id"):
            errors.append(_issue("EVENT_ID_MISSING", scope, event))
            trace_errors += 1
        if not entity_id or entity_id not in entity_ids:
            errors.append(_issue("ENTITY_TRACE_MISSING_OR_UNKNOWN", scope, event))
            trace_errors += 1
        else:
            entity_valid_count += 1
        if not chain_id:
            errors.append(_issue("CAUSAL_CHAIN_MISSING", scope, event))
            trace_errors += 1
        else:
            chain_valid_count += 1
        if decision_kind not in ALLOWED_DECISIONS:
            errors.append(_issue("DECISION_KIND_INVALID", scope, event, decision_kind))
            trace_errors += 1
        if score is None or threshold is None or gate_delta is None:
            errors.append(_issue("TENSION_TRACE_INCOMPLETE", scope, event))
            trace_errors += 1
        else:
            tension_valid_count += 1
        if not rules:
            errors.append(_issue("HEURISTIC_RULES_MISSING", scope, event))
            trace_errors += 1
        else:
            heuristic_visible_count += 1
        if not _proof_ok(event):
            errors.append(_issue("PROOF_TRACE_INVALID", scope, event))
            trace_errors += 1
        else:
            proof_valid_count += 1

        if max_authority in HARD_AUTHORITIES:
            hard_authority_count += 1
        else:
            low_authority_trace_count += 1
            item = _issue("LOW_AUTHORITY_TRACE", scope, event, f"max_authority={max_authority}")
            if legacy_tolerant:
                warnings.append({**item, "legacy_tolerated": True})
            else:
                errors.append(item)
                trace_errors += 1

        if trace_errors == 0:
            trace_complete_count += 1
        traces.append(_trace_entry(scope, event, rules, max_authority))

    event_count = len(events)
    return {
        "scope": scope,
        "events_ref": events_rel,
        "entity_catalog_ref": entities_rel,
        "legacy_tolerant": legacy_tolerant,
        "classification": "DECISION_TRACE_INDEX_READY" if not errors else "DECISION_TRACE_INDEX_FAIL",
        "pass": not errors,
        "event_count": event_count,
        "traced_event_count": len(traces),
        "trace_complete_count": trace_complete_count,
        "trace_coverage_ratio": _ratio(trace_complete_count, event_count),
        "entity_valid_count": entity_valid_count,
        "entity_coverage_ratio": _ratio(entity_valid_count, event_count),
        "proof_valid_count": proof_valid_count,
        "proof_coverage_ratio": _ratio(proof_valid_count, event_count),
        "heuristic_visible_count": heuristic_visible_count,
        "heuristic_coverage_ratio": _ratio(heuristic_visible_count, event_count),
        "chain_valid_count": chain_valid_count,
        "causal_chain_coverage_ratio": _ratio(chain_valid_count, event_count),
        "tension_valid_count": tension_valid_count,
        "tension_coverage_ratio": _ratio(tension_valid_count, event_count),
        "hard_authority_event_count": hard_authority_count,
        "low_authority_trace_count": low_authority_trace_count,
        "hard_authority_ratio": _ratio(hard_authority_count, event_count),
        "native_trace_clean": not errors and (not warnings or legacy_tolerant),
        "decision_mix": decision_counts.most_common(),
        "top_entities": entity_counts.most_common(12),
        "rule_counts": rule_counts.most_common(),
        "authority_mix": authority_counts.most_common(),
        "risk_flags": risk_counts.most_common(),
        "chain_count": len([key for key in chain_counts if key]),
        "trace_index": traces,
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
    traced_event_count = sum(int(scope["traced_event_count"]) for scope in scopes)
    trace_complete_count = sum(int(scope["trace_complete_count"]) for scope in scopes)
    entity_valid_count = sum(int(scope["entity_valid_count"]) for scope in scopes)
    proof_valid_count = sum(int(scope["proof_valid_count"]) for scope in scopes)
    heuristic_visible_count = sum(int(scope["heuristic_visible_count"]) for scope in scopes)
    chain_valid_count = sum(int(scope["chain_valid_count"]) for scope in scopes)
    tension_valid_count = sum(int(scope["tension_valid_count"]) for scope in scopes)
    hard_authority = sum(int(scope["hard_authority_event_count"]) for scope in scopes)
    low_authority = sum(int(scope["low_authority_trace_count"]) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope["scope"] == "native"), {})
    native_clean = bool(native_scope.get("native_trace_clean"))

    if errors:
        classification = "DECISION_TRACE_INDEX_FAIL"
    elif warnings:
        classification = "DECISION_TRACE_INDEX_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "DECISION_TRACE_INDEX_READY"

    return {
        "schema_version": "pnva.decision_trace_index.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "scope_count": len(scopes),
        "event_count": event_count,
        "traced_event_count": traced_event_count,
        "trace_complete_count": trace_complete_count,
        "trace_coverage_ratio": _ratio(trace_complete_count, event_count),
        "entity_coverage_ratio": _ratio(entity_valid_count, event_count),
        "proof_coverage_ratio": _ratio(proof_valid_count, event_count),
        "heuristic_coverage_ratio": _ratio(heuristic_visible_count, event_count),
        "causal_chain_coverage_ratio": _ratio(chain_valid_count, event_count),
        "tension_coverage_ratio": _ratio(tension_valid_count, event_count),
        "hard_authority_event_count": hard_authority,
        "low_authority_trace_count": low_authority,
        "hard_authority_ratio": _ratio(hard_authority, event_count),
        "native_trace_clean": native_clean,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "scopes": scopes,
        "summary": {
            "total_event_count": event_count,
            "total_traced_event_count": traced_event_count,
            "trace_complete_count": trace_complete_count,
            "trace_coverage_ratio": _ratio(trace_complete_count, event_count),
            "entity_coverage_ratio": _ratio(entity_valid_count, event_count),
            "proof_coverage_ratio": _ratio(proof_valid_count, event_count),
            "heuristic_coverage_ratio": _ratio(heuristic_visible_count, event_count),
            "causal_chain_coverage_ratio": _ratio(chain_valid_count, event_count),
            "tension_coverage_ratio": _ratio(tension_valid_count, event_count),
            "hard_authority_event_count": hard_authority,
            "low_authority_trace_count": low_authority,
            "native_trace_clean": native_clean,
        },
        "errors": errors,
        "warnings": warnings,
        "interpretation": {
            "purpose": "Index every PNVA decision as event, entity, heuristic, tension and proof.",
            "sovereignty": "A decision is publishable only when its actor, rules, causal chain, threshold signal and proof hash are visible.",
            "boundary": "Canonical low-authority traces are preserved as legacy warnings; native runtime traces must stay complete and clean.",
        },
        "recommendations": [
            "Use this index as the reviewer-facing map from event IDs to entities, rules, tension and proof.",
            "Prefer native H2/H3 authority for all new runtime traces.",
            "Keep trace coverage at 1.0 before publishing any future evidence package.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA decision trace index.")
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
