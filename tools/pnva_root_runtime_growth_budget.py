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
    "runtime_admission": "reports/pnva-root-runtime-admission-controller-2026-05-05.json",
    "admission_matrix": "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json",
    "negative_controls": "reports/pnva-root-admission-negative-controls-2026-05-05.json",
    "evolution_governor": "reports/pnva-root-evolution-governor-2026-05-05.json",
    "regression_sentinel": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "runtime_admission": "PNVA_ROOT_RUNTIME_ADMISSION_READY",
    "admission_matrix": "PNVA_ROOT_ENTITY_HEURISTIC_ADMISSION_MATRIX_READY",
    "negative_controls": "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "regression_sentinel": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
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


def _ceil_percent(value: int | float, percent: float) -> int:
    return max(1, int(math.ceil(float(value) * percent)))


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    no_tick = reports["no_tick_contract"]
    admission = reports["runtime_admission"]
    matrix = reports["admission_matrix"]
    negative = reports["negative_controls"]
    governor = reports["evolution_governor"]
    regression = reports["regression_sentinel"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    event_count = int(no_tick.get("event_count", 0))
    suppressed_count = int(no_tick.get("suppressed_count", 0))
    r3_chain_count = int(no_tick.get("r3_chain_count", 0))
    entity_rule_edge_count = int(matrix.get("entity_rule_edge_count", 0))
    bounded_legacy_edge_count = int(matrix.get("bounded_legacy_edge_count", 0))

    budget_policy = {
        "growth_mode": "SMALL_BATCH_RESTRICTED",
        "max_new_events_per_batch": _ceil_percent(event_count, 0.20),
        "max_new_r3_chains_per_batch": _ceil_percent(r3_chain_count, 0.20),
        "max_new_entity_rule_edges_per_batch": _ceil_percent(entity_rule_edge_count, 0.20),
        "min_suppression_ratio": _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_min", 0.45),
        "max_suppression_ratio": _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_max", 0.70),
        "max_denied_edges": 0,
        "max_unknown_entities": 0,
        "max_unknown_rules": 0,
        "max_projected_events": 0,
        "max_r3_pair_failures": 0,
        "max_strict_threshold_violations": 0,
        "max_bounded_legacy_edges": bounded_legacy_edge_count,
        "min_negative_controls_detected": int(negative.get("control_count", 0)),
        "allowed_growth_modes": [
            "restricted_native_event_ingest",
            "restricted_r3_precheck_commit",
            "planning_only_evolution",
        ],
        "blocked_growth_modes": [
            "unpaired_r3_runtime_events",
            "projected_runtime_evidence",
            "unknown_entity_or_rule_runtime",
            "unsanitized_log_ingest",
            "private_threshold_publication",
            "hardware_energy_claim_without_counter_benchmark",
        ],
    }

    source_checks = _source_checks(reports)
    allowed_modes = set(str(item) for item in admission.get("allowed_modes", []))
    denied_modes = set(str(item) for item in admission.get("denied_modes", []))
    controlled_debts = governor.get("controlled_debts", [])
    uncontrolled_debts = [item for item in controlled_debts if item.get("status") != "CONTROLLED"]

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "baseline_no_tick_budget_locked",
            event_count >= 589
            and suppressed_count >= 285
            and budget_policy["min_suppression_ratio"] <= no_tick.get("suppression_ratio", 0) <= budget_policy["max_suppression_ratio"],
            {
                "event_count": event_count,
                "suppressed_count": suppressed_count,
                "suppression_ratio": no_tick.get("suppression_ratio"),
                "suppression_ratio_bounds": [budget_policy["min_suppression_ratio"], budget_policy["max_suppression_ratio"]],
            },
        ),
        _check(
            "runtime_pair_and_threshold_budget_clean",
            no_tick.get("r3_pair_failure_count") == 0
            and no_tick.get("strict_threshold_violation_count") == 0
            and no_tick.get("projection_event_count") == 0
            and r3_chain_count >= 35,
            {
                "r3_chain_count": r3_chain_count,
                "r3_pair_failure_count": no_tick.get("r3_pair_failure_count"),
                "strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
                "projection_event_count": no_tick.get("projection_event_count"),
            },
        ),
        _check(
            "entity_heuristic_growth_budget_clean",
            matrix.get("denied_edge_count") == 0
            and matrix.get("unknown_entity_count") == 0
            and matrix.get("unknown_rule_count") == 0
            and matrix.get("admitted_r3_edge_count", 0) >= 4
            and matrix.get("admitted_native_edge_count", 0) >= 12
            and bounded_legacy_edge_count <= budget_policy["max_bounded_legacy_edges"],
            {
                "entity_rule_edge_count": entity_rule_edge_count,
                "admitted_r3_edge_count": matrix.get("admitted_r3_edge_count"),
                "admitted_native_edge_count": matrix.get("admitted_native_edge_count"),
                "bounded_legacy_edge_count": bounded_legacy_edge_count,
                "max_bounded_legacy_edges": budget_policy["max_bounded_legacy_edges"],
                "denied_edge_count": matrix.get("denied_edge_count"),
                "unknown_entity_count": matrix.get("unknown_entity_count"),
                "unknown_rule_count": matrix.get("unknown_rule_count"),
            },
        ),
        _check(
            "admission_modes_match_growth_policy",
            all(mode in allowed_modes for mode in budget_policy["allowed_growth_modes"])
            and all(mode in denied_modes for mode in budget_policy["blocked_growth_modes"][:3]),
            {
                "allowed_modes": admission.get("allowed_modes"),
                "denied_modes": admission.get("denied_modes"),
                "required_allowed": budget_policy["allowed_growth_modes"],
                "required_denied_core": budget_policy["blocked_growth_modes"][:3],
            },
        ),
        _check(
            "negative_controls_preserved",
            negative.get("clean_control_pass") is True
            and negative.get("detected_count") >= budget_policy["min_negative_controls_detected"]
            and negative.get("undetected_count") == 0
            and negative.get("failure_count") == 0,
            {
                "clean_control_pass": negative.get("clean_control_pass"),
                "control_count": negative.get("control_count"),
                "detected_count": negative.get("detected_count"),
                "undetected_count": negative.get("undetected_count"),
                "failure_count": negative.get("failure_count"),
            },
        ),
        _check(
            "governor_and_regression_budget_clean",
            governor.get("invariant_failure_count") == 0
            and not uncontrolled_debts
            and governor.get("blocked_card_count") == 0
            and regression.get("regressed_metric_count") == 0,
            {
                "invariant_failure_count": governor.get("invariant_failure_count"),
                "controlled_debt_count": governor.get("controlled_debt_count"),
                "uncontrolled_debt_count": len(uncontrolled_debts),
                "blocked_card_count": governor.get("blocked_card_count"),
                "regressed_metric_count": regression.get("regressed_metric_count"),
            },
        ),
        _check(
            "public_boundary_budget_clean",
            publication.get("path_leak_count") == 0 and claim.get("unbounded_high_risk_occurrence_count") == 0,
            {
                "path_leak_count": publication.get("path_leak_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
                "manifest_file_count": publication.get("manifest_file_count"),
                "checksum_count": publication.get("checksum_count"),
            },
        ),
        _check(
            "root_hash_stable",
            verifier.get("root_release_hash") == ROOT_RELEASE_HASH and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_release_hash": verifier.get("root_release_hash"), "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash")},
        ),
        _check(
            "budget_policy_complete",
            budget_policy["max_new_events_per_batch"] > 0
            and budget_policy["max_new_r3_chains_per_batch"] > 0
            and budget_policy["max_new_entity_rule_edges_per_batch"] > 0
            and budget_policy["max_denied_edges"] == 0,
            budget_policy,
        ),
    ]

    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_READY" if not failures else "PNVA_ROOT_RUNTIME_GROWTH_BUDGET_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "budget_policy": budget_policy,
        "event_count": event_count,
        "suppressed_count": suppressed_count,
        "entity_rule_edge_count": entity_rule_edge_count,
    }

    return {
        "schema_version": "pnva.root_runtime_growth_budget.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "growth_budget_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": event_count,
        "suppressed_count": suppressed_count,
        "suppression_ratio": no_tick.get("suppression_ratio"),
        "r3_chain_count": r3_chain_count,
        "entity_rule_edge_count": entity_rule_edge_count,
        "denied_edge_count": matrix.get("denied_edge_count"),
        "negative_control_count": negative.get("control_count"),
        "negative_detected_count": negative.get("detected_count"),
        "regressed_metric_count": regression.get("regressed_metric_count"),
        "budget_policy": budget_policy,
        "root_release_hash": ROOT_RELEASE_HASH,
        "runtime_growth_budget_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Define how PNVA root runtime evidence may grow without breaking no-tick, proof, entity or heuristic guarantees.",
            "sovereignty": "Growth becomes safe when it has a budget, denied modes, negative controls and regression boundaries.",
            "boundary": "This budget audits public evidence only. It does not execute actions, change live gates or alter runtime workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root runtime growth budget.")
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
