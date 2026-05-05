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
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

REPORTS = {
    "regression": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "adversarial": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
    "semantic": "reports/pnva-semantic-consistency-2026-05-05.json",
    "reproducibility": "reports/pnva-reproducibility-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "regression": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "dependency_graph": "PNVA_ROOT_DEPENDENCY_GRAPH_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "adversarial": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
    "semantic": "SEMANTIC_CONSISTENCY_READY",
    "reproducibility": "REPRODUCIBILITY_READY",
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


def _criterion(name: str, value: Any, rule: str, expected: Any) -> dict[str, Any]:
    numeric = _num(value)
    expected_numeric = _num(expected)
    if rule == "eq":
        passed = value == expected
    elif rule == "min":
        passed = numeric >= expected_numeric
    elif rule == "max":
        passed = numeric <= expected_numeric
    elif rule == "between":
        low, high = expected
        passed = _num(low) <= numeric <= _num(high)
    else:
        raise ValueError(f"unknown criterion rule: {rule}")
    return {
        "name": name,
        "value": value,
        "rule": rule,
        "expected": expected,
        "pass": bool(passed),
    }


def _theorem(
    theorem_id: str,
    claim: str,
    criteria: list[dict[str, Any]],
    evidence: dict[str, Any],
    boundary: str,
    depends_on: list[str],
) -> dict[str, Any]:
    failed = [item for item in criteria if not item.get("pass")]
    return {
        "theorem_id": theorem_id,
        "status": "PROVEN" if not failed else "NOT_PROVEN",
        "claim": claim,
        "criteria": criteria,
        "failed_criteria": failed,
        "evidence": evidence,
        "boundary": boundary,
        "depends_on": depends_on,
    }


def _classification_checks(reports: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for name, expected in EXPECTED_CLASSIFICATIONS.items():
        report = reports[name]
        checks.append(
            {
                "name": name,
                "classification": report.get("classification"),
                "expected": expected,
                "pass": report.get("classification") == expected and report.get("pass") is True,
            }
        )
    return checks


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    obs = reports["observability"]
    firewall = reports["firewall"]
    regression = reports["regression"]
    dependency = reports["dependency_graph"]
    publication = reports["publication_gate"]
    claim_boundary = reports["claim_boundary"]
    verifier = reports["release_verifier"]
    causal = reports["causal_intelligence"]
    traceability = reports["traceability"]
    adversarial = reports["adversarial"]
    semantic = reports["semantic"]
    reproducibility = reports["reproducibility"]

    no_tick = obs.get("no_tick_observability", {})
    logs = obs.get("log_observability", {})
    entities = obs.get("entity_observability", {})
    heuristics = obs.get("heuristic_observability", {})
    runtime = obs.get("runtime_observability", {})
    trace_summary = traceability.get("summary", {})
    causal_no_tick = causal.get("no_tick_aggregate", {})
    classification_checks = _classification_checks(reports)

    root_hashes = {
        "regression": regression.get("root_release_hash"),
        "firewall": firewall.get("root_release_hash"),
        "observability": _dig(obs, "root_observability.root_release_hash"),
        "dependency_graph": dependency.get("root_release_hash"),
        "publication_gate": publication.get("root_release_hash"),
        "claim_boundary": claim_boundary.get("root_release_hash"),
        "release_verifier": verifier.get("root_release_hash"),
        "release_verifier_recomputed": verifier.get("recomputed_root_release_hash"),
    }
    root_hash_values = {value for value in root_hashes.values() if value}

    theorems = [
        _theorem(
            "T1_NO_TICK_SUPPRESSION_OBSERVED",
            "The public PNVA evidence set contains proof-backed no-tick suppression with preserved decision accounting.",
            [
                _criterion("aggregate_event_count", no_tick.get("aggregate_event_count"), "min", 589),
                _criterion("aggregate_suppressed_count", no_tick.get("aggregate_suppressed_count"), "min", 285),
                _criterion("aggregate_suppression_ratio", no_tick.get("aggregate_suppression_ratio"), "between", [0.45, 0.70]),
                _criterion("proof_integrity_canonical", _dig(no_tick, "layers.canonical.proof_integrity_ratio"), "eq", 1.0),
                _criterion("proof_integrity_runtime_r3", _dig(no_tick, "layers.runtime_r3.proof_integrity_ratio"), "eq", 1.0),
            ],
            {
                "aggregate_event_count": no_tick.get("aggregate_event_count"),
                "aggregate_suppressed_count": no_tick.get("aggregate_suppressed_count"),
                "aggregate_suppression_ratio": no_tick.get("aggregate_suppression_ratio"),
                "canonical_suppressed_count": _dig(no_tick, "layers.canonical.suppressed_count"),
                "runtime_r3_suppressed_count": _dig(no_tick, "layers.runtime_r3.suppressed_count"),
            },
            "This theorem proves suppression in the public deterministic sample, not a universal performance rule.",
            ["observability", "firewall", "regression"],
        ),
        _theorem(
            "T2_RUNTIME_R3_NATIVE_NON_PROJECTED",
            "The R3 runtime sample is accepted as native, slot-bound and non-projected evidence.",
            [
                _criterion("runtime_r3_event_count", _dig(logs, "runtime_r3.event_count"), "eq", 70),
                _criterion("runtime_r3_native_count", _dig(logs, "runtime_r3.native_count"), "eq", 70),
                _criterion("runtime_r3_projected_count", _dig(logs, "runtime_r3.projected_count"), "eq", 0),
                _criterion("runtime_r3_proof_hash_unique_count", _dig(logs, "runtime_r3.proof_hash_unique_count"), "eq", 70),
                _criterion("accepted_slot_count", runtime.get("accepted_slot_count"), "eq", 35),
                _criterion("pending_slot_count", runtime.get("pending_slot_count"), "eq", 0),
                _criterion("rejected_event_count", runtime.get("rejected_event_count"), "eq", 0),
            ],
            {
                "runtime_r3_event_count": _dig(logs, "runtime_r3.event_count"),
                "runtime_r3_native_count": _dig(logs, "runtime_r3.native_count"),
                "runtime_r3_projected_count": _dig(logs, "runtime_r3.projected_count"),
                "accepted_slot_count": runtime.get("accepted_slot_count"),
            },
            "This theorem proves native status for the included R3 runtime sample only.",
            ["observability", "runtime_evidence_guard", "traceability"],
        ),
        _theorem(
            "T3_ENTITY_CATALOG_COVERAGE",
            "The PNVA evidence base has cataloged entity coverage across canonical, native and R3 runtime scopes.",
            [
                _criterion("entity_catalog_count", _dig(firewall, "locked_invariants.entity_catalog_count"), "min", 3),
                _criterion("entity_catalog_rows", entities.get("total_entity_rows"), "min", 13),
                _criterion("runtime_r3_entity_count", _dig(entities, "scopes.runtime_r3.entity_count"), "eq", 1),
                _criterion("firewall_failure_count", firewall.get("failure_count"), "eq", 0),
            ],
            {
                "scope_count": entities.get("scope_count"),
                "total_entity_rows": entities.get("total_entity_rows"),
                "type_mix": entities.get("type_mix"),
                "state_mix": entities.get("state_mix"),
            },
            "This theorem proves catalog coverage for the public evidence set, not exhaustive deployment discovery.",
            ["observability", "firewall"],
        ),
        _theorem(
            "T4_HEURISTIC_VISIBILITY_CLOSED",
            "Heuristic rules are visible, covered by proof events and clean in native influence scope.",
            [
                _criterion("heuristic_rule_count", heuristics.get("heuristic_rule_count"), "min", 9),
                _criterion("influence_edge_count", heuristics.get("influence_edge_count"), "min", 1136),
                _criterion("heuristic_coverage_ratio", heuristics.get("heuristic_coverage_ratio"), "eq", 1.0),
                _criterion("proof_event_coverage_ratio", heuristics.get("proof_event_coverage_ratio"), "eq", 1.0),
                _criterion("native_influence_clean", heuristics.get("native_influence_clean"), "eq", True),
            ],
            {
                "heuristic_rule_count": heuristics.get("heuristic_rule_count"),
                "influence_edge_count": heuristics.get("influence_edge_count"),
                "low_authority_legacy_context": heuristics.get("low_authority_legacy_context"),
            },
            "This theorem proves explicit heuristic visibility and control, not hidden automatic learning.",
            ["observability", "causal_intelligence", "firewall"],
        ),
        _theorem(
            "T5_ROOT_PROOF_CHAIN_ACYCLIC",
            "The root proof graph is present, acyclic and reachable.",
            [
                _criterion("node_count", dependency.get("node_count"), "min", 49),
                _criterion("edge_count", dependency.get("edge_count"), "min", 104),
                _criterion("cycle_count", dependency.get("cycle_count"), "eq", 0),
                _criterion("unreachable_node_count", dependency.get("unreachable_node_count"), "eq", 0),
                _criterion("missing_artifact_count", dependency.get("missing_artifact_count"), "eq", 0),
                _criterion("readiness_failure_count", dependency.get("readiness_failure_count"), "eq", 0),
            ],
            {
                "node_count": dependency.get("node_count"),
                "edge_count": dependency.get("edge_count"),
                "phase_count": dependency.get("phase_count"),
                "root_dependency_graph_hash": dependency.get("root_dependency_graph_hash"),
            },
            "This theorem proves repository-level proof dependency hygiene, not external peer review.",
            ["dependency_graph"],
        ),
        _theorem(
            "T6_PUBLIC_CLAIM_BOUNDARY_CLEAN",
            "Public PNVA claims are bounded and free of local path exposure.",
            [
                _criterion("claim_boundary_failure_count", claim_boundary.get("failure_count"), "eq", 0),
                _criterion("unbounded_high_risk_occurrence_count", claim_boundary.get("unbounded_high_risk_occurrence_count"), "eq", 0),
                _criterion("publication_path_leak_count", publication.get("path_leak_count"), "eq", 0),
                _criterion("publication_failure_count", publication.get("failure_count"), "eq", 0),
            ],
            {
                "scanned_file_count": claim_boundary.get("scanned_file_count"),
                "high_risk_occurrence_count": claim_boundary.get("high_risk_occurrence_count"),
                "unbounded_high_risk_occurrence_count": claim_boundary.get("unbounded_high_risk_occurrence_count"),
                "path_leak_count": publication.get("path_leak_count"),
            },
            "This theorem proves public wording control for scanned files; it does not endorse claims outside the repository.",
            ["claim_boundary", "publication_gate"],
        ),
        _theorem(
            "T7_RELEASE_HASH_VERIFIED",
            "The sealed root release hash recomputes and remains stable across verifier inputs.",
            [
                _criterion("root_release_hash", verifier.get("root_release_hash"), "eq", ROOT_RELEASE_HASH),
                _criterion("recomputed_root_release_hash", verifier.get("recomputed_root_release_hash"), "eq", ROOT_RELEASE_HASH),
                _criterion("verification_count", verifier.get("verification_count"), "min", 9),
                _criterion("verifier_failure_count", verifier.get("failure_count"), "eq", 0),
                _criterion("checksum_missing_count", verifier.get("checksum_missing_count"), "eq", 0),
                _criterion("checksum_mismatch_count", verifier.get("checksum_mismatch_count"), "eq", 0),
                _criterion("stable_hash_mismatch_count", verifier.get("stable_hash_mismatch_count"), "eq", 0),
                _criterion("classification_mismatch_count", verifier.get("classification_mismatch_count"), "eq", 0),
            ],
            {
                "root_release_hash": verifier.get("root_release_hash"),
                "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash"),
                "sealed_artifact_count": verifier.get("sealed_artifact_count"),
            },
            "This theorem proves the current public root seal; later artifacts are post-seal extensions.",
            ["release_verifier", "release_seal"],
        ),
        _theorem(
            "T8_REGRESSION_BASELINE_STABLE",
            "The post-firewall root baseline has no detected metric regression.",
            [
                _criterion("regression_score", regression.get("regression_score"), "eq", 100.0),
                _criterion("regression_failure_count", regression.get("failure_count"), "eq", 0),
                _criterion("monitored_metric_count", regression.get("monitored_metric_count"), "eq", 36),
                _criterion("stable_metric_count", regression.get("stable_metric_count"), "eq", 36),
                _criterion("regressed_metric_count", regression.get("regressed_metric_count"), "eq", 0),
            ],
            {
                "regression_sentinel_hash": regression.get("regression_sentinel_hash"),
                "baseline": regression.get("baseline"),
            },
            "This theorem proves stability against the declared public baseline, not future performance.",
            ["regression", "firewall", "observability"],
        ),
        _theorem(
            "T9_SEMANTIC_REPRODUCIBILITY_CLEAN",
            "Semantic consistency and reproducibility checks are clean for the published evidence package.",
            [
                _criterion("semantic_error_count", semantic.get("error_count"), "eq", 0),
                _criterion("semantic_warning_count", semantic.get("warning_count"), "eq", 0),
                _criterion("semantic_check_count", semantic.get("check_count"), "min", 331),
                _criterion("repro_command_failure_count", reproducibility.get("command_failure_count"), "eq", 0),
                _criterion("repro_comparison_failure_count", reproducibility.get("comparison_failure_count"), "eq", 0),
                _criterion("repro_comparison_count", reproducibility.get("comparison_count"), "min", 445),
            ],
            {
                "semantic_check_count": semantic.get("check_count"),
                "repro_command_count": reproducibility.get("command_count"),
                "repro_comparison_count": reproducibility.get("comparison_count"),
            },
            "This theorem proves deterministic repository checks, not independent laboratory replication.",
            ["semantic", "reproducibility"],
        ),
        _theorem(
            "T10_ADVERSARIAL_CONTROLS_DETECT_MUTATIONS",
            "Root adversarial controls detect all declared controlled mutations.",
            [
                _criterion("clean_control_pass", adversarial.get("clean_control_pass"), "eq", True),
                _criterion("test_count", adversarial.get("test_count"), "eq", 8),
                _criterion("detected_count", adversarial.get("detected_count"), "eq", 8),
                _criterion("adversarial_failure_count", adversarial.get("failure_count"), "eq", 0),
                _criterion("runtime_negative_control_detected_count", runtime.get("negative_control_detected_count"), "eq", 63),
                _criterion("runtime_negative_control_count", runtime.get("negative_control_count"), "eq", 63),
            ],
            {
                "test_count": adversarial.get("test_count"),
                "detected_count": adversarial.get("detected_count"),
                "mutation_targets": adversarial.get("mutation_targets"),
                "runtime_negative_control_detected_count": runtime.get("negative_control_detected_count"),
            },
            "This theorem proves detection for declared controlled mutations, not every possible attack.",
            ["adversarial", "runtime_evidence_guard", "observability"],
        ),
        _theorem(
            "T11_TRACEABILITY_SLOT_CLOSURE",
            "Every R3 runtime slot has closed traceability from precheck to commit proof.",
            [
                _criterion("slot_count", trace_summary.get("slot_count"), "eq", 35),
                _criterion("event_count", trace_summary.get("event_count"), "eq", 70),
                _criterion("precheck_count", trace_summary.get("precheck_count"), "eq", 35),
                _criterion("commit_count", trace_summary.get("commit_count"), "eq", 35),
                _criterion("invalid_slot_count", trace_summary.get("invalid_slot_count"), "eq", 0),
                _criterion("proof_hash_unique_count", trace_summary.get("proof_hash_unique_count"), "eq", 70),
                _criterion("traceability_score", traceability.get("root_traceability_score"), "eq", 100.0),
            ],
            {
                "summary": trace_summary,
                "root_traceability_hash": traceability.get("root_traceability_hash"),
            },
            "This theorem proves closure for the included R3 slots, not unobserved runtime activity.",
            ["traceability", "observability"],
        ),
        _theorem(
            "T12_CAUSAL_INTELLIGENCE_ALIGNMENT",
            "The causal intelligence report agrees with no-tick, entity, heuristic and root guard signals.",
            [
                _criterion("root_causal_intelligence_score", causal.get("root_causal_intelligence_score"), "eq", 100.0),
                _criterion("causal_failure_count", causal.get("failure_count"), "eq", 0),
                _criterion("causal_event_count", causal_no_tick.get("event_count"), "eq", 589),
                _criterion("causal_suppressed_count", causal_no_tick.get("suppressed_count"), "eq", 285),
                _criterion("causal_suppression_ratio", causal_no_tick.get("suppression_ratio"), "eq", 0.483871),
                _criterion("runtime_events_native_non_projected", _dig(causal, "signals.runtime_events_native_non_projected"), "eq", True),
                _criterion("runtime_slots_closed", _dig(causal, "signals.runtime_slots_closed"), "eq", True),
            ],
            {
                "score_parts": causal.get("score_parts"),
                "signals": causal.get("signals"),
                "controlled_legacy_context": causal.get("controlled_legacy_context"),
            },
            "This theorem proves deterministic signal alignment for the public evidence package.",
            ["causal_intelligence", "observability", "firewall"],
        ),
    ]

    theorem_failures = [item for item in theorems if item["status"] != "PROVEN"]
    classification_failures = [item for item in classification_checks if not item["pass"]]
    root_hash_stable = len(root_hash_values) == 1 and ROOT_RELEASE_HASH in root_hash_values
    all_theorems_proven = not theorem_failures
    checks = [
        {
            "name": "source_classifications_ready",
            "pass": not classification_failures,
            "evidence": {"failure_count": len(classification_failures), "failures": classification_failures},
        },
        {
            "name": "root_release_hash_stable",
            "pass": root_hash_stable,
            "evidence": {"root_hashes": root_hashes, "expected": ROOT_RELEASE_HASH},
        },
        {
            "name": "all_theorems_proven",
            "pass": all_theorems_proven,
            "evidence": {"theorem_count": len(theorems), "failed_theorem_count": len(theorem_failures)},
        },
        {
            "name": "public_boundaries_clean",
            "pass": claim_boundary.get("unbounded_high_risk_occurrence_count") == 0 and publication.get("path_leak_count") == 0,
            "evidence": {
                "unbounded_high_risk_occurrence_count": claim_boundary.get("unbounded_high_risk_occurrence_count"),
                "path_leak_count": publication.get("path_leak_count"),
            },
        },
    ]
    failures = [item for item in checks if not item["pass"]]
    proven_count = len(theorems) - len(theorem_failures)
    score = round(100.0 * proven_count / max(1, len(theorems)), 2)
    classification = "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY" if not failures else "PNVA_ROOT_PROOF_THEOREM_LEDGER_FAIL"
    fingerprint = {
        "classification": classification,
        "root_release_hash": ROOT_RELEASE_HASH,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "theorems": [
            {
                "theorem_id": item["theorem_id"],
                "status": item["status"],
                "criteria": [
                    {
                        "name": criterion["name"],
                        "value": criterion["value"],
                        "rule": criterion["rule"],
                        "expected": criterion["expected"],
                        "pass": criterion["pass"],
                    }
                    for criterion in item["criteria"]
                ],
            }
            for item in theorems
        ],
    }

    return {
        "schema_version": "pnva.root_proof_theorem_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "theorem_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "theorem_count": len(theorems),
        "proven_theorem_count": proven_count,
        "failed_theorem_count": len(theorem_failures),
        "root_release_hash": ROOT_RELEASE_HASH,
        "proof_theorem_ledger_hash": _sha_text(json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": classification_checks,
        "theorems": theorems,
        "failed_theorems": theorem_failures,
        "interpretation": {
            "purpose": "Convert root PASS reports into explicit proof theorem cards with claim, criteria, evidence, boundary and dependencies.",
            "sovereignty": "A robust PNVA root should state what is proven and where each proof stops.",
            "boundary": "This ledger is a post-seal publication layer over deterministic public evidence; it does not change the root release seal.",
        },
        "recommendations": [
            "Use theorem IDs in the paper, README and future public posts when making evidence-backed claims.",
            "Add new theorems only when they have deterministic criteria, source reports and an explicit boundary.",
            "Keep commercial tuning, raw local evidence and unreviewed deployment claims outside the public theorem ledger.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root proof theorem ledger.")
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
