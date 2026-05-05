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
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

EVENT_STREAMS = {
    "canonical": "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "native": "reports/pnva-native-events-demo-2026-05-05.jsonl",
    "runtime_r3": "reports/pnva-r3-runtime-events-2026-05-05.jsonl",
}

NO_TICK_REPORTS = {
    "canonical": "reports/pnva-no-tick-invariants-2026-05-05.json",
    "native": "reports/pnva-native-no-tick-invariants-2026-05-05.json",
    "runtime_r3": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
}

ROOT_REPORTS = {
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "invariant_firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_ROOT_CLASSIFICATIONS = {
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "invariant_firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_no, "error": str(exc)})
            continue
        if isinstance(item, dict):
            item["_line"] = line_no
            rows.append(item)
        else:
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
    return rows, errors


def _dig(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _decision(event: dict[str, Any]) -> str:
    decision = event.get("decision")
    if not isinstance(decision, dict):
        return "unknown"
    return str(decision.get("kind") or "unknown")


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    rules = heuristics.get("rules")
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _proof(event: dict[str, Any]) -> dict[str, Any]:
    proof = event.get("proof")
    return proof if isinstance(proof, dict) else {}


def _gate_delta(event: dict[str, Any]) -> float | None:
    value = _dig(event, "tension.gate_delta")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _strict_threshold_violation(event: dict[str, Any]) -> str:
    decision = _decision(event)
    gate_delta = _gate_delta(event)
    if gate_delta is None:
        return "missing_gate_delta"
    if decision in {"observe", "block"} and gate_delta > 0:
        return "suppression_above_threshold"
    if decision in {"collapse", "prove"} and gate_delta <= 0:
        return "execution_below_or_at_threshold"
    if decision not in {"observe", "block", "collapse", "prove"}:
        return "unknown_decision"
    return ""


def _canonical_threshold_exception(event: dict[str, Any]) -> str:
    decision = _decision(event)
    gate_delta = _gate_delta(event)
    if gate_delta is None:
        return "missing_gate_delta"
    if decision in {"observe", "block"} and gate_delta > 0:
        return "canonical_suppression_above_threshold"
    if decision in {"collapse", "prove"} and gate_delta <= 0:
        return "canonical_execution_below_or_at_threshold"
    return ""


def _classification_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "classification": reports[name].get("classification"),
            "expected": expected,
            "pass": reports[name].get("classification") == expected and reports[name].get("pass") is True,
        }
        for name, expected in EXPECTED_ROOT_CLASSIFICATIONS.items()
    ]


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def build_report(repo: Path) -> dict[str, Any]:
    no_tick_reports = {name: _read_json(repo / rel) for name, rel in NO_TICK_REPORTS.items()}
    root_reports = {name: _read_json(repo / rel) for name, rel in ROOT_REPORTS.items()}
    entity_report = root_reports["entity_capability"]
    heuristic_report = root_reports["heuristic_weight"]
    topology_report = root_reports["field_topology"]
    observability_report = root_reports["observability"]
    firewall_report = root_reports["invariant_firewall"]
    claim_report = root_reports["claim_boundary"]
    publication_report = root_reports["publication_gate"]
    verifier_report = root_reports["release_verifier"]

    entity_keys = {str(row.get("ledger_key")) for row in entity_report.get("entities", [])}
    rules = {str(row.get("rule")) for row in heuristic_report.get("rules", [])}

    events_by_scope: dict[str, list[dict[str, Any]]] = {}
    parse_errors: list[dict[str, Any]] = []
    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        events_by_scope[scope] = events
        parse_errors.extend({"scope": scope, **item} for item in errors)

    all_events = [(scope, event) for scope, events in events_by_scope.items() for event in events]
    event_ids: Counter[str] = Counter()
    proof_hashes: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    scope_event_counts: Counter[str] = Counter()
    strict_violations: list[dict[str, Any]] = []
    canonical_exceptions: list[dict[str, Any]] = []
    entity_unknown: list[dict[str, Any]] = []
    rule_unknown: list[dict[str, Any]] = []
    schema_failures: list[dict[str, Any]] = []
    source_path_leaks: list[dict[str, Any]] = []
    proof_failures: list[dict[str, Any]] = []
    projection_events: list[dict[str, Any]] = []
    guard_contract_failures: list[dict[str, Any]] = []
    r3_chains: dict[str, Counter[str]] = defaultdict(Counter)

    suppressed_count = 0
    collapse_count = 0
    prove_count = 0
    block_count = 0
    observe_count = 0

    for scope, event in all_events:
        scope_event_counts[scope] += 1
        event_id = str(event.get("event_id") or "")
        if event_id:
            event_ids[event_id] += 1
        decision = _decision(event)
        decision_counts[decision] += 1
        if decision in {"observe", "block"}:
            suppressed_count += 1
        if decision == "observe":
            observe_count += 1
        if decision == "block":
            block_count += 1
        if decision == "collapse":
            collapse_count += 1
        if decision == "prove":
            prove_count += 1

        if event.get("schema_version") != "pnva.event.v1":
            schema_failures.append({"scope": scope, "event_id": event_id, "schema_version": event.get("schema_version")})

        source_file = str(_dig(event, "source.file_name", ""))
        if "/" in source_file or "\\" in source_file:
            source_path_leaks.append({"scope": scope, "event_id": event_id, "source_file": source_file})

        proof = _proof(event)
        proof_hash = str(proof.get("proof_hash") or "")
        if proof_hash:
            proof_hashes[proof_hash] += 1
        if proof.get("valid") is not True or not proof_hash.startswith("sha256:"):
            proof_failures.append({"scope": scope, "event_id": event_id, "proof_valid": proof.get("valid"), "proof_hash": proof_hash})
        if proof.get("projection") is True:
            projection_events.append({"scope": scope, "event_id": event_id})

        entity_key = f"{scope}:{event.get('entity_id')}"
        if entity_key not in entity_keys:
            entity_unknown.append({"scope": scope, "event_id": event_id, "entity_key": entity_key})

        event_rules = _rules(event)
        if not event_rules:
            rule_unknown.append({"scope": scope, "event_id": event_id, "rule": "missing"})
        for rule in event_rules:
            if rule not in rules:
                rule_unknown.append({"scope": scope, "event_id": event_id, "rule": rule})

        if scope in {"native", "runtime_r3"}:
            violation = _strict_threshold_violation(event)
            if violation:
                strict_violations.append({"scope": scope, "event_id": event_id, "violation": violation, "decision": decision, "gate_delta": _gate_delta(event)})
        else:
            exception = _canonical_threshold_exception(event)
            if exception:
                canonical_exceptions.append({"event_id": event_id, "exception": exception, "decision": decision, "gate_delta": _gate_delta(event)})

        event_type = str(event.get("event_type") or "")
        if event_type == "ETEV_GUARD_PASS" and decision != "collapse":
            guard_contract_failures.append({"scope": scope, "event_id": event_id, "event_type": event_type, "decision": decision})
        if event_type == "ETEV_GUARD_BLOCK" and decision != "block":
            guard_contract_failures.append({"scope": scope, "event_id": event_id, "event_type": event_type, "decision": decision})

        if scope == "runtime_r3":
            chain_id = str(event.get("causal_chain_id") or "")
            r3_chains[chain_id].update([decision])

    duplicate_event_ids = [event_id for event_id, count in event_ids.items() if count > 1]
    duplicate_proof_hashes = [proof_hash for proof_hash, count in proof_hashes.items() if count > 1]
    r3_pair_failures = [
        {"causal_chain_id": chain_id, "decision_mix": sorted(counter.items())}
        for chain_id, counter in sorted(r3_chains.items())
        if counter.get("observe") != 1 or counter.get("collapse") != 1 or sum(counter.values()) != 2
    ]

    no_tick_checks = [
        {
            "name": scope,
            "classification": report.get("classification"),
            "pass": report.get("classification") == "SOVEREIGN_NO_TICK_READY" and report.get("pass") is True and not report.get("failed_invariants"),
            "event_count": _dig(report, "summary.event_count", 0),
        }
        for scope, report in no_tick_reports.items()
    ]
    root_classification_checks = _classification_checks(root_reports)

    observed_suppressed = _dig(observability_report, "no_tick_observability.aggregate_suppressed_count", 0)
    observed_event_count = _dig(observability_report, "no_tick_observability.aggregate_event_count", 0)
    observed_collapse = _dig(observability_report, "no_tick_observability.aggregate_collapse_count", 0)
    total_events = len(all_events)
    strict_event_count = scope_event_counts["native"] + scope_event_counts["runtime_r3"]
    checks = [
        _check("no_tick_layers_ready", all(item["pass"] for item in no_tick_checks), {"layers": no_tick_checks}),
        _check("root_ledgers_ready", all(item["pass"] for item in root_classification_checks), {"reports": root_classification_checks}),
        _check("parse_clean", not parse_errors, {"parse_error_count": len(parse_errors), "parse_errors": parse_errors[:10]}),
        _check(
            "event_identity_unique",
            total_events == len(event_ids) and not duplicate_event_ids,
            {"event_count": total_events, "unique_event_id_count": len(event_ids), "duplicates": duplicate_event_ids[:20]},
        ),
        _check(
            "schema_and_public_sources_clean",
            not schema_failures and not source_path_leaks,
            {"schema_failure_count": len(schema_failures), "source_path_leak_count": len(source_path_leaks), "source_path_leaks": source_path_leaks[:20]},
        ),
        _check(
            "proof_contract_complete",
            not proof_failures and not duplicate_proof_hashes and not projection_events,
            {
                "proof_valid_count": total_events - len(proof_failures),
                "proof_failure_count": len(proof_failures),
                "duplicate_proof_hash_count": len(duplicate_proof_hashes),
                "projection_event_count": len(projection_events),
            },
        ),
        _check(
            "entity_and_rule_closure_complete",
            not entity_unknown and not rule_unknown,
            {"unknown_entity_count": len(entity_unknown), "unknown_rule_count": len(rule_unknown), "unknown_entities": entity_unknown[:20], "unknown_rules": rule_unknown[:20]},
        ),
        _check(
            "suppression_matches_observability",
            suppressed_count == observed_suppressed and total_events == observed_event_count and collapse_count == observed_collapse,
            {
                "suppressed_count": suppressed_count,
                "observed_suppressed_count": observed_suppressed,
                "event_count": total_events,
                "observed_event_count": observed_event_count,
                "collapse_count": collapse_count,
                "observed_collapse_count": observed_collapse,
            },
        ),
        _check(
            "native_and_r3_threshold_contract_strict",
            strict_event_count > 0 and not strict_violations,
            {"strict_event_count": strict_event_count, "strict_violation_count": len(strict_violations), "violations": strict_violations[:20]},
        ),
        _check(
            "r3_precheck_commit_pairs_complete",
            len(r3_chains) == 35 and not r3_pair_failures,
            {"r3_chain_count": len(r3_chains), "r3_pair_failure_count": len(r3_pair_failures), "failures": r3_pair_failures[:20]},
        ),
        _check(
            "guard_event_contract_consistent",
            not guard_contract_failures,
            {"guard_event_count": sum(1 for _, event in all_events if str(event.get("event_type") or "") in {"ETEV_GUARD_PASS", "ETEV_GUARD_BLOCK"}), "guard_failure_count": len(guard_contract_failures), "failures": guard_contract_failures[:20]},
        ),
        _check(
            "canonical_legacy_threshold_exceptions_bounded",
            bool(canonical_exceptions)
            and topology_report.get("blocked_edge_count") == 0
            and topology_report.get("orphan_entity_count") == 0
            and topology_report.get("orphan_rule_count") == 0
            and topology_report.get("legacy_edge_count", 0) > 0,
            {
                "canonical_exception_count": len(canonical_exceptions),
                "policy": "canonical threshold sign exceptions are accepted only as bounded legacy/canonical evidence, never in native or R3 runtime",
                "blocked_edge_count": topology_report.get("blocked_edge_count"),
                "orphan_entity_count": topology_report.get("orphan_entity_count"),
                "orphan_rule_count": topology_report.get("orphan_rule_count"),
                "legacy_edge_count": topology_report.get("legacy_edge_count"),
            },
        ),
        _check(
            "topology_projection_and_blocking_clean",
            topology_report.get("blocked_edge_count") == 0
            and topology_report.get("unknown_entity_event_count") == 0
            and topology_report.get("unruled_event_count") == 0
            and topology_report.get("field_topology_score") == 100.0,
            {
                "blocked_edge_count": topology_report.get("blocked_edge_count"),
                "unknown_entity_event_count": topology_report.get("unknown_entity_event_count"),
                "unruled_event_count": topology_report.get("unruled_event_count"),
                "field_topology_score": topology_report.get("field_topology_score"),
            },
        ),
        _check(
            "public_boundary_clean",
            publication_report.get("path_leak_count") == 0 and claim_report.get("unbounded_high_risk_occurrence_count") == 0,
            {"path_leak_count": publication_report.get("path_leak_count"), "unbounded_high_risk_occurrence_count": claim_report.get("unbounded_high_risk_occurrence_count")},
        ),
        _check(
            "root_hash_stable",
            verifier_report.get("root_release_hash") == ROOT_RELEASE_HASH and verifier_report.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_release_hash": verifier_report.get("root_release_hash"), "recomputed_root_release_hash": verifier_report.get("recomputed_root_release_hash")},
        ),
    ]

    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY" if not failures else "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_FAIL"
    contract_seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "decision_counts": dict(sorted(decision_counts.items())),
        "scope_event_counts": dict(sorted(scope_event_counts.items())),
        "suppressed_count": suppressed_count,
        "canonical_exception_count": len(canonical_exceptions),
        "strict_violation_count": len(strict_violations),
        "r3_chain_count": len(r3_chains),
    }

    return {
        "schema_version": "pnva.root_no_tick_causal_contract.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "causal_contract_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": total_events,
        "scope_event_counts": dict(sorted(scope_event_counts.items())),
        "decision_counts": dict(sorted(decision_counts.items())),
        "collapse_count": collapse_count,
        "observe_count": observe_count,
        "block_count": block_count,
        "prove_count": prove_count,
        "suppressed_count": suppressed_count,
        "suppression_ratio": _ratio(suppressed_count, total_events),
        "proof_valid_count": total_events - len(proof_failures),
        "projection_event_count": len(projection_events),
        "strict_native_r3_event_count": strict_event_count,
        "strict_threshold_violation_count": len(strict_violations),
        "canonical_legacy_threshold_exception_count": len(canonical_exceptions),
        "r3_chain_count": len(r3_chains),
        "r3_pair_failure_count": len(r3_pair_failures),
        "guard_contract_failure_count": len(guard_contract_failures),
        "unknown_entity_count": len(entity_unknown),
        "unknown_rule_count": len(rule_unknown),
        "root_release_hash": ROOT_RELEASE_HASH,
        "no_tick_causal_contract_hash": _sha_text(json.dumps(contract_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "no_tick_layer_checks": no_tick_checks,
        "root_classification_checks": root_classification_checks,
        "interpretation": {
            "purpose": "Bind no-tick events, proof logs, entities, heuristic rules and threshold behavior into one root causal contract.",
            "sovereignty": "A no-tick system is governable when suppression and collapse can be traced to proof-backed entities and rules.",
            "boundary": "This report audits public evidence only. It does not execute system actions, alter live gates or claim universal deployment behavior.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root no-tick causal contract.")
    parser.add_argument("--repo", default=".", help="Repository root.")
    parser.add_argument("--write", help="Optional report path.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.write:
        path = Path(args.write)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
