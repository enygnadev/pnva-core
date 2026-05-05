#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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

REPORTS = {
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "event_identity": "reports/pnva-root-event-identity-ledger-2026-05-05.json",
    "causal_mesh": "reports/pnva-root-causal-mesh-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "runtime_growth_budget": "reports/pnva-root-runtime-growth-budget-2026-05-05.json",
    "negative_controls": "reports/pnva-root-admission-negative-controls-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "event_identity": "PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY",
    "causal_mesh": "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "runtime_growth_budget": "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY",
    "negative_controls": "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}

SUPPRESSED_DECISIONS = {"observe", "block"}
EXECUTION_DECISIONS = {"collapse"}


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
        if not isinstance(item, dict):
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
            continue
        item["_line"] = line_no
        item["_source_file"] = path.name
        rows.append(item)
    return rows, errors


def _dig(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _num(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default


def _ratio(numerator: int | float, denominator: int | float) -> float:
    return round(float(numerator) / float(denominator), 6) if denominator else 0.0


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _source_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "classification": reports[name].get("classification"),
            "expected": expected,
            "pass": reports[name].get("classification") == expected and reports[name].get("pass") is True,
        }
        for name, expected in EXPECTED_CLASSIFICATIONS.items()
    ]


def _top(counter: Counter[str], limit: int = 10) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _entity_rows(events: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for scope, event in events:
        entity = str(event.get("entity_id") or "")
        if not entity:
            continue
        row = rows.setdefault(
            f"{scope}:{entity}",
            {
                "scope": scope,
                "entity_id": entity,
                "entity_type": str(event.get("entity_type") or ""),
                "event_count": 0,
                "collapse_count": 0,
                "suppressed_count": 0,
                "proof_valid_count": 0,
                "rules": Counter(),
            },
        )
        decision = str(_dig(event, "decision.kind", ""))
        row["event_count"] += 1
        row["collapse_count"] += 1 if decision in EXECUTION_DECISIONS else 0
        row["suppressed_count"] += 1 if decision in SUPPRESSED_DECISIONS else 0
        row["proof_valid_count"] += 1 if _dig(event, "proof.valid") is True else 0
        row["rules"].update(str(rule) for rule in _dig(event, "heuristics.rules", []) or [] if str(rule))
    normalized = []
    for row in rows.values():
        normalized.append(
            {
                "scope": row["scope"],
                "entity_id": row["entity_id"],
                "entity_type": row["entity_type"],
                "event_count": row["event_count"],
                "collapse_count": row["collapse_count"],
                "suppressed_count": row["suppressed_count"],
                "suppression_ratio": _ratio(row["suppressed_count"], row["event_count"]),
                "proof_coverage": _ratio(row["proof_valid_count"], row["event_count"]),
                "top_rules": _top(row["rules"], 5),
            }
        )
    return sorted(normalized, key=lambda item: (-item["event_count"], item["scope"], item["entity_id"]))


def _rule_rows(events: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for scope, event in events:
        decision = str(_dig(event, "decision.kind", ""))
        proof_valid = _dig(event, "proof.valid") is True
        for rule in [str(item) for item in _dig(event, "heuristics.rules", []) or [] if str(item)]:
            row = rows.setdefault(
                rule,
                {
                    "rule": rule,
                    "edge_count": 0,
                    "collapse_edges": 0,
                    "suppressed_edges": 0,
                    "proof_edges": 0,
                    "scopes": Counter(),
                    "entities": Counter(),
                },
            )
            row["edge_count"] += 1
            row["collapse_edges"] += 1 if decision in EXECUTION_DECISIONS else 0
            row["suppressed_edges"] += 1 if decision in SUPPRESSED_DECISIONS else 0
            row["proof_edges"] += 1 if proof_valid else 0
            row["scopes"][scope] += 1
            row["entities"][str(event.get("entity_id") or "")] += 1
    normalized = []
    for row in rows.values():
        normalized.append(
            {
                "rule": row["rule"],
                "edge_count": row["edge_count"],
                "collapse_edges": row["collapse_edges"],
                "suppressed_edges": row["suppressed_edges"],
                "suppression_ratio": _ratio(row["suppressed_edges"], row["edge_count"]),
                "proof_coverage": _ratio(row["proof_edges"], row["edge_count"]),
                "scope_mix": _top(row["scopes"], 5),
                "top_entities": _top(row["entities"], 5),
            }
        )
    return sorted(normalized, key=lambda item: (-item["edge_count"], item["rule"]))


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    source_checks = _source_checks(reports)

    all_events: list[tuple[str, dict[str, Any]]] = []
    parse_errors: list[dict[str, Any]] = []
    scope_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    suppressed_proof_failures: list[dict[str, Any]] = []
    projected_suppressed_events: list[str] = []
    strict_threshold_violations: list[dict[str, Any]] = []

    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            all_events.append((scope, event))
            scope_counts[scope] += 1
            decision = str(_dig(event, "decision.kind", ""))
            decision_counts[decision] += 1
            if decision in SUPPRESSED_DECISIONS:
                proof_hash = str(_dig(event, "proof.proof_hash", ""))
                if _dig(event, "proof.valid") is not True or not proof_hash.startswith("sha256:"):
                    suppressed_proof_failures.append({"scope": scope, "event_id": event.get("event_id"), "proof_hash": proof_hash})
                if _dig(event, "proof.projection") is True:
                    projected_suppressed_events.append(str(event.get("event_id") or ""))
            if scope in {"native", "runtime_r3"}:
                gate_delta = _num(_dig(event, "tension.gate_delta"), default=999999.0)
                if decision in SUPPRESSED_DECISIONS and gate_delta >= 0:
                    strict_threshold_violations.append({"scope": scope, "event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})
                if decision in EXECUTION_DECISIONS and gate_delta < 0:
                    strict_threshold_violations.append({"scope": scope, "event_id": event.get("event_id"), "decision": decision, "gate_delta": gate_delta})

    event_count = len(all_events)
    collapse_count = decision_counts.get("collapse", 0)
    suppressed_count = sum(decision_counts.get(kind, 0) for kind in SUPPRESSED_DECISIONS)
    prove_count = decision_counts.get("prove", 0)
    baseline_event_action_count = event_count
    observed_required_action_count = collapse_count + prove_count
    avoided_action_count = suppressed_count
    avoided_action_ratio = _ratio(avoided_action_count, baseline_event_action_count)
    causal_execution_ratio = _ratio(collapse_count, event_count)
    proof_only_ratio = _ratio(prove_count, event_count)
    entity_rows = _entity_rows(all_events)
    rule_rows = _rule_rows(all_events)

    no_tick = reports["no_tick_contract"]
    identity = reports["event_identity"]
    mesh = reports["causal_mesh"]
    heuristic = reports["heuristic_weight"]
    capability = reports["entity_capability"]
    growth = reports["runtime_growth_budget"]
    negative = reports["negative_controls"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]
    budget = growth.get("budget_policy", {})

    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hashes["release_verifier_recomputed"] = verifier.get("recomputed_root_release_hash")
    root_hash_set = {value for value in root_hashes.values() if value}

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "event_streams_parse_and_match_root",
            not parse_errors
            and event_count == no_tick.get("event_count") == identity.get("event_count") == mesh.get("event_count") == 589,
            {"parse_errors": parse_errors, "scope_counts": dict(scope_counts), "event_count": event_count},
        ),
        _check(
            "suppression_gain_matches_no_tick",
            suppressed_count == no_tick.get("suppressed_count") == mesh.get("suppressed_count") == 285
            and collapse_count == no_tick.get("collapse_count") == 303
            and prove_count == no_tick.get("prove_count") == 1
            and avoided_action_ratio == no_tick.get("suppression_ratio") == mesh.get("suppression_ratio"),
            {
                "decision_counts": dict(decision_counts),
                "baseline_event_action_count": baseline_event_action_count,
                "observed_required_action_count": observed_required_action_count,
                "avoided_action_count": avoided_action_count,
                "avoided_action_ratio": avoided_action_ratio,
            },
        ),
        _check(
            "suppressed_actions_are_proof_backed",
            not suppressed_proof_failures
            and not projected_suppressed_events
            and no_tick.get("proof_valid_count") == event_count,
            {
                "suppressed_proof_failures": suppressed_proof_failures[:10],
                "projected_suppressed_event_count": len(projected_suppressed_events),
                "proof_valid_count": no_tick.get("proof_valid_count"),
            },
        ),
        _check(
            "strict_native_r3_threshold_gain_clean",
            not strict_threshold_violations
            and no_tick.get("strict_threshold_violation_count") == 0
            and identity.get("native_count") == 77,
            {
                "strict_threshold_violations": strict_threshold_violations[:10],
                "strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
                "native_count": identity.get("native_count"),
            },
        ),
        _check(
            "entity_efficiency_attribution_complete",
            len(entity_rows) == identity.get("entity_binding_count") == mesh.get("entity_count") == capability.get("entity_row_count") == 13
            and mesh.get("unknown_entity_count") == 0,
            {
                "entity_row_count": len(entity_rows),
                "unknown_entity_count": mesh.get("unknown_entity_count"),
                "top_entities_by_event_count": entity_rows[:8],
            },
        ),
        _check(
            "heuristic_efficiency_attribution_complete",
            len(rule_rows) == identity.get("rule_count") == mesh.get("rule_count") == heuristic.get("rule_count") == 9
            and sum(row["edge_count"] for row in rule_rows) == identity.get("rule_event_edge_count") == mesh.get("rule_event_edge_count") == heuristic.get("total_rule_edge_count") == 1350
            and heuristic.get("proof_complete") is True
            and heuristic.get("projection_clean") is True,
            {
                "rule_row_count": len(rule_rows),
                "rule_event_edge_count": sum(row["edge_count"] for row in rule_rows),
                "top_rules_by_edge_count": rule_rows[:8],
            },
        ),
        _check(
            "growth_and_negative_controls_preserve_efficiency",
            budget.get("growth_mode") == "SMALL_BATCH_RESTRICTED"
            and budget.get("min_suppression_ratio") <= avoided_action_ratio <= budget.get("max_suppression_ratio")
            and negative.get("detected_count") == negative.get("control_count") == 8
            and negative.get("undetected_count") == 0,
            {
                "avoided_action_ratio": avoided_action_ratio,
                "budget_policy": budget,
                "negative_controls": {
                    "control_count": negative.get("control_count"),
                    "detected_count": negative.get("detected_count"),
                    "undetected_count": negative.get("undetected_count"),
                },
            },
        ),
        _check(
            "public_boundaries_and_root_hash_stable",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and root_hash_set == {ROOT_RELEASE_HASH}
            and verifier.get("root_release_hash") == ROOT_RELEASE_HASH
            and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {
                "path_leak_count": publication.get("path_leak_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
                "root_hashes": root_hashes,
            },
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_READY" if not failures else "PNVA_ROOT_EFFICIENCY_PROOF_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "event_count": event_count,
        "avoided_action_count": avoided_action_count,
        "avoided_action_ratio": avoided_action_ratio,
        "entity_row_count": len(entity_rows),
        "rule_row_count": len(rule_rows),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_efficiency_proof_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "efficiency_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": event_count,
        "baseline_event_action_count": baseline_event_action_count,
        "collapse_count": collapse_count,
        "suppressed_count": suppressed_count,
        "prove_count": prove_count,
        "observed_required_action_count": observed_required_action_count,
        "avoided_action_count": avoided_action_count,
        "avoided_action_ratio": avoided_action_ratio,
        "causal_execution_ratio": causal_execution_ratio,
        "proof_only_ratio": proof_only_ratio,
        "entity_row_count": len(entity_rows),
        "rule_row_count": len(rule_rows),
        "rule_event_edge_count": sum(row["edge_count"] for row in rule_rows),
        "native_count": identity.get("native_count"),
        "projected_event_count": identity.get("projected_event_count"),
        "strict_threshold_violation_count": len(strict_threshold_violations),
        "suppressed_proof_failure_count": len(suppressed_proof_failures),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "efficiency_proof_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "entity_efficiency_rows": entity_rows,
        "heuristic_efficiency_rows": rule_rows,
        "interpretation": {
            "purpose": "Quantify PNVA no-tick efficiency as proof-backed causal non-execution against a public event baseline.",
            "sovereignty": "Efficiency is accepted only when avoided actions are linked to event identity, proof identity, entity rows, heuristic rules and public boundaries.",
            "boundary": "This ledger estimates avoided event actions from public proof logs. It does not claim universal speedup, hardware counters or private deployment performance.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root efficiency proof ledger.")
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
