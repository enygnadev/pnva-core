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

REPORTS = {
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "evolution_governor": "reports/pnva-root-evolution-governor-2026-05-05.json",
    "theorem_ledger": "reports/pnva-root-proof-theorem-ledger-2026-05-05.json",
    "traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "theorem_ledger": "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY",
    "traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
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


def _proof(event: dict[str, Any]) -> dict[str, Any]:
    proof = event.get("proof")
    return proof if isinstance(proof, dict) else {}


def _rules(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    rules = heuristics.get("rules")
    if not isinstance(rules, list):
        return []
    return [str(rule) for rule in rules if str(rule)]


def _classification_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "classification": reports[name].get("classification"),
            "expected": expected,
            "pass": reports[name].get("classification") == expected and reports[name].get("pass") is True,
        }
        for name, expected in EXPECTED_CLASSIFICATIONS.items()
    ]


def _counter_pairs(counter: Counter[str], limit: int = 12) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def _edge_profile(scope: str, entity_key: str, rule: str) -> dict[str, Any]:
    return {
        "edge_id": f"{entity_key}->{rule}",
        "scope": scope,
        "entity_key": entity_key,
        "rule": rule,
        "event_count": 0,
        "proof_valid_count": 0,
        "native_count": 0,
        "projected_count": 0,
        "suppressed_count": 0,
        "collapse_count": 0,
        "observe_count": 0,
        "block_count": 0,
        "prove_count": 0,
        "decision_mix": Counter(),
    }


def _finalize_edge(edge: dict[str, Any], entity_status: str, rule_status: str) -> dict[str, Any]:
    event_count = int(edge["event_count"])
    suppressed_count = int(edge["suppressed_count"])
    projected_count = int(edge["projected_count"])
    proof_valid_count = int(edge["proof_valid_count"])
    if projected_count > 0 or proof_valid_count != event_count:
        topology_status = "BLOCKED"
    elif entity_status == "R3_RUNTIME_READY":
        topology_status = "R3_READY_EDGE"
    elif entity_status == "NATIVE_READY":
        topology_status = "NATIVE_READY_EDGE"
    elif rule_status == "CONTROLLED_LEGACY":
        topology_status = "CONTROLLED_LEGACY_EDGE"
    else:
        topology_status = "CONTROLLED_CANONICAL_EDGE"
    return {
        "edge_id": edge["edge_id"],
        "scope": edge["scope"],
        "entity_key": edge["entity_key"],
        "rule": edge["rule"],
        "entity_status": entity_status,
        "rule_status": rule_status,
        "topology_status": topology_status,
        "event_count": event_count,
        "proof_valid_count": proof_valid_count,
        "native_count": int(edge["native_count"]),
        "projected_count": projected_count,
        "suppressed_count": suppressed_count,
        "collapse_count": int(edge["collapse_count"]),
        "observe_count": int(edge["observe_count"]),
        "block_count": int(edge["block_count"]),
        "prove_count": int(edge["prove_count"]),
        "suppression_ratio": _ratio(suppressed_count, event_count),
        "proof_coverage": _ratio(proof_valid_count, event_count),
        "decision_mix": _counter_pairs(edge["decision_mix"]),
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    entity_report = reports["entity_capability"]
    heuristic_report = reports["heuristic_weight"]
    obs = reports["observability"]
    governor = reports["evolution_governor"]
    theorem = reports["theorem_ledger"]
    traceability = reports["traceability"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    entity_status = {row["ledger_key"]: row["governance_status"] for row in entity_report.get("entities", [])}
    rule_status = {row["rule"]: row["governance_status"] for row in heuristic_report.get("rules", [])}
    parse_errors: list[dict[str, Any]] = []
    entity_rule_edges: dict[tuple[str, str], dict[str, Any]] = {}
    entity_decision_edges: Counter[tuple[str, str]] = Counter()
    rule_decision_edges: Counter[tuple[str, str]] = Counter()
    scope_event_counts: Counter[str] = Counter()
    entity_event_counts: Counter[str] = Counter()
    unruled_event_count = 0
    unknown_entity_event_count = 0
    total_event_count = 0
    total_rule_edge_count = 0

    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            total_event_count += 1
            scope_event_counts[scope] += 1
            entity_key = f"{scope}:{event.get('entity_id')}"
            if entity_key not in entity_status:
                unknown_entity_event_count += 1
                continue
            entity_event_counts[entity_key] += 1
            decision = _decision(event)
            entity_decision_edges[(entity_key, decision)] += 1
            rules = _rules(event)
            if not rules:
                unruled_event_count += 1
            proof = _proof(event)
            for rule in rules:
                total_rule_edge_count += 1
                rule_decision_edges[(rule, decision)] += 1
                key = (entity_key, rule)
                edge = entity_rule_edges.setdefault(key, _edge_profile(scope, entity_key, rule))
                edge["event_count"] += 1
                edge["decision_mix"].update([decision])
                if proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:"):
                    edge["proof_valid_count"] += 1
                if proof.get("native") is True:
                    edge["native_count"] += 1
                if proof.get("projection") is True:
                    edge["projected_count"] += 1
                if decision in {"observe", "block"} or _dig(event, "decision.action") == "NO_ACTION":
                    edge["suppressed_count"] += 1
                if decision == "collapse":
                    edge["collapse_count"] += 1
                if decision == "observe":
                    edge["observe_count"] += 1
                if decision == "block":
                    edge["block_count"] += 1
                if decision == "prove":
                    edge["prove_count"] += 1

    finalized_edges = [
        _finalize_edge(edge, entity_status.get(edge["entity_key"], "UNKNOWN"), rule_status.get(edge["rule"], "UNKNOWN"))
        for edge in entity_rule_edges.values()
    ]
    finalized_edges = sorted(finalized_edges, key=lambda item: (-item["event_count"], item["edge_id"]))
    blocked_edges = [edge for edge in finalized_edges if edge["topology_status"] == "BLOCKED"]
    r3_edges = [edge for edge in finalized_edges if edge["scope"] == "runtime_r3"]
    legacy_edges = [edge for edge in finalized_edges if edge["rule"] == "legacy_observer"]
    legacy_r3_leaks = [edge for edge in legacy_edges if edge["scope"] == "runtime_r3"]
    legacy_native_context = [edge for edge in legacy_edges if edge["scope"] == "native"]
    entity_with_rule_edges = {edge["entity_key"] for edge in finalized_edges}
    rule_with_entity_edges = {edge["rule"] for edge in finalized_edges}
    orphan_entities = sorted(set(entity_status) - entity_with_rule_edges)
    orphan_rules = sorted(set(rule_status) - rule_with_entity_edges)
    edge_status_counts = Counter(edge["topology_status"] for edge in finalized_edges)

    classification_checks = _classification_checks(reports)
    expected_event_count = int(obs.get("no_tick_observability", {}).get("aggregate_event_count", 0))
    expected_rule_edges = int(heuristic_report.get("total_rule_edge_count", 0))
    checks = [
        {
            "name": "source_classifications_ready",
            "pass": all(item["pass"] for item in classification_checks),
            "evidence": {"failures": [item for item in classification_checks if not item["pass"]]},
        },
        {
            "name": "node_counts_ready",
            "pass": len(entity_status) == 13 and len(rule_status) == 9,
            "evidence": {"entity_node_count": len(entity_status), "rule_node_count": len(rule_status)},
        },
        {
            "name": "event_and_rule_edge_coverage_complete",
            "pass": total_event_count == expected_event_count == entity_report.get("profile_event_count") and total_rule_edge_count == expected_rule_edges,
            "evidence": {
                "topology_event_count": total_event_count,
                "observability_event_count": expected_event_count,
                "entity_profile_event_count": entity_report.get("profile_event_count"),
                "topology_rule_edge_count": total_rule_edge_count,
                "heuristic_weight_rule_edge_count": expected_rule_edges,
            },
        },
        {
            "name": "entity_rule_topology_present",
            "pass": bool(finalized_edges) and not orphan_entities and not orphan_rules,
            "evidence": {"entity_rule_edge_count": len(finalized_edges), "orphan_entities": orphan_entities, "orphan_rules": orphan_rules},
        },
        {
            "name": "proof_and_projection_clean",
            "pass": not blocked_edges,
            "evidence": {"blocked_edge_count": len(blocked_edges), "blocked_edges": [edge["edge_id"] for edge in blocked_edges[:20]]},
        },
        {
            "name": "runtime_r3_topology_attached",
            "pass": len(r3_edges) >= 4 and all(edge["topology_status"] == "R3_READY_EDGE" for edge in r3_edges),
            "evidence": {"r3_edge_count": len(r3_edges), "r3_rules": sorted({edge["rule"] for edge in r3_edges})},
        },
        {
            "name": "controlled_legacy_bounded",
            "pass": bool(legacy_edges) and not legacy_r3_leaks and all(edge["projected_count"] == 0 for edge in legacy_edges),
            "evidence": {
                "legacy_edge_count": len(legacy_edges),
                "legacy_native_context_count": len(legacy_native_context),
                "legacy_r3_leak_count": len(legacy_r3_leaks),
            },
        },
        {
            "name": "unruled_and_unknown_events_absent",
            "pass": unruled_event_count == 0 and unknown_entity_event_count == 0,
            "evidence": {"unruled_event_count": unruled_event_count, "unknown_entity_event_count": unknown_entity_event_count},
        },
        {
            "name": "governor_and_theorems_intact",
            "pass": governor.get("invariant_failure_count") == 0 and theorem.get("failed_theorem_count") == 0,
            "evidence": {"invariant_failure_count": governor.get("invariant_failure_count"), "failed_theorem_count": theorem.get("failed_theorem_count")},
        },
        {
            "name": "traceability_ready",
            "pass": traceability.get("root_traceability_score") == 100.0 and traceability.get("failure_count") == 0,
            "evidence": {"root_traceability_score": traceability.get("root_traceability_score"), "failure_count": traceability.get("failure_count")},
        },
        {
            "name": "public_boundaries_clean",
            "pass": claim.get("unbounded_high_risk_occurrence_count") == 0 and publication.get("path_leak_count") == 0,
            "evidence": {"unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"), "path_leak_count": publication.get("path_leak_count")},
        },
        {
            "name": "root_hash_stable",
            "pass": verifier.get("root_release_hash") == ROOT_RELEASE_HASH and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            "evidence": {"root_release_hash": verifier.get("root_release_hash"), "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash")},
        },
        {
            "name": "parse_clean",
            "pass": not parse_errors,
            "evidence": {"parse_error_count": len(parse_errors), "parse_errors": parse_errors[:10]},
        },
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY" if not failures else "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_FAIL"
    topology_seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "edge_status_counts": dict(sorted(edge_status_counts.items())),
        "entity_rule_edges": [
            {
                "edge_id": edge["edge_id"],
                "topology_status": edge["topology_status"],
                "event_count": edge["event_count"],
                "projected_count": edge["projected_count"],
            }
            for edge in finalized_edges
        ],
    }
    possible_entity_rule_edges = max(1, len(entity_status) * len(rule_status))
    return {
        "schema_version": "pnva.root_field_topology_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "field_topology_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "entity_node_count": len(entity_status),
        "rule_node_count": len(rule_status),
        "event_count": total_event_count,
        "rule_event_edge_count": total_rule_edge_count,
        "entity_rule_edge_count": len(finalized_edges),
        "entity_decision_edge_count": len(entity_decision_edges),
        "rule_decision_edge_count": len(rule_decision_edges),
        "topology_density": _ratio(len(finalized_edges), possible_entity_rule_edges),
        "r3_edge_count": len(r3_edges),
        "legacy_edge_count": len(legacy_edges),
        "blocked_edge_count": len(blocked_edges),
        "orphan_entity_count": len(orphan_entities),
        "orphan_rule_count": len(orphan_rules),
        "unruled_event_count": unruled_event_count,
        "unknown_entity_event_count": unknown_entity_event_count,
        "root_release_hash": ROOT_RELEASE_HASH,
        "field_topology_ledger_hash": _sha_text(json.dumps(topology_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": classification_checks,
        "edge_status_counts": dict(sorted(edge_status_counts.items())),
        "scope_event_counts": dict(sorted(scope_event_counts.items())),
        "top_entity_event_counts": _counter_pairs(entity_event_counts, 20),
        "top_entity_rule_edges": finalized_edges[:30],
        "entity_decision_edges": [
            {"entity_key": entity, "decision": decision, "event_count": count}
            for (entity, decision), count in sorted(entity_decision_edges.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        ],
        "rule_decision_edges": [
            {"rule": rule, "decision": decision, "event_count": count}
            for (rule, decision), count in sorted(rule_decision_edges.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))
        ],
        "interpretation": {
            "purpose": "Expose the root PNVA field topology across entities, heuristic rules and no-tick decisions.",
            "sovereignty": "A root field becomes governable when entity-rule-decision relations are visible, projection-free and bounded by proof.",
            "boundary": "This ledger is an audit graph over public evidence. It does not execute system actions, change live gates or claim external deployment behavior.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root field topology ledger.")
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
