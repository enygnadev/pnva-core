#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

REPORTS = {
    "manifest": "MANIFEST.json",
    "runtime_events": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
    "runtime_entities": "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json",
    "runtime_emitter": "reports/pnva-r3-runtime-event-emitter-summary-2026-05-05.json",
    "runtime_capture_matrix": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
    "runtime_evidence_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "runtime_replay": "reports/pnva-r3-runtime-replay-2026-05-05.json",
    "runtime_policy": "reports/pnva-r3-runtime-policy-2026-05-05.json",
    "runtime_no_tick": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
    "runtime_proof_chain": "reports/pnva-r3-runtime-proof-chain-2026-05-05.json",
    "root_traceability_matrix": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "r3_cutover_gate": "reports/pnva-r3-cutover-gate-2026-05-05.json",
    "sovereign_evolution_ledger": "reports/pnva-sovereign-evolution-ledger-2026-05-05.json",
    "attestation": "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
    "semantic_consistency": "reports/pnva-semantic-consistency-2026-05-05.json",
    "reproducibility": "reports/pnva-reproducibility-2026-05-05.json",
    "sovereign_audit": "reports/pnva-sovereign-audit-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "runtime_emitter": "R3_RUNTIME_EVENT_EMITTER_READY",
    "runtime_capture_matrix": "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE",
    "runtime_evidence_guard": "R3_RUNTIME_EVIDENCE_ACCEPTED",
    "runtime_replay": "REPLAY_VALID",
    "runtime_policy": "SOVEREIGN_POLICY_READY",
    "runtime_no_tick": "SOVEREIGN_NO_TICK_READY",
    "runtime_proof_chain": "PROOF_CHAIN_SEALED",
    "root_traceability_matrix": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "r3_cutover_gate": "R3_CUTOVER_APPROVED",
    "sovereign_evolution_ledger": "PNVA_SOVEREIGN_EVOLUTION_LEDGER_R3_READY",
    "attestation": "PNVA_SOVEREIGN_EVIDENCE_ATTESTED",
    "semantic_consistency": "SEMANTIC_CONSISTENCY_READY",
    "reproducibility": "REPRODUCIBILITY_READY",
}

KNOWN_RULES = {
    "native_event_emitter",
    "adaptive_threshold",
    "field_scheduler",
    "power_orchestrator",
}

KNOWN_RISK_FLAGS = {
    "RESIZE_BATCH_PRESSURE",
    "THERMAL_PRESSURE",
    "EXECUTION_PRESSURE",
}

STRONG_DECISIONS = {"block", "collapse", "prove", "reclassify"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                events.append(item)
    return events


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _iso_to_dt(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _check(checks: list[dict[str, Any]], *, group: str, name: str, passed: bool, evidence: dict[str, Any]) -> None:
    checks.append(
        {
            "group": group,
            "name": name,
            "pass": bool(passed),
            "evidence": evidence,
        }
    )


def _event_role(event: dict[str, Any]) -> str:
    proof_ref = str(_dig(event, ["proof", "proof_ref"], ""))
    if proof_ref.endswith(":precheck"):
        return "precheck"
    if proof_ref.endswith(":commit"):
        return "commit"
    if str(event.get("event_type", "")).endswith("_authority_precheck"):
        return "precheck"
    return "commit"


def _proof_hash_ok(value: Any) -> bool:
    text = str(value or "")
    return text.startswith("sha256:") and len(text) == 71 and all(c in "0123456789abcdef" for c in text[7:])


def build_report(repo: Path) -> dict[str, Any]:
    data = {}
    for name, rel in REPORTS.items():
        path = repo / rel
        if rel.endswith(".jsonl"):
            data[name] = _read_jsonl(path)
        else:
            data[name] = _read_json(path)

    checks: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = data["runtime_events"]
    entity_catalog = data["runtime_entities"]
    entities = {item.get("entity_id"): item for item in entity_catalog.get("entities", []) if isinstance(item, dict)}
    slots: dict[str, list[dict[str, Any]]] = defaultdict(list)
    event_ids = []
    proof_hashes = []
    proof_refs = []
    source_locations = []
    rule_counter: Counter[str] = Counter()
    risk_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    action_counter: Counter[str] = Counter()

    for event in events:
        slot = _dig(event, ["tension", "components", "r3_runtime_slot_id"])
        if slot:
            slots[str(slot)].append(event)
        event_ids.append(str(event.get("event_id", "")))
        proof_hashes.append(str(_dig(event, ["proof", "proof_hash"], "")))
        proof_refs.append(str(_dig(event, ["proof", "proof_ref"], "")))
        source_locations.append((str(_dig(event, ["source", "file_name"], "")), _dig(event, ["source", "line"])))
        decision_counter[str(_dig(event, ["decision", "kind"], ""))] += 1
        action_counter[str(_dig(event, ["decision", "action"], ""))] += 1
        rule_counter.update(str(rule) for rule in _dig(event, ["heuristics", "rules"], []) or [])
        risk_counter.update(str(flag) for flag in _dig(event, ["heuristics", "risk_flags"], []) or [])

    for key, expected in EXPECTED_CLASSIFICATIONS.items():
        report = data[key]
        _check(
            checks,
            group="classification",
            name=f"{key}_classification",
            passed=report.get("classification") == expected and report.get("pass", True) is not False,
            evidence={
                "path": REPORTS[key],
                "classification": report.get("classification"),
                "expected": expected,
                "pass": report.get("pass", True),
            },
        )

    matrix = data["runtime_capture_matrix"]
    guard = data["runtime_evidence_guard"]
    replay = data["runtime_replay"]
    policy = data["runtime_policy"]
    no_tick = data["runtime_no_tick"]
    proof_chain = data["runtime_proof_chain"]
    traceability = data["root_traceability_matrix"]
    cutover = data["r3_cutover_gate"]
    ledger = data["sovereign_evolution_ledger"]
    attestation = data["attestation"]
    semantic = data["semantic_consistency"]
    reproducibility = data["reproducibility"]
    audit = data["sovereign_audit"]
    manifest = data["manifest"]

    _check(
        checks,
        group="runtime",
        name="runtime_slot_counts_close",
        passed=(
            matrix.get("capture_slot_count") == 35
            and matrix.get("verified_runtime_slot_count") == 35
            and matrix.get("pending_slot_count") == 0
            and matrix.get("required_runtime_event_count") == 70
            and guard.get("accepted_slot_count") == 35
            and guard.get("pending_slot_count") == 0
            and len(events) == 70
            and len(slots) == 35
        ),
        evidence={
            "capture_slots": matrix.get("capture_slot_count"),
            "verified_slots": matrix.get("verified_runtime_slot_count"),
            "pending_slots": matrix.get("pending_slot_count"),
            "accepted_slots": guard.get("accepted_slot_count"),
            "event_count": len(events),
            "slot_count": len(slots),
        },
    )

    _check(
        checks,
        group="runtime",
        name="identity_sets_unique",
        passed=(
            len(event_ids) == len(set(event_ids)) == 70
            and len(proof_hashes) == len(set(proof_hashes)) == 70
            and len(proof_refs) == len(set(proof_refs)) == 70
            and len(source_locations) == len(set(source_locations)) == 70
        ),
        evidence={
            "unique_event_ids": len(set(event_ids)),
            "unique_proof_hashes": len(set(proof_hashes)),
            "unique_proof_refs": len(set(proof_refs)),
            "unique_source_locations": len(set(source_locations)),
        },
    )

    pair_failures = []
    for slot, pair in sorted(slots.items()):
        roles = {_event_role(item): item for item in pair}
        pre = roles.get("precheck")
        commit = roles.get("commit")
        if len(pair) != 2 or not pre or not commit:
            pair_failures.append({"slot": slot, "error": "pair_cardinality_or_roles"})
            continue
        pre_time = _iso_to_dt(str(pre.get("timestamp", "")))
        commit_time = _iso_to_dt(str(commit.get("timestamp", "")))
        failures = []
        if pre.get("causal_chain_id") != commit.get("causal_chain_id"):
            failures.append("causal_chain_mismatch")
        if _dig(pre, ["source", "file_name"]) != _dig(commit, ["source", "file_name"]):
            failures.append("source_file_mismatch")
        if int(_dig(pre, ["source", "line"], 0)) >= int(_dig(commit, ["source", "line"], 0)):
            failures.append("source_line_order")
        if not pre_time or not commit_time or not pre_time < commit_time:
            failures.append("timestamp_order")
        if _dig(pre, ["field", "state_after"]) != "suppressed":
            failures.append("precheck_state_after")
        if _dig(commit, ["field", "state_before"]) != _dig(pre, ["field", "state_after"]):
            failures.append("state_continuity")
        if _dig(commit, ["field", "state_after"]) != "committed":
            failures.append("commit_state_after")
        if _dig(pre, ["decision", "kind"]) != "observe" or _dig(pre, ["decision", "action"]) != "NO_ACTION":
            failures.append("precheck_decision")
        if _dig(commit, ["decision", "kind"]) != "collapse":
            failures.append("commit_decision")
        if float(_dig(pre, ["tension", "gate_delta"], 0.0)) >= 0:
            failures.append("precheck_gate_delta")
        if float(_dig(commit, ["tension", "gate_delta"], 0.0)) <= 0:
            failures.append("commit_gate_delta")
        if failures:
            pair_failures.append({"slot": slot, "errors": failures})

    _check(
        checks,
        group="no_tick",
        name="slot_pairs_are_causal_no_tick_pairs",
        passed=not pair_failures,
        evidence={
            "pair_count": len(slots),
            "pair_failure_count": len(pair_failures),
            "sample_failures": pair_failures[:5],
        },
    )

    entity_failures = [
        event.get("event_id")
        for event in events
        if event.get("entity_id") not in entities or event.get("entity_type") != entities.get(event.get("entity_id"), {}).get("entity_type")
    ]
    _check(
        checks,
        group="entity",
        name="runtime_events_are_entity_catalog_bound",
        passed=(entity_catalog.get("entity_count") == len(entities) == 1 and not entity_failures),
        evidence={
            "catalog_entity_count": entity_catalog.get("entity_count"),
            "observed_entity_count": len({event.get("entity_id") for event in events}),
            "entity_failure_count": len(entity_failures),
        },
    )

    proof_failures = [
        event.get("event_id")
        for event in events
        if _dig(event, ["proof", "valid"]) is not True
        or _dig(event, ["proof", "native"]) is not True
        or _dig(event, ["proof", "projection"]) is True
        or not _proof_hash_ok(_dig(event, ["proof", "proof_hash"]))
        or not str(_dig(event, ["proof", "proof_ref"], "")).startswith("runtime:")
    ]
    _check(
        checks,
        group="proof",
        name="runtime_proofs_are_native_non_projected_and_hash_bound",
        passed=not proof_failures,
        evidence={
            "event_count": len(events),
            "proof_failure_count": len(proof_failures),
            "proof_chain_final_hash": _dig(proof_chain, ["seal", "final_chain_hash"]),
        },
    )

    source_failures = [
        event.get("event_id")
        for event in events
        if _dig(event, ["source", "format"]) != "native_pnva_event_v1"
        or _dig(event, ["source", "sanitized"]) is not True
        or "/" in str(_dig(event, ["source", "file_name"], ""))
        or "\\" in str(_dig(event, ["source", "file_name"], ""))
        or str(_dig(event, ["source", "file_name"], "")).startswith(".")
    ]
    _check(
        checks,
        group="source",
        name="runtime_source_is_sanitized_public_native",
        passed=not source_failures,
        evidence={
            "source_failure_count": len(source_failures),
            "source_file_names": sorted({str(_dig(event, ["source", "file_name"], "")) for event in events}),
            "source_formats": sorted({str(_dig(event, ["source", "format"], "")) for event in events}),
        },
    )

    unknown_rules = sorted(set(rule_counter) - KNOWN_RULES)
    unknown_flags = sorted(set(risk_counter) - KNOWN_RISK_FLAGS)
    duplicate_rule_events = [
        event.get("event_id")
        for event in events
        if len(_dig(event, ["heuristics", "rules"], []) or []) != len(set(_dig(event, ["heuristics", "rules"], []) or []))
    ]
    duplicate_flag_events = [
        event.get("event_id")
        for event in events
        if len(_dig(event, ["heuristics", "risk_flags"], []) or []) != len(set(_dig(event, ["heuristics", "risk_flags"], []) or []))
    ]
    strong_authority_failures = [
        event.get("event_id")
        for event in events
        if str(_dig(event, ["decision", "kind"], "")) in STRONG_DECISIONS
        and float(_dig(event, ["tension", "components", "authority_delta"], 0.0)) < 2.0
    ]
    _check(
        checks,
        group="heuristic",
        name="heuristics_are_known_non_legacy_and_strong_decisions_h2_plus",
        passed=(
            not unknown_rules
            and not unknown_flags
            and not duplicate_rule_events
            and not duplicate_flag_events
            and not strong_authority_failures
            and "legacy_observer" not in rule_counter
            and _dig(policy, ["summary", "low_authority_legacy_count"]) == 0
        ),
        evidence={
            "rules": sorted(rule_counter.items()),
            "risk_flags": sorted(risk_counter.items()),
            "unknown_rules": unknown_rules,
            "unknown_risk_flags": unknown_flags,
            "duplicate_rule_event_count": len(duplicate_rule_events),
            "duplicate_risk_flag_event_count": len(duplicate_flag_events),
            "strong_authority_failure_count": len(strong_authority_failures),
            "policy_low_authority_legacy_count": _dig(policy, ["summary", "low_authority_legacy_count"]),
        },
    )

    _check(
        checks,
        group="no_tick",
        name="runtime_no_tick_efficiency_is_half_suppression_half_commit",
        passed=(
            _dig(no_tick, ["no_tick_efficiency", "event_count"]) == 70
            and _dig(no_tick, ["no_tick_efficiency", "observe_count"]) == 35
            and _dig(no_tick, ["no_tick_efficiency", "collapse_count"]) == 35
            and _dig(no_tick, ["no_tick_efficiency", "suppressed_count"]) == 35
            and _dig(no_tick, ["no_tick_efficiency", "no_tick_suppression_ratio"]) == 0.5
            and _dig(no_tick, ["no_tick_efficiency", "proof_integrity_ratio"]) == 1.0
        ),
        evidence=no_tick.get("no_tick_efficiency", {}),
    )

    _check(
        checks,
        group="traceability",
        name="root_traceability_matrix_closes_slots_entities_heuristics_and_proofs",
        passed=(
            traceability.get("pass") is True
            and traceability.get("root_traceability_score") == 100.0
            and traceability.get("failure_count") == 0
            and _dig(traceability, ["summary", "slot_count"]) == 35
            and _dig(traceability, ["summary", "valid_slot_count"]) == 35
            and _dig(traceability, ["summary", "invalid_slot_count"]) == 0
            and _dig(traceability, ["summary", "proof_hash_unique_count"]) == 70
            and _dig(traceability, ["summary", "proof_ref_unique_count"]) == 70
            and _dig(traceability, ["summary", "no_tick_suppression_ratio"]) == 0.5
        ),
        evidence={
            "classification": traceability.get("classification"),
            "root_traceability_score": traceability.get("root_traceability_score"),
            "failure_count": traceability.get("failure_count"),
            "summary": traceability.get("summary", {}),
            "root_traceability_hash": traceability.get("root_traceability_hash"),
        },
    )

    _check(
        checks,
        group="cutover",
        name="r3_cutover_is_approved_without_remaining_runtime_replacements",
        passed=(
            cutover.get("contract_ready") is True
            and cutover.get("cutover_approved") is True
            and cutover.get("legacy_free_claim_allowed") is True
            and cutover.get("fresh_runtime_evidence_present") is True
            and cutover.get("remaining_runtime_replacement_count") == 0
            and cutover.get("runtime_blocker_count") == 0
        ),
        evidence={
            "contract_ready": cutover.get("contract_ready"),
            "cutover_approved": cutover.get("cutover_approved"),
            "legacy_free_claim_allowed": cutover.get("legacy_free_claim_allowed"),
            "remaining_runtime_replacement_count": cutover.get("remaining_runtime_replacement_count"),
            "runtime_blocker_count": cutover.get("runtime_blocker_count"),
        },
    )

    _check(
        checks,
        group="ledger",
        name="sovereign_ledger_is_r3_ready_with_no_runtime_blockers",
        passed=(
            ledger.get("r3_runtime_evidence_approved") is True
            and ledger.get("r3_cutover_approved") is True
            and ledger.get("runtime_pending_slot_count") == 0
            and ledger.get("blocker_count") == 0
            and float(ledger.get("sovereign_evolution_score", 0.0)) >= 98.0
        ),
        evidence={
            "score": ledger.get("sovereign_evolution_score"),
            "runtime_pending_slot_count": ledger.get("runtime_pending_slot_count"),
            "blocker_count": ledger.get("blocker_count"),
            "controlled_warning_count": ledger.get("controlled_warning_count"),
        },
    )

    _check(
        checks,
        group="attestation",
        name="attestation_semantic_reproducibility_and_audit_are_clean",
        passed=(
            attestation.get("pass") is True
            and int(attestation.get("failure_count", -1)) == 0
            and int(attestation.get("artifact_count", 0)) >= 48
            and str(attestation.get("evidence_hash", "")).startswith("sha256:")
            and semantic.get("pass") is True
            and int(semantic.get("error_count", -1)) == 0
            and reproducibility.get("pass") is True
            and int(reproducibility.get("failure_count", -1)) == 0
            and _dig(audit, ["score", "classification"]) == "SOVEREIGN_READY"
            and _dig(audit, ["score", "total"]) == 100
            and not _dig(audit, ["sovereignty", "path_leaks"], [])
        ),
        evidence={
            "artifact_count": attestation.get("artifact_count"),
            "attestation_failures": attestation.get("failure_count"),
            "semantic_errors": semantic.get("error_count"),
            "reproducibility_failures": reproducibility.get("failure_count"),
            "audit_score": _dig(audit, ["score", "total"]),
            "audit_path_leaks": len(_dig(audit, ["sovereignty", "path_leaks"], [])),
        },
    )

    manifest_files = set(manifest.get("files", []))
    required_manifest_files = {path for name, path in REPORTS.items() if name != "manifest"}
    missing_manifest_files = sorted(required_manifest_files - manifest_files)
    _check(
        checks,
        group="manifest",
        name="manifest_tracks_root_inputs",
        passed=not missing_manifest_files,
        evidence={
            "required_input_count": len(required_manifest_files),
            "missing_manifest_files": missing_manifest_files,
        },
    )

    pycache_paths = [str(path.relative_to(repo)) for path in repo.rglob("__pycache__") if path.is_dir()]
    _check(
        checks,
        group="hygiene",
        name="repository_has_no_python_bytecode_cache",
        passed=not pycache_paths,
        evidence={"pycache_count": len(pycache_paths), "sample": pycache_paths[:5]},
    )

    failures = [check for check in checks if not check["pass"]]
    root_score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_SOVEREIGNTY_GUARD_READY" if not failures else "PNVA_ROOT_SOVEREIGNTY_GUARD_FAIL"

    return {
        "schema_version": "pnva.root_sovereignty_guard.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "root_score": root_score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": len(events),
        "slot_count": len(slots),
        "entity_count": len(entities),
        "decision_mix": sorted(decision_counter.items()),
        "action_mix": sorted(action_counter.items()),
        "heuristic_rule_mix": sorted(rule_counter.items()),
        "risk_flag_mix": sorted(risk_counter.items()),
        "root_invariants": [
            "R3 runtime capture has 35 verified slots, 70 native events and zero pending slots.",
            "Every slot has one no-tick precheck and one collapse commit in the same causal chain.",
            "Every runtime event is entity-bound, source-sanitized, native, non-projected and proof-hash bound.",
            "Strong runtime decisions are H2+ by policy and avoid legacy observer authority.",
            "Replay, policy, no-tick, proof-chain, cutover, ledger, attestation, semantic, reproducibility and audit all pass.",
            "The public package keeps historical legacy warnings visible while the R3 runtime path is native-clean.",
        ],
        "checks": checks,
        "failures": failures,
        "evidence_refs": REPORTS,
        "interpretation": {
            "purpose": "Collapse PNVA runtime evidence, no-tick causality, entity coverage, heuristic authority, proof integrity and publication hygiene into one root guard.",
            "sovereignty": "The system is stronger when root readiness is decided by cross-report invariants instead of a single PASS flag.",
            "boundary": "This guard validates the public repository evidence package and deterministic R3 runtime sample; it does not claim proof for private deployments not represented by these artifacts.",
        },
        "recommendations": [
            "Run this root guard after attestation, semantic consistency, reproducibility and sovereign audit.",
            "Keep it outside the attestation hash seed because it consumes attestation, audit and reproducibility reports.",
            "Treat any root guard failure as a release blocker before public R3 claims.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the root PNVA sovereignty evidence package.")
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
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
