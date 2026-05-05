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
STRONG_DECISIONS = {"collapse", "block", "prove", "reclassify"}
SUPPRESSED_DECISIONS = {"observe", "block"}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path, scope: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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


def _load_entities(path: Path, scope: str) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    if not path.exists():
        return {}, [{"code": "ENTITY_CATALOG_MISSING", "scope": scope, "path": str(path)}]
    data = _load_json(path)
    if not isinstance(data, dict):
        return {}, [{"code": "ENTITY_CATALOG_INVALID", "scope": scope, "path": str(path)}]
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return {}, [{"code": "ENTITY_CATALOG_ENTITIES_INVALID", "scope": scope, "path": str(path)}]
    result: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    for index, item in enumerate(entities):
        if not isinstance(item, dict) or not item.get("entity_id"):
            errors.append({"code": "ENTITY_ENTRY_INVALID", "scope": scope, "index": index})
            continue
        result[str(item["entity_id"])] = item
    return result, errors


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _decision_kind(event: dict[str, Any]) -> str:
    return str(_decision(event).get("kind") or "unknown")


def _decision_action(event: dict[str, Any]) -> str:
    return str(_decision(event).get("action") or "")


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


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    if not isinstance(proof, dict):
        return False
    return (
        proof.get("valid") is True
        and str(proof.get("proof_hash") or "").startswith("sha256:")
        and bool(proof.get("proof_ref"))
    )


def _source_format(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        return ""
    return str(source.get("format") or "")


def _is_native_event(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    native_proof = isinstance(proof, dict) and proof.get("native") is True
    return _source_format(event) == "native_pnva_event_v1" or native_proof


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda item: AUTHORITY_ORDER[item])


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


def _mean(values: list[float]) -> float:
    return round(statistics.mean(values), 6) if values else 0.0


def _new_entity_row(scope: str, entity_id: str, catalog: dict[str, Any] | None) -> dict[str, Any]:
    catalog = catalog or {}
    return {
        "scope": scope,
        "entity_id": entity_id,
        "entity_type": str(catalog.get("entity_type") or "unknown"),
        "catalog_present": bool(catalog),
        "catalog_state": catalog.get("state"),
        "capabilities": catalog.get("capabilities", []) if isinstance(catalog.get("capabilities"), list) else [],
        "event_count": 0,
        "native_event_count": 0,
        "legacy_event_count": 0,
        "proof_valid_count": 0,
        "strong_decision_count": 0,
        "suppressed_count": 0,
        "collapse_count": 0,
        "observe_count": 0,
        "block_count": 0,
        "prove_count": 0,
        "relation_out_count": 0,
        "relation_in_count": 0,
        "chains": set(),
        "decision_mix": Counter(),
        "action_mix": Counter(),
        "rules": Counter(),
        "risk_flags": Counter(),
        "authority_mix": Counter(),
        "tension_scores": [],
        "gate_deltas": [],
        "max_authority": "H0",
    }


def _status(row: dict[str, Any]) -> str:
    if not row["event_count"]:
        return "catalog_idle"
    if not row["catalog_present"]:
        return "catalog_missing"
    if row["proof_valid_count"] != row["event_count"]:
        return "proof_gap"
    if row["strong_decision_count"] and row["max_authority"] not in HARD_AUTHORITIES:
        return "legacy_authority_attention"
    if row["suppressed_count"] and row["collapse_count"]:
        return "no_tick_balanced"
    if row["suppressed_count"]:
        return "no_tick_suppressor"
    if row["collapse_count"] or row["prove_count"]:
        return "causal_executor"
    return "observed"


def _final_entity(row: dict[str, Any]) -> dict[str, Any]:
    event_count = int(row["event_count"])
    proof_ratio = _ratio(int(row["proof_valid_count"]), event_count)
    suppression_ratio = _ratio(int(row["suppressed_count"]), event_count)
    strong_ratio = _ratio(int(row["strong_decision_count"]), event_count)
    chain_count = len(row["chains"])
    return {
        "scope": row["scope"],
        "entity_id": row["entity_id"],
        "entity_type": row["entity_type"],
        "catalog_present": row["catalog_present"],
        "catalog_state": row["catalog_state"],
        "capabilities": row["capabilities"],
        "status": _status(row),
        "event_count": event_count,
        "native_event_count": int(row["native_event_count"]),
        "legacy_event_count": int(row["legacy_event_count"]),
        "proof_valid_count": int(row["proof_valid_count"]),
        "proof_coverage_ratio": proof_ratio,
        "strong_decision_count": int(row["strong_decision_count"]),
        "strong_decision_ratio": strong_ratio,
        "suppressed_count": int(row["suppressed_count"]),
        "suppression_ratio": suppression_ratio,
        "collapse_count": int(row["collapse_count"]),
        "observe_count": int(row["observe_count"]),
        "block_count": int(row["block_count"]),
        "prove_count": int(row["prove_count"]),
        "chain_count": chain_count,
        "relation_out_count": int(row["relation_out_count"]),
        "relation_in_count": int(row["relation_in_count"]),
        "max_authority": row["max_authority"],
        "decision_mix": row["decision_mix"].most_common(),
        "top_actions": row["action_mix"].most_common(8),
        "rules": row["rules"].most_common(),
        "authority_mix": row["authority_mix"].most_common(),
        "risk_flags": row["risk_flags"].most_common(),
        "avg_tension_score": _mean(row["tension_scores"]),
        "avg_gate_delta": _mean(row["gate_deltas"]),
    }


def _issue(code: str, scope: str, event: dict[str, Any], detail: str = "") -> dict[str, Any]:
    return {
        "code": code,
        "scope": scope,
        "line": int(event.get("_line", 0)),
        "event_id": event.get("event_id"),
        "entity_id": event.get("entity_id"),
        "decision_kind": _decision_kind(event),
        "detail": detail,
    }


def analyze_scope(scope: str, repo: Path, spec: dict[str, Any]) -> dict[str, Any]:
    legacy_tolerant = bool(spec.get("legacy_tolerant"))
    events_rel = str(spec["events"])
    entities_rel = str(spec["entities"])
    events, event_errors = _load_jsonl(repo / events_rel, scope)
    entities, entity_errors = _load_entities(repo / entities_rel, scope)
    errors: list[dict[str, Any]] = [*event_errors, *entity_errors]
    warnings: list[dict[str, Any]] = []
    rows: dict[str, dict[str, Any]] = {
        entity_id: _new_entity_row(scope, entity_id, entity) for entity_id, entity in entities.items()
    }
    incoming: Counter[str] = Counter()
    heuristic_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    authority_counts: Counter[str] = Counter()
    native_events = 0
    proof_valid_count = 0
    events_with_rules = 0
    strong_decision_count = 0
    strong_with_hard_authority = 0
    suppressed_count = 0
    legacy_low_authority_warning_count = 0

    for event in events:
        entity_id = str(event.get("entity_id") or "entity_unknown")
        if entity_id not in rows:
            rows[entity_id] = _new_entity_row(scope, entity_id, None)
            errors.append(_issue("EVENT_ENTITY_NOT_IN_CATALOG", scope, event))
        row = rows[entity_id]
        row["event_count"] += 1
        native = _is_native_event(event)
        if native:
            native_events += 1
            row["native_event_count"] += 1
        else:
            row["legacy_event_count"] += 1
        proof_ok = _proof_ok(event)
        if proof_ok:
            proof_valid_count += 1
            row["proof_valid_count"] += 1
        else:
            target = errors if native or not legacy_tolerant else warnings
            target.append(_issue("PROOF_COVERAGE_GAP", scope, event))
        kind = _decision_kind(event)
        action = _decision_action(event)
        rules = _rules(event)
        if rules:
            events_with_rules += 1
        max_authority = _max_authority(rules)
        if AUTHORITY_ORDER[max_authority] > AUTHORITY_ORDER[row["max_authority"]]:
            row["max_authority"] = max_authority
        decision_counts[kind] += 1
        authority_counts[max_authority] += 1
        row["decision_mix"][kind] += 1
        row["action_mix"][action] += 1
        row["authority_mix"][max_authority] += 1
        row["chains"].add(str(event.get("causal_chain_id") or "chain_unknown"))
        if kind == "collapse":
            row["collapse_count"] += 1
        elif kind == "observe":
            row["observe_count"] += 1
        elif kind == "block":
            row["block_count"] += 1
        elif kind == "prove":
            row["prove_count"] += 1
        if kind in STRONG_DECISIONS:
            strong_decision_count += 1
            row["strong_decision_count"] += 1
            if max_authority in HARD_AUTHORITIES:
                strong_with_hard_authority += 1
            else:
                item = _issue("LOW_AUTHORITY_STRONG_DECISION", scope, event, f"max_authority={max_authority}")
                if legacy_tolerant and not native:
                    legacy_low_authority_warning_count += 1
                    warnings.append({**item, "legacy_tolerated": True})
                else:
                    errors.append(item)
        if kind in SUPPRESSED_DECISIONS:
            suppressed_count += 1
            row["suppressed_count"] += 1
        for rule in rules:
            heuristic_counts[rule] += 1
            row["rules"][rule] += 1
        for flag in _risk_flags(event):
            risk_counts[flag] += 1
            row["risk_flags"][flag] += 1
        tension = event.get("tension")
        if isinstance(tension, dict):
            score = _safe_float(tension.get("score"))
            gate_delta = _safe_float(tension.get("gate_delta"))
            if score is not None:
                row["tension_scores"].append(score)
            if gate_delta is not None:
                row["gate_deltas"].append(gate_delta)
        relations = event.get("relations")
        if isinstance(relations, dict):
            target = str(relations.get("target_entity_id") or "")
            if target:
                row["relation_out_count"] += 1
                incoming[target] += 1

    for entity_id, count in incoming.items():
        if entity_id not in rows:
            errors.append({"code": "RELATION_TARGET_NOT_IN_CATALOG", "scope": scope, "entity_id": entity_id, "count": count})
            rows[entity_id] = _new_entity_row(scope, entity_id, None)
        rows[entity_id]["relation_in_count"] = count

    matrix = [_final_entity(row) for row in rows.values()]
    matrix.sort(key=lambda item: (-int(item["event_count"]), str(item["entity_id"])))
    observed_entities = [item for item in matrix if int(item["event_count"]) > 0]
    entity_rows_with_suppression = sum(1 for item in observed_entities if int(item["suppressed_count"]) > 0)
    native_matrix_clean = not any(item for item in errors if item.get("scope") == scope)
    return {
        "scope": scope,
        "events_ref": events_rel,
        "entity_catalog_ref": entities_rel,
        "legacy_tolerant": legacy_tolerant,
        "classification": "ENTITY_NO_TICK_MATRIX_READY" if not errors else "ENTITY_NO_TICK_MATRIX_FAIL",
        "pass": not errors,
        "event_count": len(events),
        "catalog_entity_count": len(entities),
        "matrix_entity_count": len(matrix),
        "observed_entity_count": len(observed_entities),
        "entity_suppression_row_count": entity_rows_with_suppression,
        "native_event_count": native_events,
        "legacy_event_count": len(events) - native_events,
        "suppressed_count": suppressed_count,
        "strong_decision_count": strong_decision_count,
        "strong_with_hard_authority": strong_with_hard_authority,
        "legacy_low_authority_warning_count": legacy_low_authority_warning_count,
        "proof_valid_count": proof_valid_count,
        "proof_coverage_ratio": _ratio(proof_valid_count, len(events)),
        "heuristic_visibility_ratio": _ratio(events_with_rules, len(events)),
        "no_tick_suppression_ratio": _ratio(suppressed_count, len(events)),
        "entity_suppression_coverage_ratio": _ratio(entity_rows_with_suppression, len(observed_entities)),
        "native_matrix_clean": native_matrix_clean,
        "decision_mix": decision_counts.most_common(),
        "authority_mix": authority_counts.most_common(),
        "heuristic_rule_counts": heuristic_counts.most_common(),
        "risk_flags": risk_counts.most_common(),
        "top_entities_by_events": matrix[:8],
        "top_entities_by_suppression": sorted(matrix, key=lambda item: (-int(item["suppressed_count"]), str(item["entity_id"])))[:8],
        "matrix": matrix,
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
    total_entity_rows = sum(int(scope["matrix_entity_count"]) for scope in scopes)
    total_observed_entities = sum(int(scope["observed_entity_count"]) for scope in scopes)
    total_suppressed = sum(int(scope["suppressed_count"]) for scope in scopes)
    total_entity_suppression_rows = sum(int(scope["entity_suppression_row_count"]) for scope in scopes)
    total_strong = sum(int(scope["strong_decision_count"]) for scope in scopes)
    total_hard = sum(int(scope["strong_with_hard_authority"]) for scope in scopes)
    legacy_low_authority = sum(int(scope["legacy_low_authority_warning_count"]) for scope in scopes)
    native_scope = next((scope for scope in scopes if scope["scope"] == "native"), {})
    native_clean = bool(native_scope.get("native_matrix_clean"))
    if errors:
        classification = "ENTITY_NO_TICK_MATRIX_FAIL"
    elif warnings:
        classification = "ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS"
    else:
        classification = "ENTITY_NO_TICK_MATRIX_READY"
    return {
        "schema_version": "pnva.entity_no_tick_matrix.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not errors,
        "scope_count": len(scopes),
        "event_count": total_events,
        "entity_row_count": total_entity_rows,
        "observed_entity_row_count": total_observed_entities,
        "entity_suppression_row_count": total_entity_suppression_rows,
        "suppressed_count": total_suppressed,
        "strong_decision_count": total_strong,
        "strong_with_hard_authority": total_hard,
        "legacy_low_authority_warning_count": legacy_low_authority,
        "aggregate_no_tick_suppression_ratio": _ratio(total_suppressed, total_events),
        "aggregate_entity_suppression_coverage_ratio": _ratio(total_entity_suppression_rows, total_observed_entities),
        "native_matrix_clean": native_clean,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "scopes": scopes,
        "summary": {
            "total_event_count": total_events,
            "total_entity_rows": total_entity_rows,
            "total_observed_entity_rows": total_observed_entities,
            "entity_suppression_row_count": total_entity_suppression_rows,
            "total_suppressed_count": total_suppressed,
            "aggregate_no_tick_suppression_ratio": _ratio(total_suppressed, total_events),
            "total_strong_decision_count": total_strong,
            "total_strong_with_hard_authority": total_hard,
            "legacy_low_authority_warning_count": legacy_low_authority,
            "native_matrix_clean": native_clean,
        },
        "errors": errors,
        "warnings": warnings,
        "interpretation": {
            "purpose": "Expose PNVA no-tick behavior as an entity-by-heuristic matrix.",
            "sovereignty": "A no-tick decision is stronger when suppression, execution, proof, authority and risk are attributable to a concrete entity.",
            "boundary": "This matrix aggregates public sanitized evidence; it does not expose raw private local logs or commercial tuning.",
        },
        "recommendations": [
            "Use this matrix to select the next entity-level hardening target.",
            "Keep native entity rows clean: no missing proof, no missing catalog, no low-authority strong decision.",
            "Treat canonical legacy warnings as migration debt until all production events are emitted natively.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a PNVA no-tick matrix by entity and heuristic rule.")
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
