#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

R3_RUNTIME_CAPTURE_MATRIX = "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json"

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
PRECHECK_DECISIONS = {"observe", "block"}
PROOF_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
RUNTIME_PROOF_REF_RE = re.compile(r"^runtime:[A-Za-z0-9_.:-]+:(precheck|commit)$")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    bad_lines: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except Exception as exc:
                bad_lines.append({"line": line_no, "code": "JSON_PARSE_ERROR", "detail": str(exc)})
                continue
            if not isinstance(value, dict):
                bad_lines.append({"line": line_no, "code": "JSON_EVENT_NOT_OBJECT", "detail": "event is not an object"})
                continue
            value["_line"] = line_no
            events.append(value)
    return events, bad_lines


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


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
    value = _heuristics(event).get("rules")
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _risk_flags(event: dict[str, Any]) -> list[str]:
    value = _heuristics(event).get("risk_flags")
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _authority(rule: str) -> str:
    return RULE_AUTHORITY.get(rule, "H1")


def _max_authority(rules: list[str]) -> str:
    if not rules:
        return "H0"
    return max((_authority(rule) for rule in rules), key=lambda level: AUTHORITY_ORDER[level])


def _proof(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("proof")
    return value if isinstance(value, dict) else {}


def _proof_clean(event: dict[str, Any]) -> bool:
    proof = _proof(event)
    return (
        proof.get("valid") is True
        and proof.get("projection") is not True
        and _proof_hash_valid(proof.get("proof_hash"))
        and bool(proof.get("proof_ref"))
    )


def _components(event: dict[str, Any]) -> dict[str, Any]:
    return _dig(event, ["tension", "components"], {}) if isinstance(_dig(event, ["tension", "components"], {}), dict) else {}


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tension")
    return value if isinstance(value, dict) else {}


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _proof_hash_valid(value: Any) -> bool:
    return isinstance(value, str) and bool(PROOF_HASH_RE.fullmatch(value))


def _source(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("source")
    return value if isinstance(value, dict) else {}


def _proof_hash_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": event.get("schema_version"),
        "event_id": event.get("event_id"),
        "timestamp": event.get("timestamp"),
        "entity_id": event.get("entity_id"),
        "entity_type": event.get("entity_type"),
        "causal_chain_id": event.get("causal_chain_id"),
        "event_type": event.get("event_type"),
        "field": {
            "state_before": _dig(event, ["field", "state_before"]),
            "state_after": _dig(event, ["field", "state_after"]),
        },
        "decision": {
            "kind": _decision_kind(event),
            "action": _decision_action(event),
            "reason": str(_decision(event).get("reason") or ""),
        },
        "heuristics": {
            "rules": _rules(event),
            "risk_flags": _risk_flags(event),
        },
        "tension": {
            "score": _tension(event).get("score"),
            "threshold": _tension(event).get("threshold"),
            "gate_delta": _tension(event).get("gate_delta"),
            "components": {
                "original_event_id": _original_id(event),
                "r3_runtime_slot_id": _r3_slot_id(event),
            },
        },
        "proof": {
            "proof_ref": _proof(event).get("proof_ref"),
            "native": _proof(event).get("native"),
            "projection": _proof(event).get("projection"),
            "valid": _proof(event).get("valid"),
        },
        "source": {
            "format": _source(event).get("format"),
            "sanitized": _source(event).get("sanitized"),
        },
    }


def _expected_proof_hash(event: dict[str, Any]) -> str:
    payload = json.dumps(_proof_hash_payload(event), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return "sha256:" + _sha256_text(payload)


def _proof_ref_role_valid(event: dict[str, Any], slot: dict[str, Any], role: str) -> bool:
    proof_ref = _proof(event).get("proof_ref")
    if not isinstance(proof_ref, str) or not RUNTIME_PROOF_REF_RE.fullmatch(proof_ref):
        return False
    return proof_ref == f"runtime:{slot.get('slot_id')}:{role}"


def _gate_delta_consistent(event: dict[str, Any]) -> bool:
    tension = _tension(event)
    score = tension.get("score")
    threshold = tension.get("threshold")
    gate_delta = tension.get("gate_delta")
    if not (_finite_number(score) and _finite_number(threshold) and _finite_number(gate_delta)):
        return False
    return abs(float(gate_delta) - (float(score) - float(threshold))) <= 0.000001


def _timestamp_epoch(event: dict[str, Any]) -> float | None:
    value = event.get("timestamp")
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.timestamp()


def _field_state_valid(event: dict[str, Any]) -> bool:
    field = event.get("field")
    return isinstance(field, dict) and bool(field.get("state_before")) and bool(field.get("state_after"))


def _heuristic_rule_codes(event: dict[str, Any]) -> list[str]:
    value = _heuristics(event).get("rules")
    if not isinstance(value, list) or not value:
        return ["HEURISTICS_RULES_INVALID"]
    rules = [str(item) for item in value if str(item)]
    codes: list[str] = []
    if len(rules) != len(value):
        codes.append("HEURISTICS_RULES_INVALID")
    if len(set(rules)) != len(rules):
        codes.append("HEURISTIC_RULE_DUPLICATE")
    if any(rule not in RULE_AUTHORITY for rule in rules):
        codes.append("HEURISTIC_RULE_UNKNOWN")
    return codes


def _heuristic_risk_flag_codes(event: dict[str, Any], slot: dict[str, Any]) -> list[str]:
    value = _heuristics(event).get("risk_flags")
    if not isinstance(value, list):
        return ["RISK_FLAGS_INVALID"]

    flags = [item.strip() for item in value if isinstance(item, str) and item.strip()]
    codes: list[str] = []
    if len(flags) != len(value):
        codes.append("RISK_FLAGS_INVALID")
    if len(set(flags)) != len(flags):
        codes.append("RISK_FLAG_DUPLICATE")

    allowed_flags = {str(flag).strip() for flag in slot.get("risk_flags", []) if str(flag).strip()}
    if any(flag not in allowed_flags for flag in flags):
        codes.append("RISK_FLAG_UNKNOWN")
    return codes


def _original_id(event: dict[str, Any]) -> str:
    return str(_components(event).get("original_event_id") or "")


def _r3_slot_id(event: dict[str, Any]) -> str:
    return str(_components(event).get("r3_runtime_slot_id") or "")


def _slot_map(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = matrix.get("capture_slots")
    if not isinstance(slots, list):
        return {}
    return {str(slot.get("original_event_id") or ""): slot for slot in slots if isinstance(slot, dict) and slot.get("original_event_id")}


def _role(event: dict[str, Any], slot: dict[str, Any]) -> str:
    event_type = str(event.get("event_type") or "")
    reason = str(_decision(event).get("reason") or "")
    action = _decision_action(event)
    kind = _decision_kind(event)
    if "precheck" in event_type or "precheck" in reason or (kind in PRECHECK_DECISIONS and action == "NO_ACTION"):
        return "precheck"
    if kind == str(slot.get("decision_kind") or "") and action == str(slot.get("decision_action") or ""):
        return "commit"
    return "unknown"


def _expected_event_type(slot: dict[str, Any], role: str) -> str:
    base = str(slot.get("event_type") or "")
    return f"{base}_authority_precheck" if role == "precheck" else base


def _event_codes(event: dict[str, Any], slot: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    if event.get("schema_version") != "pnva.event.v1":
        codes.append("SCHEMA_VERSION_INVALID")
    if not event.get("event_id"):
        codes.append("MISSING_EVENT_ID")
    if not event.get("timestamp"):
        codes.append("MISSING_TIMESTAMP")
    elif _timestamp_epoch(event) is None:
        codes.append("TIMESTAMP_INVALID")
    if not event.get("entity_id"):
        codes.append("MISSING_ENTITY_ID")
    if not event.get("entity_type"):
        codes.append("MISSING_ENTITY_TYPE")
    if not event.get("causal_chain_id"):
        codes.append("MISSING_CAUSAL_CHAIN_ID")
    if not _field_state_valid(event):
        codes.append("FIELD_STATE_INVALID")
    tension = _tension(event)
    if not _finite_number(tension.get("score")):
        codes.append("TENSION_SCORE_INVALID")
    if not _finite_number(tension.get("threshold")):
        codes.append("TENSION_THRESHOLD_INVALID")
    if not _finite_number(tension.get("gate_delta")):
        codes.append("TENSION_GATE_DELTA_INVALID")
    elif not _gate_delta_consistent(event):
        codes.append("TENSION_GATE_DELTA_INCONSISTENT")
    if _proof(event).get("projection") is True:
        codes.append("PROJECTED_PROOF_FORBIDDEN")
    if _proof(event).get("native") is not True:
        codes.append("PROOF_NATIVE_REQUIRED")
    if not _proof_hash_valid(_proof(event).get("proof_hash")):
        codes.append("PROOF_HASH_FORMAT_INVALID")
    elif _proof(event).get("proof_hash") != _expected_proof_hash(event):
        codes.append("PROOF_HASH_BINDING_INVALID")
    if not _proof_clean(event):
        codes.append("PROOF_HASH_OR_VALIDITY_INVALID")
    if _source(event).get("format") != "native_pnva_event_v1":
        codes.append("SOURCE_FORMAT_INVALID")
    if _source(event).get("sanitized") is not True:
        codes.append("SOURCE_SANITIZED_REQUIRED")
    original = _original_id(event)
    if not original:
        codes.append("MISSING_ORIGINAL_EVENT_ID")
    if original and original != str(slot.get("original_event_id") or ""):
        codes.append("ORIGINAL_EVENT_MISMATCH")
    slot_id = _r3_slot_id(event)
    if not slot_id:
        codes.append("MISSING_R3_RUNTIME_SLOT_ID")
    if slot_id and slot_id != str(slot.get("slot_id") or ""):
        codes.append("R3_RUNTIME_SLOT_MISMATCH")
    if str(event.get("entity_id") or "") != str(slot.get("entity_id") or ""):
        codes.append("ENTITY_MISMATCH")
    if str(event.get("entity_type") or "") != str(slot.get("entity_type") or ""):
        codes.append("ENTITY_TYPE_MISMATCH")
    codes.extend(_heuristic_rule_codes(event))
    codes.extend(_heuristic_risk_flag_codes(event, slot))

    role = _role(event, slot)
    rules = set(_rules(event))
    risk_flags = set(_risk_flags(event))
    target_rules = set(str(rule) for rule in slot.get("target_rules", []) if str(rule))
    target_risk_flags = {str(flag).strip() for flag in slot.get("risk_flags", []) if str(flag).strip()}
    if role in {"precheck", "commit"} and not _proof_ref_role_valid(event, slot, role):
        codes.append("PROOF_REF_ROLE_MISMATCH")
    if role == "precheck":
        if str(event.get("event_type") or "") != _expected_event_type(slot, "precheck"):
            codes.append("PRECHECK_EVENT_TYPE_MISMATCH")
        if _decision_kind(event) not in PRECHECK_DECISIONS:
            codes.append("PRECHECK_DECISION_INVALID")
        if _decision_action(event) != "NO_ACTION":
            codes.append("PRECHECK_ACTION_INVALID")
        if _finite_number(tension.get("gate_delta")) and float(tension.get("gate_delta")) > 0:
            codes.append("PRECHECK_GATE_DELTA_POSITIVE")
        if "native_event_emitter" not in rules:
            codes.append("PRECHECK_NATIVE_RULE_MISSING")
    elif role == "commit":
        if str(event.get("event_type") or "") != _expected_event_type(slot, "commit"):
            codes.append("COMMIT_EVENT_TYPE_MISMATCH")
        if _decision_kind(event) not in STRONG_DECISIONS:
            codes.append("COMMIT_DECISION_NOT_STRONG")
        if _decision_action(event) != str(slot.get("decision_action") or ""):
            codes.append("COMMIT_ACTION_MISMATCH")
        if _finite_number(tension.get("gate_delta")) and float(tension.get("gate_delta")) < 0:
            codes.append("COMMIT_GATE_DELTA_NEGATIVE")
        if _max_authority(_rules(event)) not in HARD_AUTHORITIES:
            codes.append("COMMIT_AUTHORITY_BELOW_H2")
        missing_target_rules = sorted(target_rules - rules)
        if missing_target_rules:
            codes.append("COMMIT_TARGET_RULES_MISSING")
        missing_target_risk_flags = sorted(target_risk_flags - risk_flags)
        if missing_target_risk_flags:
            codes.append("COMMIT_TARGET_RISK_FLAGS_MISSING")
    else:
        if _decision_kind(event) == str(slot.get("decision_kind") or "") and _decision_action(event) != str(slot.get("decision_action") or ""):
            codes.append("COMMIT_ACTION_MISMATCH")
        codes.append("RUNTIME_ROLE_UNKNOWN")
    return codes


def _pair_evidence(prechecks: list[dict[str, Any]], commits: list[dict[str, Any]]) -> dict[str, Any]:
    matching_chain_count = 0
    ordered_pair_count = 0
    shared_chains: set[str] = set()
    exact_cardinality = len(prechecks) == 1 and len(commits) == 1
    for precheck in prechecks:
        precheck_chain = str(precheck.get("causal_chain_id") or "")
        precheck_time = _timestamp_epoch(precheck)
        for commit in commits:
            commit_chain = str(commit.get("causal_chain_id") or "")
            if not precheck_chain or precheck_chain != commit_chain:
                continue
            matching_chain_count += 1
            shared_chains.add(precheck_chain)
            commit_time = _timestamp_epoch(commit)
            if precheck_time is not None and commit_time is not None and commit_time >= precheck_time:
                ordered_pair_count += 1

    if not exact_cardinality and prechecks and commits:
        reason = "NO_TICK_PAIR_CARDINALITY_INVALID"
    elif ordered_pair_count > 0:
        reason = ""
    elif prechecks and commits and not shared_chains:
        reason = "NO_TICK_PAIR_CAUSAL_CHAIN_MISMATCH"
    elif prechecks and commits:
        reason = "NO_TICK_PAIR_ORDER_INVALID"
    else:
        reason = "NO_TICK_PAIR_INCOMPLETE"

    return {
        "valid": exact_cardinality and ordered_pair_count > 0,
        "exact_cardinality": exact_cardinality,
        "matching_chain_count": matching_chain_count,
        "ordered_pair_count": ordered_pair_count,
        "shared_causal_chain_count": len(shared_chains),
        "failure_reason": reason,
    }


def _validate_runtime_events(matrix: dict[str, Any], events: list[dict[str, Any]], bad_lines: list[dict[str, Any]]) -> dict[str, Any]:
    slots = _slot_map(matrix)
    by_slot: dict[str, dict[str, list[dict[str, Any]]]] = {
        original: {"precheck": [], "commit": [], "rejected": []}
        for original in slots
    }
    rejections: list[dict[str, Any]] = list(bad_lines)
    event_type_mix: Counter[str] = Counter()
    action_mix: Counter[str] = Counter()
    rule_mix: Counter[str] = Counter()
    seen_event_lines: dict[str, int] = {}
    seen_proof_hash_lines: dict[str, int] = {}
    seen_proof_ref_lines: dict[str, int] = {}

    for event in events:
        event_id = str(event.get("event_id") or "")
        stream_codes: list[str] = []
        if event_id:
            if event_id in seen_event_lines:
                stream_codes.append("DUPLICATE_EVENT_ID")
            else:
                seen_event_lines[event_id] = int(event.get("_line", 0) or 0)
        proof_hash = str(_proof(event).get("proof_hash") or "")
        if proof_hash:
            if proof_hash in seen_proof_hash_lines:
                stream_codes.append("DUPLICATE_PROOF_HASH")
            else:
                seen_proof_hash_lines[proof_hash] = int(event.get("_line", 0) or 0)
        proof_ref = str(_proof(event).get("proof_ref") or "")
        if proof_ref:
            if proof_ref in seen_proof_ref_lines:
                stream_codes.append("DUPLICATE_PROOF_REF")
            else:
                seen_proof_ref_lines[proof_ref] = int(event.get("_line", 0) or 0)
        original = _original_id(event)
        if original not in slots:
            codes = [*stream_codes, "UNKNOWN_ORIGINAL_EVENT_ID"]
            rejections.append(
                {
                    "line": event.get("_line", 0),
                    "event_id": event.get("event_id"),
                    "code": "UNKNOWN_ORIGINAL_EVENT_ID",
                    "codes": codes,
                    "original_event_id": original,
                }
            )
            continue
        slot = slots[original]
        codes = [*stream_codes, *_event_codes(event, slot)]
        role = _role(event, slot)
        event_type_mix[str(event.get("event_type") or "unknown")] += 1
        action_mix[_decision_action(event)] += 1
        for rule in _rules(event):
            rule_mix[rule] += 1
        if codes:
            rejection = {
                "line": event.get("_line", 0),
                "event_id": event.get("event_id"),
                "original_event_id": original,
                "role": role,
                "codes": codes,
            }
            rejections.append(rejection)
            by_slot[original]["rejected"].append(rejection)
            continue
        by_slot[original][role].append(event)

    slot_rows = []
    accepted_slot_count = 0
    no_tick_pair_integrity_count = 0
    no_tick_pair_failure_count = 0
    for original, slot in slots.items():
        row = by_slot[original]
        precheck_count = len(row["precheck"])
        commit_count = len(row["commit"])
        rejected_count = len(row["rejected"])
        pair = _pair_evidence(row["precheck"], row["commit"])
        no_tick_pair_integrity_count += 1 if pair["valid"] else 0
        no_tick_pair_failure_count += 1 if precheck_count > 0 and commit_count > 0 and not pair["valid"] else 0
        accepted = precheck_count == 1 and commit_count == 1 and rejected_count == 0 and pair["valid"]
        accepted_slot_count += 1 if accepted else 0
        slot_rows.append(
            {
                "slot_id": slot.get("slot_id"),
                "original_event_id": original,
                "entity_id": slot.get("entity_id"),
                "decision_action": slot.get("decision_action"),
                "accepted": accepted,
                "precheck_count": precheck_count,
                "commit_count": commit_count,
                "rejected_count": rejected_count,
                "missing_precheck": precheck_count == 0,
                "missing_commit": commit_count == 0,
                "no_tick_pair_valid": pair["valid"],
                "exact_no_tick_pair_cardinality": pair["exact_cardinality"],
                "matching_causal_chain_pair_count": pair["matching_chain_count"],
                "ordered_no_tick_pair_count": pair["ordered_pair_count"],
                "shared_causal_chain_count": pair["shared_causal_chain_count"],
                "pair_failure_reason": pair["failure_reason"],
            }
        )

    pending_slot_count = len(slots) - accepted_slot_count
    duplicate_event_rejection_count = sum(1 for rejection in rejections if "DUPLICATE_EVENT_ID" in rejection.get("codes", []))
    duplicate_proof_hash_rejection_count = sum(1 for rejection in rejections if "DUPLICATE_PROOF_HASH" in rejection.get("codes", []))
    duplicate_proof_ref_rejection_count = sum(1 for rejection in rejections if "DUPLICATE_PROOF_REF" in rejection.get("codes", []))
    return {
        "runtime_event_count": len(events),
        "bad_json_line_count": len(bad_lines),
        "accepted_slot_count": accepted_slot_count,
        "pending_slot_count": pending_slot_count,
        "slot_failure_count": pending_slot_count,
        "rejected_event_count": len(rejections),
        "duplicate_event_rejection_count": duplicate_event_rejection_count,
        "duplicate_proof_hash_rejection_count": duplicate_proof_hash_rejection_count,
        "duplicate_proof_ref_rejection_count": duplicate_proof_ref_rejection_count,
        "no_tick_pair_integrity_count": no_tick_pair_integrity_count,
        "no_tick_pair_failure_count": no_tick_pair_failure_count,
        "event_type_mix": event_type_mix.most_common(),
        "decision_action_mix": action_mix.most_common(),
        "heuristic_rule_mix": rule_mix.most_common(),
        "slot_rows": slot_rows,
        "rejections": rejections,
    }


def _sample_event(slot: dict[str, Any], *, role: str, control: str = "negative") -> dict[str, Any]:
    action = "NO_ACTION" if role == "precheck" else str(slot.get("decision_action") or "unknown")
    kind = "observe" if role == "precheck" else str(slot.get("decision_kind") or "collapse")
    event_type = f"{slot.get('event_type')}_authority_precheck" if role == "precheck" else str(slot.get("event_type") or "runtime_commit")
    score = 0.0 if role == "precheck" else 1.0
    threshold = 0.5
    event_id = f"evt_{control}_control_{role}_{slot.get('slot_id')}"
    proof_ref = f"runtime:{slot.get('slot_id')}:{role}"
    event = {
        "schema_version": "pnva.event.v1",
        "event_id": event_id,
        "timestamp": "2026-05-05T00:00:00Z",
        "entity_id": slot.get("entity_id"),
        "entity_type": slot.get("entity_type"),
        "causal_chain_id": f"chain_{control}_control_{slot.get('slot_id')}",
        "event_type": event_type,
        "field": {
            "state_before": "observed",
            "state_after": "suppressed" if role == "precheck" else "committed",
            "phi": score,
            "gradient": 0.0 if role == "precheck" else 1.0,
        },
        "decision": {
            "kind": kind,
            "action": action,
            "reason": "native_authority_precheck_no_tick" if role == "precheck" else "native_runtime_commit",
        },
        "heuristics": {
            "rules": list(slot.get("target_rules") or ["native_event_emitter", "adaptive_threshold", "field_scheduler"]),
            "risk_flags": list(slot.get("risk_flags") or []),
        },
        "tension": {
            "score": score,
            "threshold": threshold,
            "gate_delta": round(score - threshold, 6),
            "components": {
                "original_event_id": slot.get("original_event_id"),
                "r3_runtime_slot_id": slot.get("slot_id"),
            },
        },
        "proof": {
            "valid": True,
            "native": True,
            "projection": False,
            "proof_hash": "",
            "proof_ref": proof_ref,
        },
        "source": {
            "format": "native_pnva_event_v1",
            "sanitized": True,
        },
    }
    event["proof"]["proof_hash"] = _expected_proof_hash(event)
    return event


def _negative_controls(matrix: dict[str, Any]) -> dict[str, Any]:
    slots = list(_slot_map(matrix).values())
    if not slots:
        return {
            "negative_control_count": 0,
            "detected_count": 0,
            "pass": False,
            "controls": [],
        }
    slot = slots[0]
    controls = []

    def run_control(name: str, role: str, mutate: Any, expected_code: str) -> None:
        event = _sample_event(slot, role=role)
        mutate(event)
        codes = _event_codes(event, slot)
        detected = expected_code in codes
        controls.append(
            {
                "name": name,
                "expected_detection": expected_code,
                "detected": detected,
                "codes": codes,
            }
        )

    def run_stream_control(name: str, events: list[dict[str, Any]], expected_code: str) -> None:
        runtime = _validate_runtime_events(matrix, events, [])
        codes: list[str] = []
        for rejection in runtime["rejections"]:
            codes.extend(str(code) for code in rejection.get("codes", []) if str(code))
            if rejection.get("code"):
                codes.append(str(rejection["code"]))
        for row in runtime["slot_rows"]:
            if row.get("pair_failure_reason"):
                codes.append(str(row["pair_failure_reason"]))
        detected = expected_code in set(codes)
        controls.append(
            {
                "name": name,
                "expected_detection": expected_code,
                "detected": detected,
                "codes": sorted(set(codes)),
            }
        )

    def rebind_proof_hash(event: dict[str, Any]) -> None:
        event["proof"]["proof_hash"] = _expected_proof_hash(event)

    run_control("reject_projection_true", "commit", lambda event: event["proof"].update({"projection": True}), "PROJECTED_PROOF_FORBIDDEN")
    run_control("reject_missing_timestamp", "commit", lambda event: event.pop("timestamp", None), "MISSING_TIMESTAMP")
    run_control("reject_invalid_timestamp", "commit", lambda event: event.update({"timestamp": "not-a-valid-iso8601-timestamp"}), "TIMESTAMP_INVALID")
    run_control("reject_missing_field_state", "commit", lambda event: event.pop("field", None), "FIELD_STATE_INVALID")
    run_control("reject_missing_gate_delta", "commit", lambda event: event["tension"].pop("gate_delta", None), "TENSION_GATE_DELTA_INVALID")
    run_control("reject_gate_delta_inconsistent", "commit", lambda event: event["tension"].update({"gate_delta": 9.99}), "TENSION_GATE_DELTA_INCONSISTENT")
    run_control("reject_nonfinite_tension_score", "commit", lambda event: event["tension"].update({"score": float("nan")}), "TENSION_SCORE_INVALID")
    run_control("reject_nonfinite_tension_threshold", "commit", lambda event: event["tension"].update({"threshold": float("inf")}), "TENSION_THRESHOLD_INVALID")
    run_control("reject_missing_entity", "commit", lambda event: event.pop("entity_id", None), "MISSING_ENTITY_ID")
    run_control("reject_entity_mismatch", "commit", lambda event: event.update({"entity_id": "entity_wrong"}), "ENTITY_MISMATCH")
    run_control("reject_missing_entity_type", "commit", lambda event: event.pop("entity_type", None), "MISSING_ENTITY_TYPE")
    run_control("reject_entity_type_mismatch", "commit", lambda event: event.update({"entity_type": "entity_type_wrong"}), "ENTITY_TYPE_MISMATCH")
    run_control("reject_missing_chain", "commit", lambda event: event.pop("causal_chain_id", None), "MISSING_CAUSAL_CHAIN_ID")
    run_control("reject_missing_hash", "commit", lambda event: event["proof"].pop("proof_hash", None), "PROOF_HASH_OR_VALIDITY_INVALID")
    run_control("reject_invalid_proof_hash_format", "commit", lambda event: event["proof"].update({"proof_hash": "sha256:not-64-hex"}), "PROOF_HASH_FORMAT_INVALID")
    run_control("reject_proof_hash_binding_tamper", "commit", lambda event: event["field"].update({"state_after": "tampered_after_hash"}), "PROOF_HASH_BINDING_INVALID")
    run_control("reject_proof_ref_role_mismatch", "commit", lambda event: event["proof"].update({"proof_ref": f"runtime:{slot.get('slot_id')}:precheck"}), "PROOF_REF_ROLE_MISMATCH")
    run_control("reject_low_authority_commit", "commit", lambda event: event["heuristics"].update({"rules": ["legacy_observer"]}), "COMMIT_AUTHORITY_BELOW_H2")
    run_control("reject_missing_target_rules", "commit", lambda event: event["heuristics"].update({"rules": ["native_event_emitter"]}), "COMMIT_TARGET_RULES_MISSING")
    run_control("reject_unknown_heuristic_rule", "commit", lambda event: event["heuristics"].update({"rules": list(slot.get("target_rules") or []) + ["unknown_rule"]}), "HEURISTIC_RULE_UNKNOWN")
    run_control("reject_duplicate_heuristic_rule", "commit", lambda event: event["heuristics"].update({"rules": list(slot.get("target_rules") or []) + [str((slot.get("target_rules") or ["native_event_emitter"])[0])]}), "HEURISTIC_RULE_DUPLICATE")
    run_control("reject_invalid_risk_flags", "commit", lambda event: event["heuristics"].update({"risk_flags": "not-a-list"}), "RISK_FLAGS_INVALID")
    run_control("reject_duplicate_risk_flag", "commit", lambda event: event["heuristics"].update({"risk_flags": list(slot.get("risk_flags") or []) + [str((slot.get("risk_flags") or ["RESIZE_BATCH_PRESSURE"])[0])]}), "RISK_FLAG_DUPLICATE")
    run_control("reject_unknown_risk_flag", "commit", lambda event: event["heuristics"].update({"risk_flags": list(slot.get("risk_flags") or []) + ["UNKNOWN_RISK_FLAG"]}), "RISK_FLAG_UNKNOWN")
    run_control("reject_missing_target_risk_flags", "commit", lambda event: event["heuristics"].update({"risk_flags": []}), "COMMIT_TARGET_RISK_FLAGS_MISSING")
    run_control("reject_wrong_action", "commit", lambda event: event["decision"].update({"action": "WRONG_ACTION"}), "COMMIT_ACTION_MISMATCH")
    run_control("reject_precheck_event_type_mismatch", "precheck", lambda event: event.update({"event_type": "wrong_precheck_event_type"}), "PRECHECK_EVENT_TYPE_MISMATCH")
    run_control("reject_commit_event_type_mismatch", "commit", lambda event: event.update({"event_type": "wrong_commit_event_type"}), "COMMIT_EVENT_TYPE_MISMATCH")
    run_control("reject_precheck_execution_action", "precheck", lambda event: event["decision"].update({"action": slot.get("decision_action")}), "PRECHECK_ACTION_INVALID")
    run_control("reject_precheck_positive_gate_delta", "precheck", lambda event: event["tension"].update({"score": 1.0, "threshold": 0.5, "gate_delta": 0.5}), "PRECHECK_GATE_DELTA_POSITIVE")
    run_control("reject_commit_negative_gate_delta", "commit", lambda event: event["tension"].update({"score": 0.0, "threshold": 0.5, "gate_delta": -0.5}), "COMMIT_GATE_DELTA_NEGATIVE")
    run_control("reject_missing_slot_id", "commit", lambda event: event["tension"]["components"].pop("r3_runtime_slot_id", None), "MISSING_R3_RUNTIME_SLOT_ID")
    run_control("reject_slot_id_mismatch", "commit", lambda event: event["tension"]["components"].update({"r3_runtime_slot_id": "r3-runtime-slot-wrong"}), "R3_RUNTIME_SLOT_MISMATCH")
    run_control("reject_original_event_mismatch", "commit", lambda event: event["tension"]["components"].update({"original_event_id": "evt_wrong"}), "ORIGINAL_EVENT_MISMATCH")
    run_control("reject_missing_native_proof", "commit", lambda event: event["proof"].pop("native", None), "PROOF_NATIVE_REQUIRED")
    run_control("reject_invalid_source_format", "commit", lambda event: event["source"].update({"format": "legacy_bridge"}), "SOURCE_FORMAT_INVALID")
    run_control("reject_unsanitized_source", "commit", lambda event: event["source"].update({"sanitized": False}), "SOURCE_SANITIZED_REQUIRED")

    duplicate_precheck = _sample_event(slot, role="precheck", control="duplicate")
    duplicate_commit = _sample_event(slot, role="commit", control="duplicate")
    duplicate_commit["event_id"] = duplicate_precheck["event_id"]
    run_stream_control("reject_duplicate_event_id", [duplicate_precheck, duplicate_commit], "DUPLICATE_EVENT_ID")

    duplicate_hash_precheck = _sample_event(slot, role="precheck", control="duplicate_hash")
    duplicate_hash_commit = _sample_event(slot, role="commit", control="duplicate_hash")
    duplicate_hash_commit["proof"]["proof_hash"] = duplicate_hash_precheck["proof"]["proof_hash"]
    run_stream_control("reject_duplicate_proof_hash", [duplicate_hash_precheck, duplicate_hash_commit], "DUPLICATE_PROOF_HASH")

    duplicate_ref_precheck = _sample_event(slot, role="precheck", control="duplicate_ref")
    duplicate_ref_commit = _sample_event(slot, role="commit", control="duplicate_ref")
    duplicate_ref_commit["proof"]["proof_ref"] = duplicate_ref_precheck["proof"]["proof_ref"]
    run_stream_control("reject_duplicate_proof_ref", [duplicate_ref_precheck, duplicate_ref_commit], "DUPLICATE_PROOF_REF")

    chain_precheck = _sample_event(slot, role="precheck", control="chain")
    chain_commit = _sample_event(slot, role="commit", control="chain")
    chain_commit["causal_chain_id"] = "chain_wrong_for_pair"
    rebind_proof_hash(chain_commit)
    run_stream_control("reject_no_tick_pair_chain_mismatch", [chain_precheck, chain_commit], "NO_TICK_PAIR_CAUSAL_CHAIN_MISMATCH")

    order_precheck = _sample_event(slot, role="precheck", control="order")
    order_commit = _sample_event(slot, role="commit", control="order")
    order_precheck["timestamp"] = "2026-05-05T00:00:02Z"
    order_commit["timestamp"] = "2026-05-05T00:00:01Z"
    rebind_proof_hash(order_precheck)
    rebind_proof_hash(order_commit)
    run_stream_control("reject_commit_before_precheck", [order_precheck, order_commit], "NO_TICK_PAIR_ORDER_INVALID")

    detected_count = sum(1 for item in controls if item["detected"])
    return {
        "negative_control_count": len(controls),
        "detected_count": detected_count,
        "pass": detected_count == len(controls),
        "controls": controls,
    }


def _positive_controls(matrix: dict[str, Any]) -> dict[str, Any]:
    slots_by_action: dict[str, dict[str, Any]] = {}
    for slot in _slot_map(matrix).values():
        action = str(slot.get("decision_action") or "unknown")
        slots_by_action.setdefault(action, slot)

    controls: list[dict[str, Any]] = []
    for action, slot in sorted(slots_by_action.items()):
        for role in ("precheck", "commit"):
            event = _sample_event(slot, role=role, control="positive")
            codes = _event_codes(event, slot)
            detected_role = _role(event, slot)
            accepted = not codes and detected_role == role
            controls.append(
                {
                    "name": f"accept_{action.lower()}_{role}",
                    "expected_role": role,
                    "detected_role": detected_role,
                    "accepted": accepted,
                    "codes": codes,
                }
            )

    passed_count = sum(1 for item in controls if item["accepted"])
    return {
        "positive_control_count": len(controls),
        "passed_count": passed_count,
        "pass": bool(controls) and passed_count == len(controls),
        "controls": controls,
        "fixture_only": True,
        "runtime_evidence": False,
    }


def build_report(repo: Path, runtime_events_path: Path | None = None) -> dict[str, Any]:
    repo = repo.resolve()
    matrix_path = repo / R3_RUNTIME_CAPTURE_MATRIX
    matrix = _read_json(matrix_path)
    slots = _slot_map(matrix)
    runtime_events: list[dict[str, Any]] = []
    bad_lines: list[dict[str, Any]] = []
    if runtime_events_path:
        runtime_events, bad_lines = _load_jsonl(runtime_events_path)

    runtime = _validate_runtime_events(matrix, runtime_events, bad_lines)
    negative = _negative_controls(matrix)
    positive = _positive_controls(matrix)
    guard_ready = (
        matrix.get("pass") is True
        and matrix.get("classification") == "R3_RUNTIME_CAPTURE_MATRIX_READY_PENDING_RUNTIME"
        and matrix.get("capture_contract_ready") is True
        and int(matrix.get("capture_slot_count", 0)) == len(slots)
        and int(matrix.get("required_runtime_event_count", 0)) == len(slots) * 2
        and negative["pass"] is True
        and positive["pass"] is True
    )
    runtime_present = runtime_events_path is not None
    runtime_complete = (
        runtime_present
        and runtime["accepted_slot_count"] == len(slots)
        and runtime["rejected_event_count"] == 0
        and runtime["runtime_event_count"] == len(slots) * 2
    )

    if not guard_ready:
        classification = "R3_RUNTIME_EVIDENCE_GUARD_FAIL"
    elif runtime_complete:
        classification = "R3_RUNTIME_EVIDENCE_ACCEPTED"
    elif runtime_present:
        classification = "R3_RUNTIME_EVIDENCE_REJECTED"
    else:
        classification = "R3_RUNTIME_EVIDENCE_GUARD_READY_AWAITING_CAPTURE"

    report = {
        "schema_version": "pnva.r3_runtime_evidence_guard.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": guard_ready if not runtime_present else runtime_complete,
        "intake_guard_ready": guard_ready,
        "runtime_evidence_present": runtime_present,
        "runtime_evidence_approved": runtime_complete,
        "runtime_acceptance_complete": runtime_complete,
        "matrix_classification": matrix.get("classification"),
        "capture_slot_count": len(slots),
        "required_runtime_event_count": len(slots) * 2,
        "required_no_tick_precheck_count": len(slots),
        "required_collapse_commit_count": len(slots),
        "runtime_event_count": runtime["runtime_event_count"],
        "accepted_slot_count": runtime["accepted_slot_count"],
        "pending_slot_count": runtime["pending_slot_count"],
        "slot_failure_count": runtime["slot_failure_count"],
        "rejected_event_count": runtime["rejected_event_count"],
        "bad_json_line_count": runtime["bad_json_line_count"],
        "duplicate_event_rejection_count": runtime["duplicate_event_rejection_count"],
        "duplicate_proof_hash_rejection_count": runtime["duplicate_proof_hash_rejection_count"],
        "duplicate_proof_ref_rejection_count": runtime["duplicate_proof_ref_rejection_count"],
        "no_tick_pair_integrity_count": runtime["no_tick_pair_integrity_count"],
        "no_tick_pair_failure_count": runtime["no_tick_pair_failure_count"],
        "negative_control_count": negative["negative_control_count"],
        "negative_control_detected_count": negative["detected_count"],
        "negative_controls_pass": negative["pass"],
        "positive_control_count": positive["positive_control_count"],
        "positive_control_passed_count": positive["passed_count"],
        "positive_controls_pass": positive["pass"],
        "positive_controls_fixture_only": True,
        "enforced_controls": {
            "schema_version_required": "pnva.event.v1",
            "timestamp_required": True,
            "timestamp_iso8601_required": True,
            "duplicate_event_id_forbidden": True,
            "field_state_required": True,
            "event_type_must_match_slot": True,
            "entity_id_required": True,
            "entity_type_required": True,
            "entity_type_must_match_slot": True,
            "causal_chain_id_required": True,
            "tension_gate_delta_required": True,
            "tension_gate_delta_consistency_required": True,
            "precheck_gate_delta_nonpositive_required": True,
            "commit_gate_delta_nonnegative_required": True,
            "proof_hash_required": True,
            "proof_hash_sha256_format_required": True,
            "proof_hash_binds_event_identity": True,
            "proof_hash_unique_required": True,
            "proof_ref_unique_required": True,
            "proof_ref_runtime_slot_role_required": True,
            "proof_native_required": True,
            "proof_projection_forbidden": True,
            "source_format_required": "native_pnva_event_v1",
            "source_sanitized_required": True,
            "r3_runtime_slot_id_required": True,
            "commit_min_authority": "H2",
            "precheck_must_be_no_tick": True,
            "no_tick_pair_causal_chain_required": True,
            "no_tick_pair_commit_after_precheck_required": True,
            "no_tick_pair_exactly_one_precheck_commit_required": True,
            "runtime_event_count_exact_required": True,
            "commit_must_match_slot_action": True,
            "target_rules_required_on_commit": True,
            "heuristic_rules_known_required": True,
            "heuristic_rules_unique_required": True,
            "risk_flags_list_required": True,
            "risk_flags_known_required": True,
            "risk_flags_unique_required": True,
            "target_risk_flags_required_on_commit": True,
        },
        "runtime_mix": {
            "event_type_mix": runtime["event_type_mix"],
            "decision_action_mix": runtime["decision_action_mix"],
            "heuristic_rule_mix": runtime["heuristic_rule_mix"],
        },
        "slot_rows": runtime["slot_rows"],
        "rejections": runtime["rejections"],
        "negative_controls": negative["controls"],
        "positive_controls": positive["controls"],
        "reports_checked": {
            "r3_runtime_capture_matrix": R3_RUNTIME_CAPTURE_MATRIX,
            "runtime_events": str(runtime_events_path) if runtime_events_path else "",
        },
        "summary": {
            "intake_guard_ready": guard_ready,
            "runtime_evidence_present": runtime_present,
            "runtime_evidence_approved": runtime_complete,
            "capture_slot_count": len(slots),
            "required_runtime_event_count": len(slots) * 2,
            "accepted_slot_count": runtime["accepted_slot_count"],
            "pending_slot_count": runtime["pending_slot_count"],
            "rejected_event_count": runtime["rejected_event_count"],
            "duplicate_event_rejection_count": runtime["duplicate_event_rejection_count"],
            "duplicate_proof_hash_rejection_count": runtime["duplicate_proof_hash_rejection_count"],
            "duplicate_proof_ref_rejection_count": runtime["duplicate_proof_ref_rejection_count"],
            "no_tick_pair_integrity_count": runtime["no_tick_pair_integrity_count"],
            "no_tick_pair_failure_count": runtime["no_tick_pair_failure_count"],
            "negative_control_detected_count": negative["detected_count"],
            "negative_control_count": negative["negative_control_count"],
            "positive_control_passed_count": positive["passed_count"],
            "positive_control_count": positive["positive_control_count"],
        },
        "interpretation": {
            "purpose": "Protect the R3 runtime intake boundary before fresh events are accepted as legacy-free evidence.",
            "sovereignty": "PNVA becomes harder to fake when projected proofs, malformed, duplicated or content-unbound proof hashes, wrong proof-ref slot roles, wrong event types, malformed or inconsistent tension values, invalid gate signs, duplicate events, entity or slot mismatches, unsanitized sources, unknown heuristic rules, invalid risk flags, weak authority, missing target rules, missing target risk flags, extra runtime events and causally broken no-tick pairs are rejected before cutover.",
            "boundary": "Without a runtime-events file this guard certifies the intake contract only; it does not claim final runtime completion.",
        },
        "recommendations": [
            "Feed fresh runtime JSONL through this guard before rerunning R3 cutover approval.",
            "Reject any event with proof.projection=true in final runtime evidence.",
            "Reject any event with non-finite tension values, entity mismatch, slot mismatch or original-event mismatch.",
            "Require every slot to contain exactly one native no-tick precheck and exactly one H2+ commit in the same causal_chain_id, with commit timestamp at or after precheck timestamp.",
            "Require the runtime event count to equal the declared R3 requirement instead of allowing extra events.",
            "Require precheck and commit event_type values to match the capture slot contract.",
            "Reject duplicate event_id, proof_hash and proof_ref values before accepting runtime coverage.",
            "Reject runtime events whose proof_hash does not bind to the canonical event identity payload.",
            "Require proof_ref to match runtime:<slot-id>:precheck or runtime:<slot-id>:commit.",
            "Require gate_delta to equal score minus threshold, with nonpositive prechecks and nonnegative commits.",
            "Reject unknown or duplicated heuristic rules before accepting runtime coverage.",
            "Reject malformed, unknown, duplicated or missing target risk flags before accepting runtime coverage.",
            "Keep entity_id, causal_chain_id, source.sanitized and proof_hash mandatory for every runtime event.",
        ],
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate PNVA R3 runtime evidence intake before cutover.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--runtime-events", default="")
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    runtime_events = Path(args.runtime_events).resolve() if args.runtime_events else None
    report = build_report(repo, runtime_events)
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
