#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"

REPORTS = {
    "firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "semantic_consistency": "reports/pnva-semantic-consistency-2026-05-05.json",
    "reproducibility": "reports/pnva-reproducibility-2026-05-05.json",
}


BASELINE = {
    "root_release_hash": "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc",
    "scores": {
        "firewall_score": 100.0,
        "observability_score": 100.0,
        "dependency_score": 100.0,
        "publication_score": 100.0,
        "claim_boundary_score": 100.0,
    },
    "no_tick": {
        "aggregate_event_count_min": 589,
        "aggregate_suppressed_count_min": 285,
        "aggregate_suppression_ratio_min": 0.45,
        "aggregate_suppression_ratio_max": 0.70,
        "runtime_r3_suppression_ratio_min": 0.50,
    },
    "logs": {
        "canonical_event_count_min": 512,
        "native_event_count_min": 7,
        "runtime_r3_event_count_min": 70,
        "runtime_r3_proof_hash_unique_count_min": 70,
        "runtime_r3_projected_count_max": 0,
    },
    "entities": {
        "entity_catalog_count_min": 3,
        "entity_catalog_rows_min": 13,
    },
    "heuristics": {
        "heuristic_rule_count_min": 9,
        "influence_edge_count_min": 1136,
        "heuristic_coverage_ratio_min": 1.0,
        "proof_event_coverage_ratio_min": 1.0,
    },
    "runtime": {
        "accepted_slot_count_min": 35,
        "pending_slot_count_max": 0,
        "rejected_event_count_max": 0,
        "no_tick_pair_failure_count_max": 0,
        "negative_control_detected_count_min": 63,
        "contract_check_count_min": 315,
        "contract_failure_count_max": 0,
    },
    "public": {
        "path_leak_count_max": 0,
        "unbounded_high_risk_occurrence_count_max": 0,
        "dependency_cycle_count_max": 0,
        "dependency_unreachable_node_count_max": 0,
        "semantic_error_count_max": 0,
        "semantic_warning_count_max": 0,
        "reproducibility_failure_count_max": 0,
    },
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
        return float(value)
    except (TypeError, ValueError):
        return default


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _check(name: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "pass": bool(passed), "evidence": evidence}


def _metric(name: str, value: Any, rule: str, limit: Any) -> dict[str, Any]:
    numeric = _num(value)
    limit_numeric = _num(limit)
    if rule == "min":
        passed = numeric >= limit_numeric
    elif rule == "max":
        passed = numeric <= limit_numeric
    elif rule == "eq":
        passed = value == limit
    else:
        raise ValueError(f"unknown rule: {rule}")
    return {
        "name": name,
        "value": value,
        "rule": rule,
        "limit": limit,
        "pass": bool(passed),
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    firewall = reports["firewall"]
    observability = reports["observability"]
    dependency = reports["dependency_graph"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]
    semantic = reports["semantic_consistency"]
    reproducibility = reports["reproducibility"]

    no_tick = observability.get("no_tick_observability", {})
    logs = observability.get("log_observability", {})
    entities = observability.get("entity_observability", {})
    heuristics = observability.get("heuristic_observability", {})
    runtime = observability.get("runtime_observability", {})

    root_hashes = {
        "firewall": firewall.get("root_release_hash"),
        "observability": _dig(observability, "root_observability.root_release_hash"),
        "dependency_graph": dependency.get("root_release_hash"),
        "publication_gate": publication.get("root_release_hash"),
        "claim_boundary": claim.get("root_release_hash"),
        "release_verifier": verifier.get("root_release_hash"),
        "release_verifier_recomputed": verifier.get("recomputed_root_release_hash"),
    }
    root_hash_set = set(value for value in root_hashes.values() if value)

    metrics = [
        _metric("root_hash_stable", next(iter(root_hash_set)) if len(root_hash_set) == 1 else "", "eq", BASELINE["root_release_hash"]),
        _metric("firewall_score", firewall.get("firewall_score"), "min", BASELINE["scores"]["firewall_score"]),
        _metric("observability_score", observability.get("observability_score"), "min", BASELINE["scores"]["observability_score"]),
        _metric("dependency_score", dependency.get("dependency_score"), "min", BASELINE["scores"]["dependency_score"]),
        _metric("publication_score", publication.get("publication_score"), "min", BASELINE["scores"]["publication_score"]),
        _metric("claim_boundary_score", claim.get("claim_boundary_score"), "min", BASELINE["scores"]["claim_boundary_score"]),
        _metric("aggregate_event_count", no_tick.get("aggregate_event_count"), "min", BASELINE["no_tick"]["aggregate_event_count_min"]),
        _metric("aggregate_suppressed_count", no_tick.get("aggregate_suppressed_count"), "min", BASELINE["no_tick"]["aggregate_suppressed_count_min"]),
        _metric("aggregate_suppression_ratio_min", no_tick.get("aggregate_suppression_ratio"), "min", BASELINE["no_tick"]["aggregate_suppression_ratio_min"]),
        _metric("aggregate_suppression_ratio_max", no_tick.get("aggregate_suppression_ratio"), "max", BASELINE["no_tick"]["aggregate_suppression_ratio_max"]),
        _metric("runtime_r3_suppression_ratio", _dig(no_tick, "layers.runtime_r3.no_tick_suppression_ratio"), "min", BASELINE["no_tick"]["runtime_r3_suppression_ratio_min"]),
        _metric("canonical_event_count", _dig(logs, "canonical.event_count"), "min", BASELINE["logs"]["canonical_event_count_min"]),
        _metric("native_event_count", _dig(logs, "native.event_count"), "min", BASELINE["logs"]["native_event_count_min"]),
        _metric("runtime_r3_event_count", _dig(logs, "runtime_r3.event_count"), "min", BASELINE["logs"]["runtime_r3_event_count_min"]),
        _metric("runtime_r3_proof_hash_unique_count", _dig(logs, "runtime_r3.proof_hash_unique_count"), "min", BASELINE["logs"]["runtime_r3_proof_hash_unique_count_min"]),
        _metric("runtime_r3_projected_count", _dig(logs, "runtime_r3.projected_count"), "max", BASELINE["logs"]["runtime_r3_projected_count_max"]),
        _metric("entity_catalog_count", _dig(firewall, "locked_invariants.entity_catalog_count"), "min", BASELINE["entities"]["entity_catalog_count_min"]),
        _metric("entity_catalog_rows", entities.get("total_entity_rows"), "min", BASELINE["entities"]["entity_catalog_rows_min"]),
        _metric("heuristic_rule_count", heuristics.get("heuristic_rule_count"), "min", BASELINE["heuristics"]["heuristic_rule_count_min"]),
        _metric("influence_edge_count", heuristics.get("influence_edge_count"), "min", BASELINE["heuristics"]["influence_edge_count_min"]),
        _metric("heuristic_coverage_ratio", heuristics.get("heuristic_coverage_ratio"), "min", BASELINE["heuristics"]["heuristic_coverage_ratio_min"]),
        _metric("proof_event_coverage_ratio", heuristics.get("proof_event_coverage_ratio"), "min", BASELINE["heuristics"]["proof_event_coverage_ratio_min"]),
        _metric("runtime_accepted_slots", runtime.get("accepted_slot_count"), "min", BASELINE["runtime"]["accepted_slot_count_min"]),
        _metric("runtime_pending_slots", runtime.get("pending_slot_count"), "max", BASELINE["runtime"]["pending_slot_count_max"]),
        _metric("runtime_rejected_events", runtime.get("rejected_event_count"), "max", BASELINE["runtime"]["rejected_event_count_max"]),
        _metric("runtime_no_tick_pair_failures", runtime.get("no_tick_pair_failure_count"), "max", BASELINE["runtime"]["no_tick_pair_failure_count_max"]),
        _metric("runtime_negative_control_detected_count", runtime.get("negative_control_detected_count"), "min", BASELINE["runtime"]["negative_control_detected_count_min"]),
        _metric("runtime_contract_check_count", runtime.get("contract_check_count"), "min", BASELINE["runtime"]["contract_check_count_min"]),
        _metric("runtime_contract_failure_count", runtime.get("contract_failure_count"), "max", BASELINE["runtime"]["contract_failure_count_max"]),
        _metric("publication_path_leak_count", publication.get("path_leak_count"), "max", BASELINE["public"]["path_leak_count_max"]),
        _metric("unbounded_high_risk_occurrence_count", claim.get("unbounded_high_risk_occurrence_count"), "max", BASELINE["public"]["unbounded_high_risk_occurrence_count_max"]),
        _metric("dependency_cycle_count", dependency.get("cycle_count"), "max", BASELINE["public"]["dependency_cycle_count_max"]),
        _metric("dependency_unreachable_node_count", dependency.get("unreachable_node_count"), "max", BASELINE["public"]["dependency_unreachable_node_count_max"]),
        _metric("semantic_error_count", semantic.get("error_count"), "max", BASELINE["public"]["semantic_error_count_max"]),
        _metric("semantic_warning_count", semantic.get("warning_count"), "max", BASELINE["public"]["semantic_warning_count_max"]),
        _metric("reproducibility_failure_count", reproducibility.get("failure_count"), "max", BASELINE["public"]["reproducibility_failure_count_max"]),
    ]

    classification_reports = [
        ("firewall", firewall, "PNVA_ROOT_INVARIANT_FIREWALL_READY"),
        ("observability", observability, "PNVA_ROOT_OBSERVABILITY_INDEX_READY"),
        ("dependency_graph", dependency, "PNVA_ROOT_DEPENDENCY_GRAPH_READY"),
        ("publication_gate", publication, "PNVA_ROOT_PUBLICATION_GATE_READY"),
        ("claim_boundary", claim, "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY"),
        ("release_verifier", verifier, "PNVA_ROOT_RELEASE_VERIFIED"),
        ("semantic_consistency", semantic, "SEMANTIC_CONSISTENCY_READY"),
        ("reproducibility", reproducibility, "REPRODUCIBILITY_READY"),
    ]
    classification_failures = [
        {
            "name": name,
            "classification": report.get("classification"),
            "expected": expected,
            "pass": report.get("pass"),
        }
        for name, report, expected in classification_reports
        if report.get("classification") != expected or report.get("pass") is not True
    ]
    metric_failures = [item for item in metrics if not item["pass"]]

    checks = [
        _check("baseline_classifications_stable", not classification_failures, {"classification_failures": classification_failures}),
        _check("root_hash_stable", len(root_hash_set) == 1 and next(iter(root_hash_set)) == BASELINE["root_release_hash"], {"root_hashes": root_hashes}),
        _check("regression_metrics_stable", not metric_failures, {"failure_count": len(metric_failures), "failures": metric_failures[:20]}),
        _check("firewall_remains_clean", firewall.get("failure_count") == 0 and firewall.get("pass") is True, {"firewall_score": firewall.get("firewall_score"), "failure_count": firewall.get("failure_count")}),
        _check("public_hygiene_remains_clean", publication.get("path_leak_count") == 0 and claim.get("unbounded_high_risk_occurrence_count") == 0, {"path_leak_count": publication.get("path_leak_count"), "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count")}),
    ]
    failures = [item for item in checks if not item["pass"]]
    stable_metric_count = len(metrics) - len(metric_failures)
    score = round(100.0 * stable_metric_count / max(1, len(metrics)), 2)
    classification = "PNVA_ROOT_REGRESSION_SENTINEL_READY" if not failures else "PNVA_ROOT_REGRESSION_SENTINEL_ALERT"

    fingerprint = {
        "classification": classification,
        "metrics": [{k: item[k] for k in ["name", "value", "rule", "limit", "pass"]} for item in metrics],
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "root_hashes": root_hashes,
    }

    return {
        "schema_version": "pnva.root_regression_sentinel.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "regression_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "monitored_metric_count": len(metrics),
        "stable_metric_count": stable_metric_count,
        "regressed_metric_count": len(metric_failures),
        "root_release_hash": BASELINE["root_release_hash"],
        "regression_sentinel_hash": _sha_text(json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))),
        "checks": checks,
        "metrics": metrics,
        "baseline": BASELINE,
        "next_watch_targets": [
            "keep runtime R3 projected proofs at zero",
            "keep no-tick suppression ratio above 0.45 without exceeding the upper balance limit",
            "increase entity coverage only through cataloged entities with proof refs",
            "increase heuristic rules only with proof-event coverage preserved",
            "rerun publication and claim guards after every public text change",
        ],
        "interpretation": {
            "purpose": "Watch for root-level metric drift after the invariant firewall has passed.",
            "sovereignty": "A sovereign PNVA root needs stable metrics, not only a single successful validation run.",
            "boundary": "This sentinel tracks the public evidence package and deterministic runtime sample; it does not change the root release seal.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PNVA root regression sentinel.")
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
