#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

REPORTS = {
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "admission_matrix": "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json",
    "runtime_admission": "reports/pnva-root-runtime-admission-controller-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "growth_budget": "reports/pnva-root-runtime-growth-budget-2026-05-05.json",
    "negative_controls": "reports/pnva-root-admission-negative-controls-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "admission_matrix": "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY",
    "runtime_admission": "PNVA_ROOT_RUNTIME_ADMISSION_READY",
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "growth_budget": "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY",
    "negative_controls": "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _same_number(values: dict[str, Any], *, tolerance: float = 0.0) -> bool:
    numbers = [_num(value) for value in values.values()]
    if not numbers:
        return False
    base = numbers[0]
    return all(abs(value - base) <= tolerance for value in numbers)


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


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    no_tick = reports["no_tick_contract"]
    topology = reports["field_topology"]
    capability = reports["entity_capability"]
    heuristic = reports["heuristic_weight"]
    matrix = reports["admission_matrix"]
    runtime = reports["runtime_admission"]
    observability = reports["observability"]
    intelligence = reports["causal_intelligence"]
    growth = reports["growth_budget"]
    negative = reports["negative_controls"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    source_checks = _source_checks(reports)

    event_counts = {
        "no_tick_contract": no_tick.get("event_count"),
        "field_topology": topology.get("event_count"),
        "admission_matrix": matrix.get("event_count"),
        "runtime_admission": runtime.get("event_count"),
        "observability": _dig(observability, "no_tick_observability.aggregate_event_count"),
        "causal_intelligence": _dig(intelligence, "no_tick_aggregate.event_count"),
        "growth_budget": growth.get("event_count"),
    }
    suppressed_counts = {
        "no_tick_contract": no_tick.get("suppressed_count"),
        "runtime_admission": runtime.get("suppressed_count"),
        "observability": _dig(observability, "no_tick_observability.aggregate_suppressed_count"),
        "causal_intelligence": _dig(intelligence, "no_tick_aggregate.suppressed_count"),
        "growth_budget": growth.get("suppressed_count"),
    }
    suppression_ratios = {
        "no_tick_contract": no_tick.get("suppression_ratio"),
        "runtime_admission": runtime.get("suppression_ratio"),
        "observability": _dig(observability, "no_tick_observability.aggregate_suppression_ratio"),
        "causal_intelligence": _dig(intelligence, "no_tick_aggregate.suppression_ratio"),
        "growth_budget": growth.get("suppression_ratio"),
    }
    decision_counts = {
        "collapse": {
            "no_tick_contract": no_tick.get("collapse_count"),
            "observability": _dig(observability, "no_tick_observability.aggregate_collapse_count"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.collapse_count"),
        },
        "observe": {
            "no_tick_contract": no_tick.get("observe_count"),
            "observability": _dig(observability, "no_tick_observability.aggregate_observe_count"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.observe_count"),
        },
        "block": {
            "no_tick_contract": no_tick.get("block_count"),
            "observability": _dig(observability, "no_tick_observability.aggregate_block_count"),
            "causal_intelligence": _dig(intelligence, "no_tick_aggregate.block_count"),
        },
    }
    entity_counts = {
        "field_topology": topology.get("entity_node_count"),
        "entity_capability": capability.get("entity_row_count"),
        "runtime_admission": runtime.get("entity_row_count"),
        "observability": _dig(observability, "entity_observability.total_entity_rows"),
    }
    rule_counts = {
        "field_topology": topology.get("rule_node_count"),
        "heuristic_weight": heuristic.get("rule_count"),
        "runtime_admission": runtime.get("rule_count"),
        "observability": _dig(observability, "heuristic_observability.heuristic_rule_count"),
    }
    rule_event_edges = {
        "field_topology": topology.get("rule_event_edge_count"),
        "heuristic_weight": heuristic.get("total_rule_edge_count"),
        "admission_matrix": matrix.get("rule_event_edge_count"),
    }
    entity_rule_edges = {
        "field_topology": topology.get("entity_rule_edge_count"),
        "admission_matrix": matrix.get("entity_rule_edge_count"),
        "runtime_admission": runtime.get("entity_rule_edge_count"),
        "growth_budget": growth.get("entity_rule_edge_count"),
    }
    r3_counts = {
        "no_tick_contract": no_tick.get("r3_chain_count"),
        "runtime_admission": runtime.get("r3_chain_count"),
        "growth_budget": growth.get("r3_chain_count"),
        "observability_accepted_slots": _dig(observability, "runtime_observability.accepted_slot_count"),
    }
    root_hashes = {
        name: report.get("root_release_hash")
        for name, report in reports.items()
        if report.get("root_release_hash")
    }
    root_hashes["release_verifier_recomputed"] = verifier.get("recomputed_root_release_hash")
    root_hash_set = set(value for value in root_hashes.values() if value)

    budget = growth.get("budget_policy", {})
    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "no_tick_counts_mesh_agree",
            _same_number(event_counts)
            and _same_number(suppressed_counts)
            and _same_number(suppression_ratios, tolerance=0.000001)
            and all(_same_number(values) for values in decision_counts.values()),
            {
                "event_counts": event_counts,
                "suppressed_counts": suppressed_counts,
                "suppression_ratios": suppression_ratios,
                "decision_counts": decision_counts,
            },
        ),
        _check(
            "entity_counts_mesh_agree",
            _same_number(entity_counts)
            and no_tick.get("unknown_entity_count") == 0
            and topology.get("unknown_entity_event_count") == 0
            and matrix.get("unknown_entity_count") == 0,
            {
                "entity_counts": entity_counts,
                "unknown_entity_counts": {
                    "no_tick_contract": no_tick.get("unknown_entity_count"),
                    "field_topology": topology.get("unknown_entity_event_count"),
                    "admission_matrix": matrix.get("unknown_entity_count"),
                },
            },
        ),
        _check(
            "heuristic_counts_mesh_agree",
            _same_number(rule_counts)
            and _same_number(rule_event_edges)
            and heuristic.get("proof_complete") is True
            and heuristic.get("projection_clean") is True
            and _dig(observability, "heuristic_observability.heuristic_coverage_ratio") == 1.0
            and _dig(observability, "heuristic_observability.proof_event_coverage_ratio") == 1.0
            and no_tick.get("unknown_rule_count") == 0
            and matrix.get("unknown_rule_count") == 0,
            {
                "rule_counts": rule_counts,
                "rule_event_edges": rule_event_edges,
                "proof_complete": heuristic.get("proof_complete"),
                "projection_clean": heuristic.get("projection_clean"),
                "heuristic_coverage_ratio": _dig(observability, "heuristic_observability.heuristic_coverage_ratio"),
                "proof_event_coverage_ratio": _dig(observability, "heuristic_observability.proof_event_coverage_ratio"),
                "unknown_rule_counts": {
                    "no_tick_contract": no_tick.get("unknown_rule_count"),
                    "admission_matrix": matrix.get("unknown_rule_count"),
                },
            },
        ),
        _check(
            "entity_rule_admission_mesh_agree",
            _same_number(entity_rule_edges)
            and matrix.get("denied_edge_count") == 0
            and runtime.get("blocked_edge_count") == 0
            and topology.get("blocked_edge_count") == 0,
            {
                "entity_rule_edges": entity_rule_edges,
                "admission_classes": {
                    "admitted_r3_edge_count": matrix.get("admitted_r3_edge_count"),
                    "admitted_native_edge_count": matrix.get("admitted_native_edge_count"),
                    "controlled_canonical_edge_count": matrix.get("controlled_canonical_edge_count"),
                    "bounded_legacy_edge_count": matrix.get("bounded_legacy_edge_count"),
                    "denied_edge_count": matrix.get("denied_edge_count"),
                },
                "blocked_edge_counts": {
                    "runtime_admission": runtime.get("blocked_edge_count"),
                    "field_topology": topology.get("blocked_edge_count"),
                },
            },
        ),
        _check(
            "runtime_r3_mesh_agree",
            _same_number(r3_counts)
            and no_tick.get("r3_pair_failure_count") == 0
            and no_tick.get("strict_threshold_violation_count") == 0
            and _dig(observability, "runtime_observability.no_tick_pair_failure_count") == 0
            and _dig(observability, "runtime_observability.pending_slot_count") == 0
            and _dig(observability, "runtime_observability.rejected_event_count") == 0,
            {
                "r3_counts": r3_counts,
                "r3_pair_failure_count": no_tick.get("r3_pair_failure_count"),
                "strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
                "runtime_observability": observability.get("runtime_observability"),
            },
        ),
        _check(
            "proof_projection_and_negative_controls_clean",
            no_tick.get("proof_valid_count") == no_tick.get("event_count")
            and no_tick.get("projection_event_count") == 0
            and capability.get("proof_complete") is True
            and capability.get("projection_clean") is True
            and negative.get("detected_count") == negative.get("control_count")
            and negative.get("undetected_count") == 0,
            {
                "proof_valid_count": no_tick.get("proof_valid_count"),
                "event_count": no_tick.get("event_count"),
                "projection_event_count": no_tick.get("projection_event_count"),
                "entity_proof_complete": capability.get("proof_complete"),
                "entity_projection_clean": capability.get("projection_clean"),
                "negative_controls": {
                    "control_count": negative.get("control_count"),
                    "detected_count": negative.get("detected_count"),
                    "undetected_count": negative.get("undetected_count"),
                },
            },
        ),
        _check(
            "public_boundary_mesh_closed",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and publication.get("checksum_count", 0) > 0
            and publication.get("manifest_file_count", 0) > publication.get("checksum_count", 0),
            {
                "manifest_file_count": publication.get("manifest_file_count"),
                "checksum_count": publication.get("checksum_count"),
                "path_leak_count": publication.get("path_leak_count"),
                "scanned_file_count": claim.get("scanned_file_count"),
                "high_risk_occurrence_count": claim.get("high_risk_occurrence_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
            },
        ),
        _check(
            "growth_budget_mesh_applied",
            budget.get("growth_mode") == "SMALL_BATCH_RESTRICTED"
            and budget.get("max_new_events_per_batch", 0) > 0
            and budget.get("max_new_r3_chains_per_batch", 0) > 0
            and budget.get("max_new_entity_rule_edges_per_batch", 0) > 0
            and budget.get("max_denied_edges") == 0
            and budget.get("max_unknown_entities") == 0
            and budget.get("max_unknown_rules") == 0
            and budget.get("max_projected_events") == 0
            and budget.get("min_suppression_ratio") <= no_tick.get("suppression_ratio", 0) <= budget.get("max_suppression_ratio"),
            budget,
        ),
        _check(
            "root_release_hash_mesh_aligned",
            root_hash_set == {ROOT_RELEASE_HASH}
            and verifier.get("root_release_hash") == ROOT_RELEASE_HASH
            and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_hashes": root_hashes, "expected": ROOT_RELEASE_HASH},
        ),
    ]

    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY" if not failures else "PNVA_ROOT_CAUSAL_MESH_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "event_count": no_tick.get("event_count"),
        "suppressed_count": no_tick.get("suppressed_count"),
        "entity_count": topology.get("entity_node_count"),
        "rule_count": topology.get("rule_node_count"),
        "entity_rule_edge_count": topology.get("entity_rule_edge_count"),
        "rule_event_edge_count": topology.get("rule_event_edge_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_causal_mesh_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "causal_mesh_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": no_tick.get("event_count"),
        "suppressed_count": no_tick.get("suppressed_count"),
        "suppression_ratio": no_tick.get("suppression_ratio"),
        "entity_count": topology.get("entity_node_count"),
        "rule_count": topology.get("rule_node_count"),
        "rule_event_edge_count": topology.get("rule_event_edge_count"),
        "entity_rule_edge_count": topology.get("entity_rule_edge_count"),
        "r3_chain_count": no_tick.get("r3_chain_count"),
        "proof_valid_count": no_tick.get("proof_valid_count"),
        "denied_edge_count": matrix.get("denied_edge_count"),
        "unknown_entity_count": no_tick.get("unknown_entity_count"),
        "unknown_rule_count": no_tick.get("unknown_rule_count"),
        "manifest_file_count": publication.get("manifest_file_count"),
        "checksum_count": publication.get("checksum_count"),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "causal_mesh_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Prove that root no-tick logs, entities, heuristics, admission, observability, growth and publication reports agree as one causal mesh.",
            "sovereignty": "A root system is stronger when every PASS is cross-counted against the other PASS reports, not trusted in isolation.",
            "boundary": "This ledger audits public evidence only. It does not execute actions, change live gates or alter runtime workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root causal mesh ledger.")
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
