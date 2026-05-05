#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
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
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "runtime_admission": "reports/pnva-root-runtime-admission-controller-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "runtime_admission": "PNVA_ROOT_RUNTIME_ADMISSION_READY",
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


def _edge_template(scope: str, entity_key: str, rule: str) -> dict[str, Any]:
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


def _admission_status(edge: dict[str, Any], entity_status: str, rule_status: str, allowed_modes: set[str]) -> str:
    if edge["projected_count"] > 0 or edge["proof_valid_count"] != edge["event_count"]:
        return "DENY_EDGE"
    if entity_status == "R3_RUNTIME_READY" and rule_status == "PUBLIC_WEIGHT_READY" and "restricted_r3_precheck_commit" in allowed_modes:
        return "ADMIT_R3_RESTRICTED"
    if entity_status == "NATIVE_READY" and rule_status == "PUBLIC_WEIGHT_READY" and "restricted_native_event_ingest" in allowed_modes:
        return "ADMIT_NATIVE_RESTRICTED"
    if entity_status == "NATIVE_READY" and rule_status == "CONTROLLED_LEGACY":
        return "OBSERVE_NATIVE_LEGACY_ONLY"
    if rule_status == "CONTROLLED_LEGACY":
        return "BOUND_CANONICAL_LEGACY"
    if entity_status == "CONTROLLED_CANONICAL" and rule_status == "PUBLIC_WEIGHT_READY":
        return "CONTROLLED_CANONICAL_EVIDENCE"
    return "DENY_EDGE"


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


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    entity_report = reports["entity_capability"]
    heuristic_report = reports["heuristic_weight"]
    topology = reports["field_topology"]
    no_tick = reports["no_tick_contract"]
    admission = reports["runtime_admission"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    entity_status = {str(row.get("ledger_key")): str(row.get("governance_status")) for row in entity_report.get("entities", [])}
    entity_readiness = {str(row.get("ledger_key")): float(row.get("readiness_score", 0.0)) for row in entity_report.get("entities", [])}
    rule_status = {str(row.get("rule")): str(row.get("governance_status")) for row in heuristic_report.get("rules", [])}
    rule_weight = {str(row.get("rule")): float(row.get("public_weight", 0.0)) for row in heuristic_report.get("rules", [])}
    allowed_modes = set(str(item) for item in admission.get("allowed_modes", []))

    parse_errors: list[dict[str, Any]] = []
    unknown_entities: list[dict[str, Any]] = []
    unknown_rules: list[dict[str, Any]] = []
    edges: dict[tuple[str, str], dict[str, Any]] = {}
    total_event_count = 0
    total_rule_event_count = 0

    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            total_event_count += 1
            entity_key = f"{scope}:{event.get('entity_id')}"
            if entity_key not in entity_status:
                unknown_entities.append({"scope": scope, "event_id": event.get("event_id"), "entity_key": entity_key})
                continue
            rules = _rules(event)
            if not rules:
                unknown_rules.append({"scope": scope, "event_id": event.get("event_id"), "rule": "missing"})
                continue
            proof = _proof(event)
            decision = _decision(event)
            for rule in rules:
                if rule not in rule_status:
                    unknown_rules.append({"scope": scope, "event_id": event.get("event_id"), "rule": rule})
                    continue
                total_rule_event_count += 1
                edge = edges.setdefault((entity_key, rule), _edge_template(scope, entity_key, rule))
                edge["event_count"] += 1
                edge["decision_mix"].update([decision])
                if decision in {"observe", "block"}:
                    edge["suppressed_count"] += 1
                if decision == "collapse":
                    edge["collapse_count"] += 1
                if decision == "observe":
                    edge["observe_count"] += 1
                if decision == "block":
                    edge["block_count"] += 1
                if decision == "prove":
                    edge["prove_count"] += 1
                if proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:"):
                    edge["proof_valid_count"] += 1
                if proof.get("native") is True:
                    edge["native_count"] += 1
                if proof.get("projection") is True:
                    edge["projected_count"] += 1

    rows: list[dict[str, Any]] = []
    for (entity_key, rule), edge in sorted(edges.items()):
        e_status = entity_status.get(entity_key, "UNKNOWN_ENTITY")
        r_status = rule_status.get(rule, "UNKNOWN_RULE")
        status = _admission_status(edge, e_status, r_status, allowed_modes)
        event_count = int(edge["event_count"])
        suppressed_count = int(edge["suppressed_count"])
        readiness = entity_readiness.get(entity_key, 0.0)
        weight = rule_weight.get(rule, 0.0)
        rows.append(
            {
                "edge_id": edge["edge_id"],
                "scope": edge["scope"],
                "entity_key": entity_key,
                "rule": rule,
                "entity_status": e_status,
                "rule_status": r_status,
                "admission_status": status,
                "event_count": event_count,
                "proof_valid_count": int(edge["proof_valid_count"]),
                "proof_coverage": _ratio(edge["proof_valid_count"], event_count),
                "native_count": int(edge["native_count"]),
                "projected_count": int(edge["projected_count"]),
                "suppressed_count": suppressed_count,
                "suppression_ratio": _ratio(suppressed_count, event_count),
                "collapse_count": int(edge["collapse_count"]),
                "observe_count": int(edge["observe_count"]),
                "block_count": int(edge["block_count"]),
                "prove_count": int(edge["prove_count"]),
                "entity_readiness_score": readiness,
                "rule_public_weight": weight,
                "admission_weight": round(readiness * weight * _ratio(edge["proof_valid_count"], event_count), 6),
                "decision_mix": _counter_pairs(edge["decision_mix"]),
            }
        )

    status_counts = Counter(row["admission_status"] for row in rows)
    denied_edges = [row for row in rows if row["admission_status"] == "DENY_EDGE"]
    r3_edges = [row for row in rows if row["admission_status"] == "ADMIT_R3_RESTRICTED"]
    native_edges = [row for row in rows if row["admission_status"] == "ADMIT_NATIVE_RESTRICTED"]
    legacy_edges = [row for row in rows if row["admission_status"] in {"BOUND_CANONICAL_LEGACY", "OBSERVE_NATIVE_LEGACY_ONLY"}]
    controlled_edges = [row for row in rows if row["admission_status"] == "CONTROLLED_CANONICAL_EVIDENCE"]
    source_checks = _classification_checks(reports)

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check("parse_clean", not parse_errors, {"parse_error_count": len(parse_errors), "parse_errors": parse_errors[:10]}),
        _check(
            "event_and_rule_edge_counts_match_root",
            total_event_count == topology.get("event_count") == no_tick.get("event_count")
            and total_rule_event_count == topology.get("rule_event_edge_count") == heuristic_report.get("total_rule_edge_count"),
            {
                "event_count": total_event_count,
                "topology_event_count": topology.get("event_count"),
                "contract_event_count": no_tick.get("event_count"),
                "rule_event_edge_count": total_rule_event_count,
                "topology_rule_event_edge_count": topology.get("rule_event_edge_count"),
                "heuristic_rule_event_edge_count": heuristic_report.get("total_rule_edge_count"),
            },
        ),
        _check(
            "entity_rule_matrix_complete",
            len(rows) == topology.get("entity_rule_edge_count") and not unknown_entities and not unknown_rules,
            {
                "matrix_edge_count": len(rows),
                "topology_entity_rule_edge_count": topology.get("entity_rule_edge_count"),
                "unknown_entity_count": len(unknown_entities),
                "unknown_rule_count": len(unknown_rules),
                "unknown_entities": unknown_entities[:20],
                "unknown_rules": unknown_rules[:20],
            },
        ),
        _check(
            "runtime_edges_admitted_restricted",
            len(r3_edges) >= 4 and len(native_edges) >= 12 and all(row["projected_count"] == 0 for row in r3_edges + native_edges),
            {"r3_restricted_edge_count": len(r3_edges), "native_restricted_edge_count": len(native_edges), "projected_runtime_edge_count": sum(1 for row in r3_edges + native_edges if row["projected_count"] > 0)},
        ),
        _check(
            "legacy_edges_bounded",
            len(legacy_edges) == topology.get("legacy_edge_count") and all(row["projected_count"] == 0 for row in legacy_edges),
            {"legacy_edge_count": len(legacy_edges), "topology_legacy_edge_count": topology.get("legacy_edge_count"), "legacy_projection_count": sum(row["projected_count"] for row in legacy_edges)},
        ),
        _check(
            "no_denied_or_uncovered_edges",
            not denied_edges and all(row["proof_coverage"] == 1.0 for row in rows),
            {"denied_edge_count": len(denied_edges), "denied_edges": [row["edge_id"] for row in denied_edges[:20]], "uncovered_edge_count": sum(1 for row in rows if row["proof_coverage"] != 1.0)},
        ),
        _check(
            "controlled_canonical_edges_remain_evidence_only",
            len(controlled_edges) >= 17 and all(row["scope"] == "canonical" for row in controlled_edges),
            {"controlled_canonical_edge_count": len(controlled_edges), "noncanonical_controlled_count": sum(1 for row in controlled_edges if row["scope"] != "canonical")},
        ),
        _check(
            "runtime_admission_modes_enforced",
            admission.get("admission_decision") == "ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING"
            and "restricted_native_event_ingest" in allowed_modes
            and "restricted_r3_precheck_commit" in allowed_modes,
            {"admission_decision": admission.get("admission_decision"), "allowed_modes": admission.get("allowed_modes"), "denied_modes": admission.get("denied_modes")},
        ),
        _check(
            "public_boundary_clean",
            publication.get("path_leak_count") == 0 and claim.get("unbounded_high_risk_occurrence_count") == 0,
            {"path_leak_count": publication.get("path_leak_count"), "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count")},
        ),
        _check(
            "root_hash_stable",
            verifier.get("root_release_hash") == ROOT_RELEASE_HASH and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_release_hash": verifier.get("root_release_hash"), "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash")},
        ),
    ]

    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY" if not failures else "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_FAIL"
    matrix_seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "status_counts": dict(sorted(status_counts.items())),
        "edge_count": len(rows),
        "rule_event_edge_count": total_rule_event_count,
    }

    return {
        "schema_version": "pnva.root_entity_heuristic_admission_matrix.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "admission_matrix_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": total_event_count,
        "rule_event_edge_count": total_rule_event_count,
        "entity_rule_edge_count": len(rows),
        "admitted_r3_edge_count": len(r3_edges),
        "admitted_native_edge_count": len(native_edges),
        "controlled_canonical_edge_count": len(controlled_edges),
        "bounded_legacy_edge_count": len(legacy_edges),
        "denied_edge_count": len(denied_edges),
        "unknown_entity_count": len(unknown_entities),
        "unknown_rule_count": len(unknown_rules),
        "status_counts": dict(sorted(status_counts.items())),
        "root_release_hash": ROOT_RELEASE_HASH,
        "entity_heuristic_admission_matrix_hash": _sha_text(json.dumps(matrix_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "top_edges_by_admission_weight": sorted(rows, key=lambda row: (-row["admission_weight"], -row["event_count"], row["edge_id"]))[:20],
        "admission_rows": rows,
        "interpretation": {
            "purpose": "Map every entity-rule edge into an explicit admission class for future PNVA runtime evidence.",
            "sovereignty": "Entity and heuristic growth is safe only when each edge has a status, proof coverage and a bounded runtime mode.",
            "boundary": "This matrix audits public evidence only. It does not execute runtime actions or change live gates.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root entity-heuristic admission matrix.")
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
