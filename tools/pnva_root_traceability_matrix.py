#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

DEFAULT_RUNTIME_EVENTS = "reports/pnva-r3-runtime-events-2026-05-05.jsonl"
DEFAULT_RUNTIME_ENTITIES = "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json"
DEFAULT_RUNTIME_GUARD = "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json"
DEFAULT_RUNTIME_NO_TICK = "reports/pnva-r3-runtime-no-tick-2026-05-05.json"
DEFAULT_RUNTIME_POLICY = "reports/pnva-r3-runtime-policy-2026-05-05.json"
DEFAULT_RUNTIME_PROOF_CHAIN = "reports/pnva-r3-runtime-proof-chain-2026-05-05.json"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_no, "error": str(exc)})
            continue
        if isinstance(event, dict):
            event["_line"] = line_no
            events.append(event)
        else:
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
    return events, errors


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _slot_id(event: dict[str, Any]) -> str:
    return str(_dig(event, ["tension", "components", "r3_runtime_slot_id"], ""))


def _role(event: dict[str, Any]) -> str:
    proof_ref = str(_dig(event, ["proof", "proof_ref"], ""))
    if proof_ref.endswith(":precheck"):
        return "precheck"
    if proof_ref.endswith(":commit"):
        return "commit"
    kind = str(_dig(event, ["decision", "kind"], ""))
    if kind == "observe":
        return "precheck"
    if kind == "collapse":
        return "commit"
    return "unknown"


def _proof_hash_ok(value: Any) -> bool:
    text = str(value or "")
    if not text.startswith("sha256:"):
        return False
    digest = text.split(":", 1)[1]
    return len(digest) == 64 and all(char in "0123456789abcdef" for char in digest)


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _counter_to_pairs(counter: Counter[str]) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))]


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _slot_row(slot_id: str, slot_events: list[dict[str, Any]], entities: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(slot_events, key=lambda event: int(event.get("_line", 0) or 0))
    prechecks = [event for event in ordered if _role(event) == "precheck"]
    commits = [event for event in ordered if _role(event) == "commit"]
    precheck = prechecks[0] if prechecks else {}
    commit = commits[0] if commits else {}

    failures: list[str] = []
    if len(prechecks) != 1:
        failures.append("precheck_cardinality")
    if len(commits) != 1:
        failures.append("commit_cardinality")

    entity_ids = {str(event.get("entity_id", "")) for event in ordered}
    entity_types = {str(event.get("entity_type", "")) for event in ordered}
    if len(entity_ids) != 1 or "" in entity_ids:
        failures.append("entity_id_not_unique")
    if len(entity_types) != 1 or "" in entity_types:
        failures.append("entity_type_not_unique")
    entity_id = next(iter(entity_ids)) if entity_ids else ""
    entity_type = next(iter(entity_types)) if entity_types else ""
    catalog_entity = entities.get(entity_id, {})
    if not catalog_entity or catalog_entity.get("entity_type") != entity_type:
        failures.append("entity_not_catalog_bound")

    chain_ids = {str(event.get("causal_chain_id", "")) for event in ordered}
    if len(chain_ids) != 1 or "" in chain_ids:
        failures.append("causal_chain_not_unique")

    proof_hashes = [str(_dig(event, ["proof", "proof_hash"], "")) for event in ordered]
    proof_refs = [str(_dig(event, ["proof", "proof_ref"], "")) for event in ordered]
    if len(proof_hashes) != len(set(proof_hashes)) or not all(_proof_hash_ok(value) for value in proof_hashes):
        failures.append("proof_hash_not_unique_or_invalid")
    if len(proof_refs) != len(set(proof_refs)) or not all(value.startswith(f"runtime:{slot_id}:") for value in proof_refs):
        failures.append("proof_ref_not_slot_bound")
    if any(_dig(event, ["proof", "valid"]) is not True for event in ordered):
        failures.append("proof_invalid")
    if any(_dig(event, ["proof", "native"]) is not True for event in ordered):
        failures.append("proof_not_native")
    if any(_dig(event, ["proof", "projection"]) is True for event in ordered):
        failures.append("projection_proof_present")

    source_files = {str(_dig(event, ["source", "file_name"], "")) for event in ordered}
    source_formats = {str(_dig(event, ["source", "format"], "")) for event in ordered}
    if len(source_files) != 1 or "" in source_files:
        failures.append("source_file_not_unique")
    if source_formats != {"native_pnva_event_v1"}:
        failures.append("source_format_not_native")
    if any(_dig(event, ["source", "sanitized"]) is not True for event in ordered):
        failures.append("source_not_sanitized")

    pre_score = _num(_dig(precheck, ["tension", "score"]))
    pre_threshold = _num(_dig(precheck, ["tension", "threshold"]))
    pre_gate = _num(_dig(precheck, ["tension", "gate_delta"]))
    commit_score = _num(_dig(commit, ["tension", "score"]))
    commit_threshold = _num(_dig(commit, ["tension", "threshold"]))
    commit_gate = _num(_dig(commit, ["tension", "gate_delta"]))
    if prechecks and not (pre_score < pre_threshold and pre_gate < 0):
        failures.append("precheck_not_no_tick_below_threshold")
    if commits and not (commit_score >= commit_threshold and commit_gate > 0):
        failures.append("commit_not_collapse_above_threshold")

    if prechecks and commits:
        if str(precheck.get("timestamp", "")) >= str(commit.get("timestamp", "")):
            failures.append("timestamp_not_ordered")
        if int(precheck.get("_line", 0) or 0) >= int(commit.get("_line", 0) or 0):
            failures.append("jsonl_line_not_ordered")
        if _num(_dig(precheck, ["source", "line"])) >= _num(_dig(commit, ["source", "line"])):
            failures.append("source_line_not_ordered")
        if _dig(precheck, ["field", "state_after"]) != _dig(commit, ["field", "state_before"]):
            failures.append("field_state_not_continuous")

    rule_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    for event in ordered:
        rule_counter.update(str(rule) for rule in _dig(event, ["heuristics", "rules"], []) or [])
        risk_counter.update(str(flag) for flag in _dig(event, ["heuristics", "risk_flags"], []) or [])
        action_counter.update([str(_dig(event, ["decision", "action"], ""))])
        decision_counter.update([str(_dig(event, ["decision", "kind"], ""))])

    if not {"native_event_emitter", "adaptive_threshold", "field_scheduler"}.issubset(set(rule_counter)):
        failures.append("required_runtime_rules_missing")

    return {
        "slot_id": slot_id,
        "valid": not failures,
        "failure_codes": failures,
        "event_count": len(ordered),
        "precheck_count": len(prechecks),
        "commit_count": len(commits),
        "entity_id": entity_id,
        "entity_type": entity_type,
        "causal_chain_id": next(iter(chain_ids)) if chain_ids else "",
        "precheck_event_id": precheck.get("event_id", ""),
        "commit_event_id": commit.get("event_id", ""),
        "precheck_gate_delta": pre_gate,
        "commit_gate_delta": commit_gate,
        "precheck_score": pre_score,
        "commit_score": commit_score,
        "threshold": commit_threshold or pre_threshold,
        "state_path": [
            _dig(precheck, ["field", "state_before"], ""),
            _dig(precheck, ["field", "state_after"], ""),
            _dig(commit, ["field", "state_after"], ""),
        ],
        "source_file": next(iter(source_files)) if source_files else "",
        "source_lines": [int(_dig(event, ["source", "line"], 0) or 0) for event in ordered],
        "jsonl_lines": [int(event.get("_line", 0) or 0) for event in ordered],
        "proof_refs": proof_refs,
        "proof_hashes": proof_hashes,
        "heuristic_rules": _counter_to_pairs(rule_counter),
        "risk_flags": _counter_to_pairs(risk_counter),
        "actions": _counter_to_pairs(action_counter),
        "decisions": _counter_to_pairs(decision_counter),
    }


def build_report(
    repo: Path,
    runtime_events_path: Path,
    runtime_entities_path: Path,
    runtime_guard_path: Path,
    runtime_no_tick_path: Path,
    runtime_policy_path: Path,
    runtime_proof_chain_path: Path,
) -> dict[str, Any]:
    events, parse_errors = _read_jsonl(runtime_events_path)
    entity_catalog = _read_json(runtime_entities_path)
    runtime_guard = _read_json(runtime_guard_path)
    runtime_no_tick = _read_json(runtime_no_tick_path)
    runtime_policy = _read_json(runtime_policy_path)
    runtime_proof_chain = _read_json(runtime_proof_chain_path)

    entities = {str(item.get("entity_id", "")): item for item in entity_catalog.get("entities", []) if isinstance(item, dict)}
    by_slot: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_slot[_slot_id(event)].append(event)

    slot_rows = [_slot_row(slot_id, by_slot[slot_id], entities) for slot_id in sorted(slot for slot in by_slot if slot)]
    invalid_slot_rows = [row for row in slot_rows if not row["valid"]]

    rule_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    entity_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()
    proof_hashes: list[str] = []
    proof_refs: list[str] = []
    native_proof_count = 0
    projected_proof_count = 0
    for event in events:
        entity_counter.update([str(event.get("entity_id", ""))])
        decision_counter.update([str(_dig(event, ["decision", "kind"], ""))])
        action_counter.update([str(_dig(event, ["decision", "action"], ""))])
        rule_counter.update(str(rule) for rule in _dig(event, ["heuristics", "rules"], []) or [])
        risk_counter.update(str(flag) for flag in _dig(event, ["heuristics", "risk_flags"], []) or [])
        proof_hashes.append(str(_dig(event, ["proof", "proof_hash"], "")))
        proof_refs.append(str(_dig(event, ["proof", "proof_ref"], "")))
        native_proof_count += 1 if _dig(event, ["proof", "native"]) is True else 0
        projected_proof_count += 1 if _dig(event, ["proof", "projection"]) is True else 0

    precheck_count = sum(1 for event in events if _role(event) == "precheck")
    commit_count = sum(1 for event in events if _role(event) == "commit")
    no_tick_efficiency = runtime_no_tick.get("no_tick_efficiency", {})
    proof_chain_seal = runtime_proof_chain.get("seal", {})
    policy_summary = runtime_policy.get("summary", {})

    checks = [
        _check(
            "runtime_event_stream_closed",
            not parse_errors and len(events) == 70 and len(by_slot) == 35 and precheck_count == 35 and commit_count == 35,
            {
                "event_count": len(events),
                "slot_count": len(by_slot),
                "precheck_count": precheck_count,
                "commit_count": commit_count,
                "parse_error_count": len(parse_errors),
            },
        ),
        _check(
            "slot_rows_all_valid",
            len(slot_rows) == 35 and not invalid_slot_rows,
            {
                "slot_row_count": len(slot_rows),
                "invalid_slot_count": len(invalid_slot_rows),
                "invalid_slots": [row["slot_id"] for row in invalid_slot_rows[:10]],
            },
        ),
        _check(
            "entity_binding_closed",
            int(entity_catalog.get("entity_count", 0)) == len(entities) == len([entity for entity in entity_counter if entity]) == 1,
            {
                "catalog_entity_count": entity_catalog.get("entity_count"),
                "observed_entity_count": len([entity for entity in entity_counter if entity]),
                "entity_mix": _counter_to_pairs(entity_counter),
            },
        ),
        _check(
            "heuristic_authority_closed",
            runtime_policy.get("classification") == "SOVEREIGN_POLICY_READY"
            and policy_summary.get("low_authority_legacy_count") == 0
            and policy_summary.get("strong_decision_count") == 35
            and policy_summary.get("proof_policy_bad") == 0
            and dict(policy_summary.get("authority_mix", [])).get("H2") == 70,
            {
                "policy_classification": runtime_policy.get("classification"),
                "authority_mix": policy_summary.get("authority_mix", []),
                "strong_decision_count": policy_summary.get("strong_decision_count"),
                "low_authority_legacy_count": policy_summary.get("low_authority_legacy_count"),
                "proof_policy_bad": policy_summary.get("proof_policy_bad"),
            },
        ),
        _check(
            "no_tick_efficiency_aligned",
            runtime_no_tick.get("classification") == "SOVEREIGN_NO_TICK_READY"
            and no_tick_efficiency.get("event_count") == 70
            and no_tick_efficiency.get("suppressed_count") == 35
            and no_tick_efficiency.get("collapse_count") == 35
            and no_tick_efficiency.get("no_tick_suppression_ratio") == 0.5
            and no_tick_efficiency.get("proof_integrity_ratio") == 1.0,
            {
                "no_tick_classification": runtime_no_tick.get("classification"),
                "no_tick_efficiency": no_tick_efficiency,
            },
        ),
        _check(
            "runtime_guard_aligned",
            runtime_guard.get("classification") == "R3_RUNTIME_EVIDENCE_ACCEPTED"
            and runtime_guard.get("accepted_slot_count") == 35
            and runtime_guard.get("pending_slot_count") == 0
            and runtime_guard.get("no_tick_pair_integrity_count") == 35
            and runtime_guard.get("no_tick_pair_failure_count") == 0
            and runtime_guard.get("negative_control_detected_count") == runtime_guard.get("negative_control_count") == 63,
            {
                "guard_classification": runtime_guard.get("classification"),
                "accepted_slot_count": runtime_guard.get("accepted_slot_count"),
                "pending_slot_count": runtime_guard.get("pending_slot_count"),
                "no_tick_pair_integrity_count": runtime_guard.get("no_tick_pair_integrity_count"),
                "no_tick_pair_failure_count": runtime_guard.get("no_tick_pair_failure_count"),
                "negative_control_count": runtime_guard.get("negative_control_count"),
                "negative_control_detected_count": runtime_guard.get("negative_control_detected_count"),
            },
        ),
        _check(
            "proof_chain_aligned",
            runtime_proof_chain.get("classification") == "PROOF_CHAIN_SEALED"
            and proof_chain_seal.get("event_count") == len(events)
            and proof_chain_seal.get("proof_ok") == len(events)
            and proof_chain_seal.get("proof_bad") == 0
            and proof_chain_seal.get("unique_event_ids") == len(events),
            {
                "proof_chain_classification": runtime_proof_chain.get("classification"),
                "event_count": proof_chain_seal.get("event_count"),
                "proof_ok": proof_chain_seal.get("proof_ok"),
                "proof_bad": proof_chain_seal.get("proof_bad"),
                "unique_event_ids": proof_chain_seal.get("unique_event_ids"),
                "final_chain_hash": proof_chain_seal.get("final_chain_hash"),
            },
        ),
        _check(
            "proof_identity_closed",
            len(proof_hashes) == len(set(proof_hashes)) == 70
            and len(proof_refs) == len(set(proof_refs)) == 70
            and native_proof_count == 70
            and projected_proof_count == 0,
            {
                "proof_hash_count": len(proof_hashes),
                "unique_proof_hash_count": len(set(proof_hashes)),
                "proof_ref_count": len(proof_refs),
                "unique_proof_ref_count": len(set(proof_refs)),
                "native_proof_count": native_proof_count,
                "projected_proof_count": projected_proof_count,
            },
        ),
    ]
    failures = [check for check in checks if not check["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_TRACEABILITY_MATRIX_READY" if not failures else "PNVA_ROOT_TRACEABILITY_MATRIX_FAIL"

    stable_seed = {
        "slot_rows": [
            {
                "slot_id": row["slot_id"],
                "valid": row["valid"],
                "entity_id": row["entity_id"],
                "precheck_event_id": row["precheck_event_id"],
                "commit_event_id": row["commit_event_id"],
                "proof_refs": row["proof_refs"],
                "failure_codes": row["failure_codes"],
            }
            for row in slot_rows
        ],
        "checks": [{key: check[key] for key in ["name", "pass"]} for check in checks],
        "classification": classification,
    }

    return {
        "schema_version": "pnva.root_traceability_matrix.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "root_traceability_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "summary": {
            "event_count": len(events),
            "slot_count": len(slot_rows),
            "valid_slot_count": len(slot_rows) - len(invalid_slot_rows),
            "invalid_slot_count": len(invalid_slot_rows),
            "precheck_count": precheck_count,
            "commit_count": commit_count,
            "entity_count": len([entity for entity in entity_counter if entity]),
            "heuristic_rule_count": len(rule_counter),
            "risk_flag_count": len(risk_counter),
            "proof_hash_unique_count": len(set(proof_hashes)),
            "proof_ref_unique_count": len(set(proof_refs)),
            "no_tick_suppression_ratio": no_tick_efficiency.get("no_tick_suppression_ratio"),
            "runtime_guard_negative_controls": f"{runtime_guard.get('negative_control_detected_count')}/{runtime_guard.get('negative_control_count')}",
        },
        "runtime_mix": {
            "entities": _counter_to_pairs(entity_counter),
            "decisions": _counter_to_pairs(decision_counter),
            "actions": _counter_to_pairs(action_counter),
            "heuristic_rules": _counter_to_pairs(rule_counter),
            "risk_flags": _counter_to_pairs(risk_counter),
        },
        "slot_rows": slot_rows,
        "root_traceability_hash": "sha256:" + _sha_text(json.dumps(stable_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "interpretation": {
            "purpose": "Expose one root matrix that ties PNVA no-tick runtime evidence to entity identity, heuristic authority, proof identity and slot causality.",
            "sovereignty": "The package is stronger when every no-tick suppression and collapse can be traced to a slot, entity, heuristic set, proof ref and downstream validator.",
            "boundary": "This matrix validates the public deterministic R3 runtime evidence sample; it does not claim private deployment coverage.",
        },
        "recommendations": [
            "Run this matrix after runtime evidence guard, no-tick, policy and proof-chain reports are available.",
            "Treat any invalid slot row as a root blocker before sealing a release.",
            "Use slot_rows as the public laboratory map for reviewers who need to audit no-tick, entity and heuristic behavior.",
        ],
    }


def _resolve(repo: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root traceability matrix.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--runtime-events", default=DEFAULT_RUNTIME_EVENTS)
    parser.add_argument("--runtime-entities", default=DEFAULT_RUNTIME_ENTITIES)
    parser.add_argument("--runtime-guard", default=DEFAULT_RUNTIME_GUARD)
    parser.add_argument("--runtime-no-tick", default=DEFAULT_RUNTIME_NO_TICK)
    parser.add_argument("--runtime-policy", default=DEFAULT_RUNTIME_POLICY)
    parser.add_argument("--runtime-proof-chain", default=DEFAULT_RUNTIME_PROOF_CHAIN)
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(
        repo=repo,
        runtime_events_path=_resolve(repo, args.runtime_events),
        runtime_entities_path=_resolve(repo, args.runtime_entities),
        runtime_guard_path=_resolve(repo, args.runtime_guard),
        runtime_no_tick_path=_resolve(repo, args.runtime_no_tick),
        runtime_policy_path=_resolve(repo, args.runtime_policy),
        runtime_proof_chain_path=_resolve(repo, args.runtime_proof_chain),
    )
    raw = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write:
        out = _resolve(repo, args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
