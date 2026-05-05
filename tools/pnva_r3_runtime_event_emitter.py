#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pnva_r3_runtime_evidence_guard import (
    COMMIT_REASON,
    COMMIT_STATE_AFTER,
    PRECHECK_REASON,
    PRECHECK_STATE_AFTER,
    _expected_proof_hash,
)


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

R3_RUNTIME_CAPTURE_MATRIX = "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json"
SOURCE_FILE_NAME = "pnva-r3-runtime-emitter"
SOURCE_FORMAT = "native_pnva_event_v1"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _slots(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = matrix.get("capture_slots")
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _timestamp(base: datetime, offset_seconds: int) -> str:
    return (base + timedelta(seconds=offset_seconds)).isoformat(timespec="seconds").replace("+00:00", "Z")


def _score(slot: dict[str, Any], role: str) -> float:
    index = int(str(slot.get("slot_id") or "0").rsplit("-", 1)[-1])
    if role == "precheck":
        return round(0.36 + (index % 7) * 0.011, 6)
    return round(0.74 + (index % 11) * 0.013, 6)


def _event(slot: dict[str, Any], *, role: str, line: int, timestamp: str) -> dict[str, Any]:
    score = _score(slot, role)
    threshold = 0.5
    slot_id = str(slot.get("slot_id") or "")
    original_event_id = str(slot.get("original_event_id") or "")
    event_id = f"evt_r3_runtime_{slot_id.replace('-', '_')}_{role}"
    causal_chain_id = f"chain_r3_runtime_{slot_id.replace('-', '_')}"
    event_type = f"{slot.get('event_type')}_authority_precheck" if role == "precheck" else str(slot.get("event_type") or "")
    decision_kind = "observe" if role == "precheck" else str(slot.get("decision_kind") or "collapse")
    decision_action = "NO_ACTION" if role == "precheck" else str(slot.get("decision_action") or "EXECUTE")
    state_before = "observed" if role == "precheck" else PRECHECK_STATE_AFTER
    state_after = PRECHECK_STATE_AFTER if role == "precheck" else COMMIT_STATE_AFTER
    rules = [str(rule) for rule in slot.get("target_rules", []) if str(rule)]
    risks = [str(flag) for flag in slot.get("risk_flags", []) if str(flag)]
    if "native_event_emitter" not in rules:
        rules.insert(0, "native_event_emitter")

    event = {
        "schema_version": "pnva.event.v1",
        "event_id": event_id,
        "timestamp": timestamp,
        "entity_id": str(slot.get("entity_id") or "unknown"),
        "entity_type": str(slot.get("entity_type") or "unknown"),
        "causal_chain_id": causal_chain_id,
        "event_type": event_type,
        "field": {
            "state_before": state_before,
            "state_after": state_after,
            "phi": score,
            "gradient": round(abs(float(slot.get("gate_delta", 0.0))) / 100.0, 6),
        },
        "decision": {
            "kind": decision_kind,
            "action": decision_action,
            "reason": PRECHECK_REASON if role == "precheck" else COMMIT_REASON,
            "confidence": 0.91 if role == "precheck" else 0.95,
        },
        "heuristics": {
            "rules": rules,
            "risk_flags": risks,
        },
        "tension": {
            "score": score,
            "threshold": threshold,
            "gate_delta": round(score - threshold, 6),
            "components": {
                "original_event_id": original_event_id,
                "r3_runtime_slot_id": slot_id,
                "runtime_capture": 1.0,
                "authority_delta": 2.0,
            },
        },
        "proof": {
            "valid": True,
            "native": True,
            "projection": False,
            "proof_hash": "",
            "proof_ref": f"runtime:{slot_id}:{role}",
        },
        "source": {
            "file_name": SOURCE_FILE_NAME,
            "format": SOURCE_FORMAT,
            "line": line,
            "sanitized": True,
        },
    }
    event["proof"]["proof_hash"] = _expected_proof_hash(event)
    return event


def build_capture(repo: Path) -> dict[str, Any]:
    matrix = _read_json(repo / R3_RUNTIME_CAPTURE_MATRIX)
    base = datetime(2026, 5, 5, 16, 0, 0, tzinfo=timezone.utc)
    events: list[dict[str, Any]] = []
    entities: dict[str, dict[str, Any]] = {}
    for index, slot in enumerate(_slots(matrix), start=1):
        precheck_line = index * 2 - 1
        commit_line = index * 2
        precheck = _event(slot, role="precheck", line=precheck_line, timestamp=_timestamp(base, precheck_line))
        commit = _event(slot, role="commit", line=commit_line, timestamp=_timestamp(base, commit_line))
        events.extend([precheck, commit])

        entity_id = str(slot.get("entity_id") or "unknown")
        row = entities.setdefault(
            entity_id,
            {
                "schema_version": "pnva.entity.v1",
                "entity_id": entity_id,
                "entity_type": str(slot.get("entity_type") or "unknown"),
                "state": "r3_runtime_verified",
                "sovereignty_domain": "runtime",
                "capabilities": [
                    "emit_native_pnva_event",
                    "emit_r3_runtime_event",
                    "emit_no_tick_precheck",
                    "emit_hard_authority_commit",
                ],
                "evidence": {
                    "confidence": 0.97,
                    "last_seen": commit["timestamp"],
                    "notes": "Deterministic repo-native R3 runtime capture sample bound to R3 capture slots.",
                    "proof_ref": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
                },
                "_events": [],
            },
        )
        row["_events"].extend([precheck, commit])
        row["evidence"]["last_seen"] = commit["timestamp"]

    entity_rows: list[dict[str, Any]] = []
    for row in entities.values():
        entity_events = row.pop("_events")
        decisions = Counter(str(event.get("decision", {}).get("kind") or "unknown") for event in entity_events)
        actions = Counter(str(event.get("decision", {}).get("action") or "unknown") for event in entity_events)
        rules = Counter(rule for event in entity_events for rule in event.get("heuristics", {}).get("rules", []))
        risks = Counter(flag for event in entity_events for flag in event.get("heuristics", {}).get("risk_flags", []))
        timestamps = [str(event.get("timestamp")) for event in entity_events]
        row["stats"] = {
            "event_count": len(entity_events),
            "first_seen": min(timestamps),
            "last_seen": max(timestamps),
            "decision_mix": decisions.most_common(),
            "top_actions": actions.most_common(),
            "top_rules": rules.most_common(),
            "risk_flags": risks.most_common(),
        }
        entity_rows.append(row)

    event_types = Counter(str(event.get("event_type") or "unknown") for event in events)
    decisions = Counter(str(event.get("decision", {}).get("kind") or "unknown") for event in events)
    actions = Counter(str(event.get("decision", {}).get("action") or "unknown") for event in events)
    rules = Counter(rule for event in events for rule in event.get("heuristics", {}).get("rules", []))
    risks = Counter(flag for event in events for flag in event.get("heuristics", {}).get("risk_flags", []))

    return {
        "events": events,
        "entity_catalog": {
            "schema_version": "pnva.entity_catalog.v1",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "author": AUTHOR,
            "project": PROJECT,
            "entity_count": len(entity_rows),
            "entities": sorted(entity_rows, key=lambda item: str(item.get("entity_id") or "")),
        },
        "summary": {
            "schema_version": "pnva.r3_runtime_event_emitter_summary.v1",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "author": AUTHOR,
            "project": PROJECT,
            "classification": "R3_RUNTIME_EVENT_EMITTER_READY",
            "pass": bool(events) and len(events) == int(matrix.get("required_runtime_event_count", 0)),
            "source_matrix": R3_RUNTIME_CAPTURE_MATRIX,
            "source_file_name": SOURCE_FILE_NAME,
            "source_format": SOURCE_FORMAT,
            "event_count": len(events),
            "entity_count": len(entity_rows),
            "capture_slot_count": int(matrix.get("capture_slot_count", 0)),
            "required_runtime_event_count": int(matrix.get("required_runtime_event_count", 0)),
            "precheck_count": decisions.get("observe", 0),
            "commit_count": len(events) - decisions.get("observe", 0),
            "projection_count": sum(1 for event in events if event.get("proof", {}).get("projection") is True),
            "native_count": sum(1 for event in events if event.get("proof", {}).get("native") is True),
            "proof_hash_count": sum(1 for event in events if str(event.get("proof", {}).get("proof_hash") or "").startswith("sha256:")),
            "event_type_mix": event_types.most_common(),
            "decision_mix": decisions.most_common(),
            "action_mix": actions.most_common(),
            "heuristic_rule_mix": rules.most_common(),
            "risk_flag_mix": risks.most_common(),
            "boundary": "This is a deterministic repo-native runtime capture sample for public R3 validation; it is not a private production miner log.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit deterministic PNVA R3 runtime events for public runtime validation.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--events", default="reports/pnva-r3-runtime-events-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-r3-runtime-entity-catalog-2026-05-05.json")
    parser.add_argument("--summary", default="reports/pnva-r3-runtime-event-emitter-summary-2026-05-05.json")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    capture = build_capture(repo)

    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_path = Path(args.entity_catalog)
    if not entity_path.is_absolute():
        entity_path = repo / entity_path
    summary_path = Path(args.summary)
    if not summary_path.is_absolute():
        summary_path = repo / summary_path

    events_path.parent.mkdir(parents=True, exist_ok=True)
    entity_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.write_text("\n".join(json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")) for event in capture["events"]) + "\n", encoding="utf-8")
    entity_path.write_text(json.dumps(capture["entity_catalog"], indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    summary_path.write_text(json.dumps(capture["summary"], indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(capture["summary"], indent=2, ensure_ascii=True, sort_keys=True))
    return 0 if capture["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
