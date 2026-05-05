#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from pnva_r3_runtime_evidence_guard import _expected_proof_hash as _expected_r3_runtime_proof_hash
except Exception:  # pragma: no cover - replay must still work without R3 tooling.
    _expected_r3_runtime_proof_hash = None


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


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_time(value: Any) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except Exception:
        return float(default)
    if numeric != numeric:
        return float(default)
    return float(numeric)


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


def _expected_proof_hash(event: dict[str, Any]) -> str:
    return "sha256:" + _sha(_proof_seed(event))


def _expected_proof_hashes(event: dict[str, Any]) -> list[str]:
    hashes = [_expected_proof_hash(event)]
    proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
    proof_ref = str(proof.get("proof_ref") or "")
    if proof_ref.startswith("runtime:") and _expected_r3_runtime_proof_hash is not None:
        hashes.append(_expected_r3_runtime_proof_hash(event))
    return hashes


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
    if not isinstance(data, dict):
        return set()
    entities = data.get("entities", [])
    if not isinstance(entities, list):
        return set()
    return {str(item.get("entity_id", "")) for item in entities if isinstance(item, dict) and item.get("entity_id")}


def validate_events(events: list[dict[str, Any]], *, entity_ids: set[str], strict_order: bool) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    chains: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_types: Counter[str] = Counter()
    decision_kinds: Counter[str] = Counter()
    actions: Counter[str] = Counter()
    risk_flags: Counter[str] = Counter()
    relation_count = 0
    proof_hash_ok = 0
    proof_hash_bad = 0
    guard_pass_ok = 0
    guard_block_ok = 0
    previous_ts: dt.datetime | None = None
    global_disorder = 0

    for index, event in enumerate(events, start=1):
        line = int(event.get("_line", index))
        missing = sorted(REQUIRED_EVENT_KEYS.difference(event))
        if missing:
            errors.append({"line": line, "code": "MISSING_REQUIRED_KEYS", "missing": missing})
            continue
        if event.get("schema_version") != "pnva.event.v1":
            errors.append({"line": line, "code": "BAD_SCHEMA_VERSION", "value": event.get("schema_version")})
        event_id = str(event.get("event_id") or "")
        if event_id in event_ids:
            errors.append({"line": line, "code": "DUPLICATE_EVENT_ID", "event_id": event_id})
        event_ids.add(event_id)
        timestamp = _parse_time(event.get("timestamp"))
        if timestamp is None:
            errors.append({"line": line, "code": "BAD_TIMESTAMP", "timestamp": event.get("timestamp")})
        elif previous_ts and timestamp < previous_ts:
            global_disorder += 1
            warning = {
                "line": line,
                "code": "GLOBAL_TIMESTAMP_DISORDER",
                "event_id": event_id,
                "timestamp": event.get("timestamp"),
            }
            if strict_order:
                errors.append(warning)
            else:
                warnings.append(warning)
        if timestamp is not None:
            previous_ts = timestamp

        chain_id = str(event.get("causal_chain_id") or "")
        chains[chain_id].append(event)
        event_type = str(event.get("event_type") or "")
        event_types[event_type] += 1
        decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
        decision_kind = str(decision.get("kind") or "")
        action = str(decision.get("action") or "")
        decision_kinds[decision_kind] += 1
        actions[action] += 1
        for flag in event.get("heuristics", {}).get("risk_flags", []) if isinstance(event.get("heuristics"), dict) else []:
            risk_flags[str(flag)] += 1

        proof = event.get("proof", {}) if isinstance(event.get("proof"), dict) else {}
        expected_hashes = _expected_proof_hashes(event)
        if proof.get("proof_hash") in expected_hashes and proof.get("valid") is True:
            proof_hash_ok += 1
        else:
            proof_hash_bad += 1
            errors.append(
                {
                    "line": line,
                    "code": "PROOF_HASH_MISMATCH",
                    "event_id": event_id,
                    "expected": expected_hashes[0],
                    "accepted_hash_policy_count": len(expected_hashes),
                    "observed": proof.get("proof_hash"),
                }
            )

        tension = event.get("tension", {}) if isinstance(event.get("tension"), dict) else {}
        gate_delta = _safe_float(tension.get("gate_delta"))
        lowered = event_type.lower()
        if "etev_guard_pass" in lowered:
            if decision_kind == "collapse" and gate_delta >= -1e-9:
                guard_pass_ok += 1
            else:
                errors.append({"line": line, "code": "GUARD_PASS_INCONSISTENT", "event_id": event_id, "gate_delta": gate_delta, "decision_kind": decision_kind})
        if "etev_guard_block" in lowered:
            if decision_kind == "block" and gate_delta <= 1e-9:
                guard_block_ok += 1
            else:
                errors.append({"line": line, "code": "GUARD_BLOCK_INCONSISTENT", "event_id": event_id, "gate_delta": gate_delta, "decision_kind": decision_kind})

        relations = event.get("relations")
        if isinstance(relations, dict) and relations.get("target_entity_id"):
            relation_count += 1
            target = str(relations.get("target_entity_id"))
            if entity_ids and target not in entity_ids:
                warnings.append({"line": line, "code": "RELATION_TARGET_NOT_IN_ENTITY_CATALOG", "event_id": event_id, "target_entity_id": target})

    chain_disorder = 0
    chain_lengths = {}
    for chain_id, chain_events in chains.items():
        chain_lengths[chain_id] = len(chain_events)
        prev: dt.datetime | None = None
        for event in chain_events:
            timestamp = _parse_time(event.get("timestamp"))
            if timestamp is None:
                continue
            if prev and timestamp < prev:
                chain_disorder += 1
                warning = {
                    "code": "CHAIN_TIMESTAMP_DISORDER",
                    "chain_id": chain_id,
                    "event_id": event.get("event_id"),
                    "timestamp": event.get("timestamp"),
                }
                if strict_order:
                    errors.append(warning)
                else:
                    warnings.append(warning)
            prev = timestamp

    return {
        "pass": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "event_count": len(events),
            "unique_event_ids": len(event_ids),
            "chain_count": len(chains),
            "relation_count": relation_count,
            "proof_hash_ok": proof_hash_ok,
            "proof_hash_bad": proof_hash_bad,
            "guard_pass_ok": guard_pass_ok,
            "guard_block_ok": guard_block_ok,
            "global_timestamp_disorder": global_disorder,
            "chain_timestamp_disorder": chain_disorder,
            "top_event_types": event_types.most_common(12),
            "top_decision_kinds": decision_kinds.most_common(12),
            "top_actions": actions.most_common(12),
            "risk_flags": risk_flags.most_common(12),
            "largest_chains": Counter(chain_lengths).most_common(8),
        },
    }


def build_report(events_path: Path, entity_catalog_path: Path, *, strict_order: bool = False) -> dict[str, Any]:
    events, parse_errors = _load_events(events_path)
    entity_ids = _load_entity_ids(entity_catalog_path)
    validation = validate_events(events, entity_ids=entity_ids, strict_order=strict_order)
    errors = list(parse_errors) + validation["errors"]
    report = {
        "schema_version": "pnva.replay_validation.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "events_ref": str(events_path),
        "entity_catalog_ref": str(entity_catalog_path),
        "strict_order": bool(strict_order),
        "pass": not errors,
        "classification": "REPLAY_VALID" if not errors else "REPLAY_INVALID",
        "errors": errors,
        "warnings": validation["warnings"],
        "summary": validation["summary"],
        "interpretation": {
            "no_tick_meaning": "The canonical sequence can be replay-validated without rewriting runtime history.",
            "proof_meaning": "Each event proof hash is deterministic over sanitized canonical content.",
            "warning_policy": "Timestamp disorder is a warning in sampled multi-source logs unless strict ordering is requested.",
        },
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate replay invariants for PNVA canonical event sequences.")
    parser.add_argument("--events", default="reports/pnva-canonical-events-sample-2026-05-05.jsonl")
    parser.add_argument("--entity-catalog", default="reports/pnva-entity-catalog-2026-05-05.json")
    parser.add_argument("--write", default="")
    parser.add_argument("--strict-order", action="store_true")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    events_path = Path(args.events)
    if not events_path.is_absolute():
        events_path = repo / events_path
    entity_catalog_path = Path(args.entity_catalog)
    if not entity_catalog_path.is_absolute():
        entity_catalog_path = repo / entity_catalog_path
    report = build_report(events_path, entity_catalog_path, strict_order=bool(args.strict_order))
    report["events_ref"] = str(events_path.relative_to(repo)) if events_path.is_relative_to(repo) else events_path.name
    report["entity_catalog_ref"] = str(entity_catalog_path.relative_to(repo)) if entity_catalog_path.is_relative_to(repo) else entity_catalog_path.name
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
