#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

CANONICAL_EVENTS = "reports/pnva-canonical-events-sample-2026-05-05.jsonl"
AUTHORITY_LEDGER = "reports/pnva-authority-migration-ledger-2026-05-05.json"
R3_PROJECTION_SUMMARY = "reports/pnva-r3-authority-projection-summary-2026-05-05.json"
R3_PROJECTION_EVENTS = "reports/pnva-r3-authority-projection-events-2026-05-05.jsonl"
R3_PROJECTION_NO_TICK = "reports/pnva-r3-authority-projection-no-tick-2026-05-05.json"
R3_CUTOVER_GATE = "reports/pnva-r3-cutover-gate-2026-05-05.json"

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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _public_path(repo: Path, path: Path | None) -> str:
    if path is None:
        return ""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(repo))
    except ValueError:
        return resolved.name


def _load_jsonl(path: Path, scope: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError(f"{scope}:{line_no}: event is not an object")
            event["_line"] = line_no
            event["_scope"] = scope
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


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


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


def _proof_ok(event: dict[str, Any]) -> bool:
    proof = event.get("proof")
    if not isinstance(proof, dict):
        return False
    return (
        proof.get("valid") is True
        and str(proof.get("proof_hash") or "").startswith("sha256:")
        and bool(proof.get("proof_ref"))
    )


def _field(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("field")
    return value if isinstance(value, dict) else {}


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    value = event.get("tension")
    return value if isinstance(value, dict) else {}


def _components(event: dict[str, Any]) -> dict[str, Any]:
    value = _tension(event).get("components")
    return value if isinstance(value, dict) else {}


def _source_file(event: dict[str, Any]) -> str:
    source = event.get("source")
    if not isinstance(source, dict):
        return ""
    return str(source.get("file_name") or "")


def _is_low_authority_strong(event: dict[str, Any]) -> bool:
    return _decision_kind(event) in STRONG_DECISIONS and _max_authority(_rules(event)) not in HARD_AUTHORITIES


def _target_rules(event: dict[str, Any]) -> list[str]:
    action = _decision_action(event)
    flags = set(_risk_flags(event))
    if action == "COOLDOWN_GPU" or any("THERMAL" in flag or "COOLDOWN" in flag for flag in flags):
        return ["native_event_emitter", "power_orchestrator", "field_scheduler", "adaptive_threshold"]
    if str(event.get("event_type") or "").upper().startswith("ETEV_GUARD"):
        return ["native_event_emitter", "etev_guard", "adaptive_threshold", "field_scheduler"]
    return ["native_event_emitter", "adaptive_threshold", "field_scheduler"]


def _original_id(projected: dict[str, Any]) -> str:
    return str(_components(projected).get("original_event_id") or "")


def _projection_role(projected: dict[str, Any]) -> str:
    event_type = str(projected.get("event_type") or "")
    reason = str(_decision(projected).get("reason") or "")
    if "precheck" in event_type or "precheck" in reason:
        return "precheck"
    return "commit"


def _projection_pairs(events: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    pairs: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for event in events:
        original = _original_id(event)
        if not original:
            continue
        pairs[original][_projection_role(event)] = event
    return dict(pairs)


def _runtime_pairs(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_original: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        original = _original_id(event)
        if original:
            by_original[original].append(event)
    return dict(by_original)


def _runtime_slot_status(original_id: str, runtime_by_original: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    observed = runtime_by_original.get(original_id, [])
    non_projected = []
    for event in observed:
        proof = event.get("proof") if isinstance(event.get("proof"), dict) else {}
        if proof.get("projection") is not True:
            non_projected.append(event)
    precheck = [
        event
        for event in non_projected
        if _projection_role(event) == "precheck" or _decision_kind(event) in {"observe", "block"}
    ]
    commit = [
        event
        for event in non_projected
        if _projection_role(event) == "commit" and _decision_kind(event) in STRONG_DECISIONS
    ]
    proof_clean = all(_proof_ok(event) for event in non_projected)
    hard_authority = all(_max_authority(_rules(event)) in HARD_AUTHORITIES for event in commit)
    verified = bool(precheck) and bool(commit) and proof_clean and hard_authority
    return {
        "verified": verified,
        "observed_runtime_event_count": len(observed),
        "non_projected_runtime_event_count": len(non_projected),
        "runtime_precheck_count": len(precheck),
        "runtime_commit_count": len(commit),
        "runtime_proof_clean": proof_clean if non_projected else False,
        "runtime_hard_authority": hard_authority if commit else False,
    }


def build_report(repo: Path, runtime_events_path: Path | None = None) -> dict[str, Any]:
    repo = repo.resolve()
    canonical_events = _load_jsonl(repo / CANONICAL_EVENTS, "canonical")
    projection_events = _load_jsonl(repo / R3_PROJECTION_EVENTS, "r3_projection")
    runtime_events = _load_jsonl(runtime_events_path, "runtime") if runtime_events_path else []
    ledger = _read_json(repo / AUTHORITY_LEDGER)
    projection_summary = _read_json(repo / R3_PROJECTION_SUMMARY)
    projection_no_tick = _read_json(repo / R3_PROJECTION_NO_TICK)
    cutover = _read_json(repo / R3_CUTOVER_GATE)

    candidates = [event for event in canonical_events if _is_low_authority_strong(event)]
    projections = _projection_pairs(projection_events)
    runtime_by_original = _runtime_pairs(runtime_events)

    slots: list[dict[str, Any]] = []
    entity_rows: dict[str, dict[str, Any]] = {}
    action_rows: dict[tuple[str, str], dict[str, Any]] = {}
    target_rule_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    projection_pair_count = 0
    projected_precheck_count = 0
    projected_commit_count = 0
    verified_runtime_slot_count = 0

    for index, event in enumerate(candidates, 1):
        original_id = str(event.get("event_id") or "")
        target_rules = _target_rules(event)
        target_max_authority = _max_authority(target_rules)
        pair = projections.get(original_id, {})
        projected_precheck = pair.get("precheck")
        projected_commit = pair.get("commit")
        has_pair = bool(projected_precheck and projected_commit)
        projection_pair_count += 1 if has_pair else 0
        projected_precheck_count += 1 if projected_precheck else 0
        projected_commit_count += 1 if projected_commit else 0
        runtime_status = _runtime_slot_status(original_id, runtime_by_original)
        verified_runtime_slot_count += 1 if runtime_status["verified"] else 0
        entity_id = str(event.get("entity_id") or "unknown")
        action = _decision_action(event)
        risk_flags = _risk_flags(event)

        for rule in target_rules:
            target_rule_counter[rule] += 1
        for flag in risk_flags:
            risk_counter[flag] += 1

        entity_row = entity_rows.setdefault(
            entity_id,
            {
                "entity_id": entity_id,
                "entity_type": str(event.get("entity_type") or "unknown"),
                "required_slot_count": 0,
                "verified_runtime_slot_count": 0,
                "pending_slot_count": 0,
                "actions": Counter(),
                "target_rules": Counter(),
                "risk_flags": Counter(),
            },
        )
        entity_row["required_slot_count"] += 1
        entity_row["verified_runtime_slot_count"] += 1 if runtime_status["verified"] else 0
        entity_row["pending_slot_count"] += 0 if runtime_status["verified"] else 1
        entity_row["actions"][action] += 1
        for rule in target_rules:
            entity_row["target_rules"][rule] += 1
        for flag in risk_flags:
            entity_row["risk_flags"][flag] += 1

        action_key = (entity_id, action)
        action_row = action_rows.setdefault(
            action_key,
            {
                "entity_id": entity_id,
                "decision_action": action,
                "required_slot_count": 0,
                "verified_runtime_slot_count": 0,
                "pending_slot_count": 0,
                "target_rules": Counter(),
                "risk_flags": Counter(),
                "required_no_tick_prechecks": 0,
                "required_collapse_commits": 0,
            },
        )
        action_row["required_slot_count"] += 1
        action_row["verified_runtime_slot_count"] += 1 if runtime_status["verified"] else 0
        action_row["pending_slot_count"] += 0 if runtime_status["verified"] else 1
        action_row["required_no_tick_prechecks"] += 1
        action_row["required_collapse_commits"] += 1
        for rule in target_rules:
            action_row["target_rules"][rule] += 1
        for flag in risk_flags:
            action_row["risk_flags"][flag] += 1

        slots.append(
            {
                "slot_id": f"r3-runtime-slot-{index:03d}",
                "status": "verified_runtime" if runtime_status["verified"] else "pending_runtime",
                "original_event_id": original_id,
                "original_line": int(event.get("_line", 0)),
                "entity_id": entity_id,
                "entity_type": str(event.get("entity_type") or "unknown"),
                "event_type": str(event.get("event_type") or "unknown"),
                "decision_kind": _decision_kind(event),
                "decision_action": action,
                "source_file": _source_file(event),
                "current_rules": _rules(event),
                "current_max_authority": _max_authority(_rules(event)),
                "target_rules": target_rules,
                "target_max_authority": target_max_authority,
                "risk_flags": risk_flags,
                "score": _safe_float(_tension(event).get("score")),
                "threshold": _safe_float(_tension(event).get("threshold")),
                "gate_delta": _safe_float(_tension(event).get("gate_delta")),
                "proof_valid": _proof_ok(event),
                "projected_precheck_event_id": projected_precheck.get("event_id") if projected_precheck else None,
                "projected_commit_event_id": projected_commit.get("event_id") if projected_commit else None,
                "projection_pair_ready": has_pair,
                "required_runtime_precheck": {
                    "event_type": f"{event.get('event_type')}_authority_precheck",
                    "decision_kind": "observe",
                    "decision_action": "NO_ACTION",
                    "required_reason": "native_authority_precheck_no_tick",
                    "proof_projection_allowed": False,
                },
                "required_runtime_commit": {
                    "event_type": str(event.get("event_type") or "unknown"),
                    "decision_kind": _decision_kind(event),
                    "decision_action": action,
                    "min_authority": "H2",
                    "proof_projection_allowed": False,
                },
                "runtime_status": runtime_status,
            }
        )

    pending_slot_count = len(slots) - verified_runtime_slot_count
    projection_pair_coverage = _ratio(projection_pair_count, len(slots))
    runtime_coverage = _ratio(verified_runtime_slot_count, len(slots))
    contract_ready = (
        ledger.get("pass") is True
        and projection_summary.get("pass") is True
        and cutover.get("contract_ready") is True
        and int(ledger.get("candidate_event_count", 0)) == len(slots)
        and int(projection_summary.get("projected_commit_count", 0)) == len(slots)
        and int(projection_summary.get("projected_precheck_count", 0)) == len(slots)
        and projection_pair_count == len(slots)
    )
    runtime_complete = verified_runtime_slot_count == len(slots) and len(slots) > 0
    classification = "R3_RUNTIME_CAPTURE_MATRIX_FAIL"
    if contract_ready and runtime_complete:
        classification = "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE"
    elif contract_ready:
        classification = "R3_RUNTIME_CAPTURE_MATRIX_READY_PENDING_RUNTIME"
    boundary = (
        "This matrix now confirms the slot-bound native runtime sample: all capture slots are verified, pending runtime replacements are zero and the final cutover may rely on downstream guard approval."
        if runtime_complete
        else "This matrix approves the capture contract, not the final runtime cutover. Pending slots must be replaced by fresh native runtime evidence before R3 legacy-free can be claimed."
    )
    recommendations = [
        "Keep each runtime slot emitted as one no-tick precheck and one native commit without proof.projection=true.",
        "Keep adaptive_threshold, field_scheduler and native_event_emitter on every replacement commit.",
        "Use power_orchestrator on cooldown and thermal-pressure replacement slots.",
    ]
    if runtime_complete:
        recommendations.append("Keep replay, policy, no-tick, proof-chain and cutover validators in the release loop so future captures cannot drift.")
    else:
        recommendations.append("Run replay, policy and no-tick validation over the fresh runtime capture sample before changing the cutover gate.")

    entity_row_output = []
    for row in entity_rows.values():
        entity_row_output.append(
            {
                "entity_id": row["entity_id"],
                "entity_type": row["entity_type"],
                "required_slot_count": row["required_slot_count"],
                "verified_runtime_slot_count": row["verified_runtime_slot_count"],
                "pending_slot_count": row["pending_slot_count"],
                "runtime_coverage_ratio": _ratio(row["verified_runtime_slot_count"], row["required_slot_count"]),
                "actions": row["actions"].most_common(),
                "target_rules": row["target_rules"].most_common(),
                "risk_flags": row["risk_flags"].most_common(),
            }
        )

    action_row_output = []
    for row in action_rows.values():
        action_row_output.append(
            {
                "entity_id": row["entity_id"],
                "decision_action": row["decision_action"],
                "required_slot_count": row["required_slot_count"],
                "verified_runtime_slot_count": row["verified_runtime_slot_count"],
                "pending_slot_count": row["pending_slot_count"],
                "runtime_coverage_ratio": _ratio(row["verified_runtime_slot_count"], row["required_slot_count"]),
                "required_no_tick_prechecks": row["required_no_tick_prechecks"],
                "required_collapse_commits": row["required_collapse_commits"],
                "target_rules": row["target_rules"].most_common(),
                "risk_flags": row["risk_flags"].most_common(),
            }
        )

    return {
        "schema_version": "pnva.r3_runtime_capture_matrix.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": contract_ready,
        "capture_contract_ready": contract_ready,
        "runtime_capture_complete": runtime_complete,
        "runtime_capture_present": bool(runtime_events),
        "runtime_capture_approved": runtime_complete,
        "source_candidate_count": len(slots),
        "ledger_candidate_count": int(ledger.get("candidate_event_count", 0)),
        "cutover_remaining_runtime_replacement_count": int(cutover.get("remaining_runtime_replacement_count", 0)),
        "capture_slot_count": len(slots),
        "verified_runtime_slot_count": verified_runtime_slot_count,
        "pending_slot_count": pending_slot_count,
        "runtime_capture_coverage_ratio": runtime_coverage,
        "required_runtime_event_count": len(slots) * 2,
        "required_no_tick_precheck_count": len(slots),
        "required_collapse_commit_count": len(slots),
        "projection_pair_count": projection_pair_count,
        "projection_pair_coverage_ratio": projection_pair_coverage,
        "projected_precheck_count": projected_precheck_count,
        "projected_commit_count": projected_commit_count,
        "projected_no_tick_suppression_count": int(projection_summary.get("projected_no_tick_suppression_count", 0)),
        "projected_no_tick_suppression_ratio": float(projection_summary.get("projected_no_tick_suppression_ratio", 0.0)),
        "projection_no_tick_classification": projection_no_tick.get("classification"),
        "entity_target_count": len(entity_rows),
        "action_target_count": len(action_rows),
        "target_rule_count": len(target_rule_counter),
        "target_rule_mix": target_rule_counter.most_common(),
        "risk_flag_mix": risk_counter.most_common(),
        "entity_rows": sorted(entity_row_output, key=lambda row: (-row["required_slot_count"], row["entity_id"])),
        "action_rows": sorted(action_row_output, key=lambda row: (-row["required_slot_count"], row["entity_id"], row["decision_action"])),
        "capture_slots": slots,
        "acceptance_contract": {
            "event_schema": "pnva.event.v1",
            "entity_schema": "pnva.entity_catalog.v1",
            "minimum_authority_for_commit": "H2",
            "required_pair_per_slot": ["native no-tick precheck", "native collapse commit"],
            "forbidden_final_runtime_fields": ["proof.projection=true", "legacy_observer as max authority", "missing entity_id", "missing causal_chain_id", "missing proof_hash"],
            "required_validators": ["replay", "sovereign_policy", "no_tick_invariants", "proof_chain", "semantic_consistency", "reproducibility"],
        },
        "reports_checked": {
            "canonical_events": CANONICAL_EVENTS,
            "authority_ledger": AUTHORITY_LEDGER,
            "r3_projection_summary": R3_PROJECTION_SUMMARY,
            "r3_projection_events": R3_PROJECTION_EVENTS,
            "r3_projection_no_tick": R3_PROJECTION_NO_TICK,
            "r3_cutover_gate": R3_CUTOVER_GATE,
            "runtime_events": _public_path(repo, runtime_events_path),
        },
        "summary": {
            "capture_contract_ready": contract_ready,
            "runtime_capture_complete": runtime_complete,
            "source_candidate_count": len(slots),
            "capture_slot_count": len(slots),
            "verified_runtime_slot_count": verified_runtime_slot_count,
            "pending_slot_count": pending_slot_count,
            "runtime_capture_coverage_ratio": runtime_coverage,
            "projection_pair_coverage_ratio": projection_pair_coverage,
            "entity_target_count": len(entity_rows),
            "action_target_count": len(action_rows),
            "target_rule_count": len(target_rule_counter),
            "required_runtime_event_count": len(slots) * 2,
        },
        "interpretation": {
            "purpose": "Convert the R3 authority debt into concrete runtime capture slots with entity, action, no-tick and heuristic acceptance criteria.",
            "sovereignty": "PNVA becomes harder to misrepresent when every runtime replacement has an explicit slot, target authority and proof requirement.",
            "boundary": boundary,
        },
        "recommendations": recommendations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA R3 runtime capture matrix.")
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
