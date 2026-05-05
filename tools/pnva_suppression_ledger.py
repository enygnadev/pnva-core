#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
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
        return set(), [{"code": "ENTITY_CATALOG_ENTITIES_INVALID", "scope": scope, "path": str(path)}]
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


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _decision_kind(event: dict[str, Any]) -> str:
    return str(_decision(event).get("kind") or "unknown")


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


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        return ""
    return str(source.get("format") or "")


def _is_native(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    proof_native = isinstance(proof, dict) and proof.get("native") is True
    return _source_format(event) == "native_pnva_event_v1" or proof_native


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


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _mean(values: list[float]) -> float:
    return round(statistics.mean(values), 6) if values else 0.0


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


def _ledger_entry(scope: str, event: dict[str, Any], gate_delta: float | None, rules: list[str]) -> dict[str, Any]:
    decision = _decision(event)
    proof = _proof(event)
    tension = event.get("tension") if isinstance(event.get("tension"), dict) else {}
    return {
        "scope": scope,
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "entity_id": event.get("entity_id"),
        "event_type": event.get("event_type"),
        "causal_chain_id": event.get("causal_chain_id"),
        "decision_kind": str(decision.get("kind") or ""),
        "decision_action": str(decision.get("action") or ""),
        "decision_reason": str(decision.get("reason") or ""),
        "score": tension.get("score"),
        "threshold": tension.get("threshold"),
        "gate_delta": gate_delta,
        "suppression_signal": "below_threshold" if gate_delta is not None and gate_delta < 0 else "above_threshold_legacy_or_boundary",
        "rules": rules,
        "max_authority": _max_authority(rules),
        "risk_flags": _risk_flags(event),
        "proof_ref": proof.get("proof_ref"),
        "proof_hash": proof.get("proof_hash"),
    }


def analyze_scope(scope: str, repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    events_rel = str(spec["events"])
    entities_rel = str(spec["entities"])
    legacy_tolerant = bool(spec.get("legacy_tolerant"))
    events, event_errors = _load_events(repo / events_rel, scope)
    entity_ids, entity_errors = _load_entities(repo / entities_rel, scope)
    errors: list[dict[str, Any]] = [*event_errors, *entity_errors]
    warnings: list[dict[str, Any]] = []
    ledger: list[dict[str, Any]] = []
    decision_counts: Counter[str] = Counter()
    entity_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    gate_deltas: list[float] = []
    below_threshold_count = 0
    above_threshold_count = 0
    proof_valid_count = 0
    native_suppression_count = 0
    low_authority_suppression_count = 0
    low_authority_block_count = 0

    for event in events:
        kind = _decision_kind(event)
        if kind not in SUPPRESSED_DECISIONS:
            continue
        rules = _rules(event)
        max_authority = _max_authority(rules)
        native = _is_native(event)
        entity_id = str(event.get("entity_id") or "")
        tension = event.get("tension") if isinstance(event.get("tension"), dict) else {}
        gate_delta = _safe_float(tension.get("gate_delta"))
        ledger.append(_ledger_entry(scope, event, gate_delta, rules))
        decision_counts[kind] += 1
        entity_counts[entity_id] += 1
        authority_counts[max_authority] += 1
        if native:
            native_suppression_count += 1
        for rule in rules:
            rule_counts[rule] += 1
        for flag in _risk_flags(event):
            risk_counts[flag] += 1
        if _proof_ok(event):
            proof_valid_count += 1
        else:
            errors.append(_issue("SUPPRESSION_PROOF_MISSING_OR_INVALID", scope, event))
        if not entity_id or entity_id not in entity_ids:
            errors.append(_issue("SUPPRESSION_ENTITY_NOT_IN_CATALOG", scope, event))
        if not rules:
            errors.append(_issue("SUPPRESSION_HEURISTICS_MISSING", scope, event))
        if gate_delta is None:
            errors.append(_issue("SUPPRESSION_GATE_DELTA_MISSING", scope, event))
            continue
        gate_deltas.append(gate_delta)
        if gate_delta < 0:
            below_threshold_count += 1
        else:
            above_threshold_count += 1
            item = _issue("SUPPRESSION_ABOVE_THRESHOLD", scope, event, f"gate_delta={gate_delta}")
            if legacy_tolerant and not native:
                warnings.append({**item, "legacy_tolerated": True})
            else:
                errors.append(item)
        if max_authority not in HARD_AUTHORITIES:
            low_authority_suppression_count += 1
            if kind == "block":
                low_authority_block_count += 1
                item = _issue("LOW_AUTHORITY_BLOCK_SUPPRESSION", scope, event, f"max_authority={max_authority}")
                if legacy_tolerant and not native:
                    warnings.append({**item, "legacy_tolerated": True})
                else:
                    errors.append(item)

    suppressed_count = len(ledger)
    native_clean = not any(item for item in errors if item.get("scope") == scope) and not any(
        item for item in warnings if item.get("scope") == scope and not legacy_tolerant
    )
    return {
        "scope": scope,
        "events_ref": events_rel,
        "entity_catalog_ref": entities_rel,
        "legacy_tolerant": legacy_tolerant,
        "classification": "SUPPRESSION_LEDGER_READY" if not errors else "SUPPRESSION_LEDGER_FAIL",
        "pass": not errors,
        "event_count": len(events),
        "suppressed_count": suppressed_count,
        "observe_count": decision_counts.get("observe", 0),
        "block_count": decision_counts.get("block", 0),
        "native_suppression_count": native_suppression_count,
        "proof_valid_count": proof_valid_count,
        "proof_coverage_ratio": _ratio(proof_valid_count, suppressed_count),
        "below_threshold_suppression_count": below_threshold_count,
        "above_threshold_suppression_count": above_threshold_count,
        "low_authority_suppression_count": low_authority_suppression_count,
        "low_authority_block_count": low_authority_block_count,
        "no_tick_suppression_ratio": _ratio(suppressed_count, len(events)),
        "native_suppression_clean": native_clean,
        "gate_delta_stats": {
            "count": len(gate_deltas),
            "min": round(min(gate_deltas), 6) if gate_deltas else 0.0,
            "max": round(max(gate_deltas), 6) if gate_deltas else 0.0,
            "mean": _mean(gate_deltas),
            "median": round(statistics.median(gate_deltas), 6) if gate_deltas else 0.0,
        },
        "top_entities": entity_counts.most_common(12),
        "decision_mix": decision_counts.most_common(),
        "rule_counts": rule_counts.most_common(),
        "authority_mix": authority_counts.most_common(),
        "risk_flags": risk_counts.most_common(),
        "ledger": ledger,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    scopes = [analyze_scope(scope, repo, spec) for scope, spec in DEFAULT_SCOPES.items()]
    errors = []
    warnings = []
    for scope in scopes:
        errors.extend(scope["errors"])
        warnings.extend(scope["warnings"])
    total_events = sum(int(scope["event_count"]) for scope in scopes)
    suppressed_count = sum(int(scope["suppressed_count"]) for scope in scopes)
    proof_valid_count = sum(int(scope["proof_valid_count"]) for scope in scopes)
    above_threshold = sum(int(scope["above_threshold_suppression_count"]) for scope in scopes)
    below_threshold = sum(int(scope["below_threshold_suppression_count"]) for scope in scopes)
    low_authority = sum(int(scope["low_authority_suppression_count"]) for scope in scopes)
    low_authority_blocks = sum(int(scope["low_authority_block_count"]) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope["scope"] == "native"), {})
    native_clean = bool(native_scope.get("native_suppression_clean"))
    if errors:
        classification = "SUPPRESSION_LEDGER_FAIL"
    elif warnings:
        classification = "SUPPRESSION_LEDGER_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "SUPPRESSION_LEDGER_READY"
    return {
        "schema_version": "pnva.suppression_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "scope_count": len(scopes),
        "event_count": total_events,
        "suppressed_count": suppressed_count,
        "estimated_avoided_execution_count": suppressed_count,
        "proof_valid_count": proof_valid_count,
        "proof_coverage_ratio": _ratio(proof_valid_count, suppressed_count),
        "below_threshold_suppression_count": below_threshold,
        "above_threshold_suppression_count": above_threshold,
        "low_authority_suppression_count": low_authority,
        "low_authority_block_count": low_authority_blocks,
        "aggregate_no_tick_suppression_ratio": _ratio(suppressed_count, total_events),
        "native_suppression_clean": native_clean,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "scopes": scopes,
        "summary": {
            "total_event_count": total_events,
            "total_suppressed_count": suppressed_count,
            "estimated_avoided_execution_count": suppressed_count,
            "proof_coverage_ratio": _ratio(proof_valid_count, suppressed_count),
            "aggregate_no_tick_suppression_ratio": _ratio(suppressed_count, total_events),
            "above_threshold_suppression_count": above_threshold,
            "below_threshold_suppression_count": below_threshold,
            "low_authority_suppression_count": low_authority,
            "low_authority_block_count": low_authority_blocks,
            "native_suppression_clean": native_clean,
        },
        "errors": errors,
        "warnings": warnings,
        "interpretation": {
            "purpose": "Treat PNVA non-execution as an auditable suppression ledger, not as missing work.",
            "sovereignty": "Every no-tick suppression should name the entity, heuristic authority, tension signal and proof hash that justified not executing.",
            "boundary": "Legacy bridge threshold drift remains explicit warnings; native suppression must stay below threshold and proof-backed.",
        },
        "recommendations": [
            "Use this ledger to explain saved executions as proof-backed no-tick suppressions.",
            "Replace legacy above-threshold suppressions with native calibrated events over time.",
            "Keep native suppression clean: proof present, entity catalog present, heuristic visible and gate_delta below threshold.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA proof-backed suppression ledger.")
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
