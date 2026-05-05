#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
SCHEMA_VERSION = "pnva.event.v1"
CANONICAL_EVENTS = "reports/pnva-canonical-events-sample-2026-05-05.jsonl"
AUTHORITY_LEDGER = "reports/pnva-authority-migration-ledger-2026-05-05.json"

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


def _sha(value: str, size: int = 64) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:size]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"{path}:{line_no}: event is not an object")
            event["_line"] = line_no
            events.append(event)
    return events


def _safe_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        numeric = float(value)
    except Exception:
        return default
    if not math.isfinite(numeric):
        return default
    return float(numeric)


def _round(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def _decision(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("decision")
    return value if isinstance(value, dict) else {}


def _decision_kind(event: dict[str, Any]) -> str:
    return str(_decision(event).get("kind") or "unknown")


def _decision_action(event: dict[str, Any]) -> str:
    return str(_decision(event).get("action") or "unknown")


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


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda level: AUTHORITY_ORDER[level])


def _is_low_authority_strong(event: dict[str, Any]) -> bool:
    return _decision_kind(event) in STRONG_DECISIONS and _max_authority(_rules(event)) not in HARD_AUTHORITIES


def _target_rules(event: dict[str, Any]) -> list[str]:
    action = _decision_action(event)
    flags = set(_risk_flags(event))
    if action == "COOLDOWN_GPU" or any("THERMAL" in flag or "COOLDOWN" in flag for flag in flags):
        return ["native_event_emitter", "power_orchestrator", "field_scheduler", "adaptive_threshold"]
    return ["native_event_emitter", "adaptive_threshold", "field_scheduler"]


def _proof_seed(event: dict[str, Any]) -> str:
    source = event.get("source", {}) if isinstance(event.get("source"), dict) else {}
    payload = {
        "source": source.get("file_name", ""),
        "line": source.get("line", 0),
        "timestamp": event.get("timestamp", ""),
        "entity_id": event.get("entity_id", ""),
        "event_type": event.get("event_type", ""),
        "decision": event.get("decision", {}),
        "tension": event.get("tension", {}),
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _proof_hash(event: dict[str, Any]) -> str:
    return "sha256:" + _sha(_proof_seed(event), 64)


def _event_id(event: dict[str, Any], original_id: str, role: str) -> str:
    seed = _proof_seed(event) + "|" + original_id + "|" + role
    return f"evt_r3auth_{role}_{_sha(seed, 16)}"


def _field(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("field")
    return value if isinstance(value, dict) else {}


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tension")
    return value if isinstance(value, dict) else {}


def _components(event: dict[str, Any]) -> dict[str, Any]:
    value = _tension(event).get("components")
    return value if isinstance(value, dict) else {}


def _project_event(original: dict[str, Any], *, role: str, line: int) -> dict[str, Any]:
    original_id = str(original.get("event_id") or "")
    action = _decision_action(original)
    rules = sorted(set(_target_rules(original)))
    original_tension = _tension(original)
    original_components = _components(original)
    original_score = _safe_float(original_tension.get("score"))
    hash4d_score = _safe_float(original_components.get("hash4d_score"), 0.65)
    helper_health = _safe_float(original_components.get("runtime_helper_health"), 0.80)
    native_threshold = 0.60

    if role == "precheck":
        score = min(0.49, max(0.10, abs(original_score) / 100.0 + hash4d_score * 0.20))
        decision_kind = "observe"
        projected_action = "NO_ACTION"
        reason = "native_authority_precheck_no_tick"
        state_after = "native_authority_checked"
        risk_flags = sorted(set(_risk_flags(original) + ["R3_AUTHORITY_PREFLIGHT"]))
    else:
        score = min(0.95, max(0.64, hash4d_score * 0.70 + helper_health * 0.20 + 0.12))
        decision_kind = "collapse"
        projected_action = action
        reason = "native_authority_projection_authorized"
        state_after = str(_field(original).get("state_after") or "resolved")
        risk_flags = sorted(set(_risk_flags(original) + ["R3_AUTHORITY_PROJECTED"]))

    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": "",
        "timestamp": str(original.get("timestamp") or ""),
        "causal_chain_id": f"chain_r3_authority_projection_{_sha(original_id, 12)}",
        "entity_id": str(original.get("entity_id") or "unknown"),
        "entity_type": str(original.get("entity_type") or "event_source"),
        "event_type": "cuda_slot_scan_authority_precheck" if role == "precheck" else str(original.get("event_type") or "cuda_slot_scan"),
        "field": {
            "state_before": str(_field(original).get("state_before") or "observing"),
            "state_after": state_after,
            "phi": _round(score),
            "gradient": _round(hash4d_score),
            "hessian": _round(helper_health),
        },
        "tension": {
            "score": _round(score),
            "threshold": native_threshold,
            "margin": 0.0,
            "gate_delta": _round(score - native_threshold),
            "components": {
                "original_event_id": original_id,
                "original_score": _round(original_score),
                "original_gate_delta": _round(_safe_float(original_tension.get("gate_delta"))),
                "hash4d_score": _round(hash4d_score),
                "runtime_helper_health": _round(helper_health),
                "authority_projection": 1.0,
                "r3_candidate": 1.0,
            },
        },
        "decision": {
            "kind": decision_kind,
            "action": projected_action,
            "reason": reason,
            "confidence": 0.93 if role == "commit" else 0.88,
        },
        "heuristics": {
            "rules": rules,
            "risk_flags": risk_flags,
        },
        "proof": {
            "proof_hash": "",
            "proof_ref": f"r3-authority-projection:{original_id}:{role}",
            "valid": True,
            "canonical": False,
            "native": True,
            "projection": True,
        },
        "source": {
            "format": "native_pnva_event_v1",
            "file_name": "pnva-r3-authority-projection",
            "line": line,
            "sanitized": True,
            "projection_from": "authority_migration_ledger",
        },
    }
    event["event_id"] = _event_id(event, original_id, role)
    event["proof"]["proof_hash"] = _proof_hash(event)
    return event


def _entity_catalog(events: list[dict[str, Any]], *, events_ref: str) -> dict[str, Any]:
    by_entity: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        by_entity.setdefault(str(event.get("entity_id") or "unknown"), []).append(event)
    entities = []
    for entity_id, items in sorted(by_entity.items()):
        decisions = Counter(str(item.get("decision", {}).get("kind") or "unknown") for item in items)
        actions = Counter(str(item.get("decision", {}).get("action") or "unknown") for item in items)
        risks = Counter(flag for item in items for flag in item.get("heuristics", {}).get("risk_flags", []))
        rules = Counter(rule for item in items for rule in item.get("heuristics", {}).get("rules", []))
        timestamps = sorted(str(item.get("timestamp") or "") for item in items if item.get("timestamp"))
        entities.append(
            {
                "schema_version": "pnva.entity.v1",
                "entity_id": entity_id,
                "entity_type": str(items[0].get("entity_type") or "event_source"),
                "sovereignty_domain": "runtime",
                "state": "candidate",
                "capabilities": [
                    "emit_native_pnva_event",
                    "r3_authority_projection",
                    "hard_authority_decision",
                    "no_tick_precheck",
                ],
                "evidence": {
                    "proof_ref": events_ref,
                    "confidence": 0.94,
                    "last_seen": timestamps[-1] if timestamps else "",
                    "notes": "R3 authority projection entity derived from public canonical legacy debt.",
                },
                "stats": {
                    "event_count": len(items),
                    "first_seen": timestamps[0] if timestamps else "",
                    "last_seen": timestamps[-1] if timestamps else "",
                    "decision_mix": decisions.most_common(),
                    "top_actions": actions.most_common(),
                    "top_rules": rules.most_common(),
                    "risk_flags": risks.most_common(),
                },
            }
        )
    return {
        "schema_version": "pnva.entity_catalog.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "entity_count": len(entities),
        "entities": entities,
    }


def build_projection(repo: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    canonical_events = _load_jsonl(repo / CANONICAL_EVENTS)
    ledger = _read_json(repo / AUTHORITY_LEDGER)
    candidates = [event for event in canonical_events if _is_low_authority_strong(event)]
    projected: list[dict[str, Any]] = []
    for index, event in enumerate(candidates, 1):
        projected.append(_project_event(event, role="precheck", line=(index * 2) - 1))
        projected.append(_project_event(event, role="commit", line=index * 2))

    decisions = Counter(str(event.get("decision", {}).get("kind") or "unknown") for event in projected)
    actions = Counter(str(event.get("decision", {}).get("action") or "unknown") for event in projected)
    rules = Counter(rule for event in projected for rule in event.get("heuristics", {}).get("rules", []))
    risks = Counter(flag for event in projected for flag in event.get("heuristics", {}).get("risk_flags", []))
    strong_count = sum(1 for event in projected if str(event.get("decision", {}).get("kind")) in STRONG_DECISIONS)
    low_authority_strong = sum(
        1
        for event in projected
        if str(event.get("decision", {}).get("kind")) in STRONG_DECISIONS
        and _max_authority([str(rule) for rule in event.get("heuristics", {}).get("rules", [])]) not in HARD_AUTHORITIES
    )
    proof_valid = sum(
        1
        for event in projected
        if event.get("proof", {}).get("valid") is True and str(event.get("proof", {}).get("proof_hash") or "").startswith("sha256:")
    )
    candidate_count = len(candidates)
    summary = {
        "schema_version": "pnva.r3_authority_projection_summary.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": "R3_AUTHORITY_PROJECTION_READY",
        "pass": True,
        "source_candidate_count": candidate_count,
        "ledger_candidate_count": int(ledger.get("candidate_event_count", 0)),
        "candidate_count_matches_ledger": candidate_count == int(ledger.get("candidate_event_count", 0)),
        "projected_event_count": len(projected),
        "projected_native_event_count": len(projected),
        "projected_precheck_count": decisions.get("observe", 0),
        "projected_commit_count": decisions.get("collapse", 0),
        "projected_strong_decision_count": strong_count,
        "projected_low_authority_strong_count": low_authority_strong,
        "projected_no_tick_suppression_count": decisions.get("observe", 0),
        "projected_no_tick_suppression_ratio": round(decisions.get("observe", 0) / max(1, len(projected)), 6),
        "proof_valid_count": proof_valid,
        "proof_coverage_ratio": round(proof_valid / max(1, len(projected)), 6),
        "entity_count": len({event.get("entity_id") for event in projected}),
        "decision_mix": decisions.most_common(),
        "action_mix": actions.most_common(),
        "rule_mix": rules.most_common(),
        "risk_flags": risks.most_common(),
        "reports_checked": {
            "canonical_events": CANONICAL_EVENTS,
            "authority_migration_ledger": AUTHORITY_LEDGER,
        },
        "interpretation": {
            "purpose": "Project the R3-A1 authority migration debt into native hard-authority pnva.event.v1 evidence before runtime replacement.",
            "no_tick": "Each migrated strong decision receives a native observe precheck before the native collapse event.",
            "boundary": "This is a reproducible projection, not a claim that historical H0 events were originally native H2 events.",
        },
        "recommendations": [
            "Use this projection as the implementation contract for the runtime cuda_slot_scan native emitter.",
            "Keep the legacy sample unchanged until fresh runtime evidence replaces the projected candidate.",
            "Require policy, replay and no-tick validation before claiming R3_NATIVE_CLEAN_LEGACY_FREE.",
        ],
    }
    if not summary["candidate_count_matches_ledger"] or low_authority_strong or proof_valid != len(projected):
        summary["classification"] = "R3_AUTHORITY_PROJECTION_FAIL"
        summary["pass"] = False
    return projected, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a native R3 authority projection from PNVA legacy authority debt.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--events", default="reports/pnva-r3-authority-projection-events-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-r3-authority-projection-entities-2026-05-05.json")
    parser.add_argument("--summary", default="reports/pnva-r3-authority-projection-summary-2026-05-05.json")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    catalog_path = Path(args.entity_catalog)
    if not catalog_path.is_absolute():
        catalog_path = repo / catalog_path
    summary_path = Path(args.summary)
    if not summary_path.is_absolute():
        summary_path = repo / summary_path

    events, summary = build_projection(repo)
    for path in (events_path, catalog_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True, ensure_ascii=True, separators=(",", ":")) + "\n" for event in events),
        encoding="utf-8",
    )
    events_ref = str(events_path.relative_to(repo)) if events_path.is_relative_to(repo) else events_path.name
    catalog = _entity_catalog(events, events_ref=events_ref)
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    summary["events_ref"] = events_ref
    summary["entity_catalog_ref"] = str(catalog_path.relative_to(repo)) if catalog_path.is_relative_to(repo) else catalog_path.name
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True))
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
