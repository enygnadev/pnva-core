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
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "evolution_governor": "reports/pnva-root-evolution-governor-2026-05-05.json",
    "regression_sentinel": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "invariant_firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "regression_sentinel": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "invariant_firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
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


def _admission_modes(failures: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    if failures:
        return (
            ["audit_only"],
            [
                "runtime_expand",
                "native_execute",
                "r3_cutover_expand",
                "public_release_claim_expand",
                "unsanitized_log_ingest",
                "private_threshold_publication",
            ],
        )
    return (
        [
            "audit_only",
            "observe",
            "simulate",
            "restricted_native_event_ingest",
            "restricted_r3_precheck_commit",
            "planning_only_evolution",
        ],
        [
            "unbounded_public_claims",
            "unsanitized_log_ingest",
            "private_threshold_publication",
            "unpaired_r3_runtime_events",
            "projected_runtime_evidence",
            "unknown_entity_or_rule_runtime",
            "hardware_energy_claim_without_counter_benchmark",
        ],
    )


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    no_tick = reports["no_tick_contract"]
    topology = reports["field_topology"]
    entities = reports["entity_capability"]
    heuristics = reports["heuristic_weight"]
    governor = reports["evolution_governor"]
    regression = reports["regression_sentinel"]
    firewall = reports["invariant_firewall"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    source_checks = _source_checks(reports)
    locked_invariants = governor.get("locked_invariants", [])
    invariant_failures = [item for item in locked_invariants if item.get("pass") is not True]
    controlled_debts = governor.get("controlled_debts", [])
    uncontrolled_debts = [item for item in controlled_debts if item.get("status") != "CONTROLLED"]
    evolution_cards = governor.get("evolution_cards", [])
    unsafe_cards = [item for item in evolution_cards if item.get("status") != "SAFE_TO_PLAN"]

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "no_tick_runtime_contract_admissible",
            no_tick.get("causal_contract_score") == 100.0
            and no_tick.get("strict_threshold_violation_count") == 0
            and no_tick.get("r3_pair_failure_count") == 0
            and no_tick.get("guard_contract_failure_count") == 0
            and no_tick.get("unknown_entity_count") == 0
            and no_tick.get("unknown_rule_count") == 0
            and no_tick.get("projection_event_count") == 0,
            {
                "causal_contract_score": no_tick.get("causal_contract_score"),
                "strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
                "r3_pair_failure_count": no_tick.get("r3_pair_failure_count"),
                "guard_contract_failure_count": no_tick.get("guard_contract_failure_count"),
                "unknown_entity_count": no_tick.get("unknown_entity_count"),
                "unknown_rule_count": no_tick.get("unknown_rule_count"),
                "projection_event_count": no_tick.get("projection_event_count"),
            },
        ),
        _check(
            "no_tick_budget_inside_regression_bounds",
            no_tick.get("event_count", 0) >= _dig(regression, "baseline.no_tick.aggregate_event_count_min", 0)
            and no_tick.get("suppressed_count", 0) >= _dig(regression, "baseline.no_tick.aggregate_suppressed_count_min", 0)
            and _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_min", 0) <= no_tick.get("suppression_ratio", 0) <= _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_max", 1),
            {
                "event_count": no_tick.get("event_count"),
                "suppressed_count": no_tick.get("suppressed_count"),
                "suppression_ratio": no_tick.get("suppression_ratio"),
                "min_event_count": _dig(regression, "baseline.no_tick.aggregate_event_count_min"),
                "min_suppressed_count": _dig(regression, "baseline.no_tick.aggregate_suppressed_count_min"),
                "suppression_ratio_bounds": [
                    _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_min"),
                    _dig(regression, "baseline.no_tick.aggregate_suppression_ratio_max"),
                ],
            },
        ),
        _check(
            "entity_admission_clean",
            entities.get("blocked_entity_count") == 0
            and entities.get("projection_clean") is True
            and entities.get("proof_complete") is True
            and entities.get("entity_row_count", 0) >= 13
            and entities.get("r3_runtime_ready_count", 0) >= 1,
            {
                "entity_row_count": entities.get("entity_row_count"),
                "r3_runtime_ready_count": entities.get("r3_runtime_ready_count"),
                "native_ready_count": entities.get("native_ready_count"),
                "controlled_canonical_count": entities.get("controlled_canonical_count"),
                "blocked_entity_count": entities.get("blocked_entity_count"),
                "projection_clean": entities.get("projection_clean"),
                "proof_complete": entities.get("proof_complete"),
            },
        ),
        _check(
            "heuristic_admission_clean",
            heuristics.get("blocked_rule_count") == 0
            and heuristics.get("projection_clean") is True
            and heuristics.get("proof_complete") is True
            and heuristics.get("ready_rule_count", 0) >= 8
            and heuristics.get("controlled_legacy_rule_count") == 1,
            {
                "rule_count": heuristics.get("rule_count"),
                "ready_rule_count": heuristics.get("ready_rule_count"),
                "controlled_legacy_rule_count": heuristics.get("controlled_legacy_rule_count"),
                "blocked_rule_count": heuristics.get("blocked_rule_count"),
                "total_rule_edge_count": heuristics.get("total_rule_edge_count"),
                "projection_clean": heuristics.get("projection_clean"),
                "proof_complete": heuristics.get("proof_complete"),
            },
        ),
        _check(
            "field_topology_admission_clean",
            topology.get("blocked_edge_count") == 0
            and topology.get("orphan_entity_count") == 0
            and topology.get("orphan_rule_count") == 0
            and topology.get("unruled_event_count") == 0
            and topology.get("unknown_entity_event_count") == 0
            and topology.get("r3_edge_count", 0) >= 4,
            {
                "entity_rule_edge_count": topology.get("entity_rule_edge_count"),
                "r3_edge_count": topology.get("r3_edge_count"),
                "legacy_edge_count": topology.get("legacy_edge_count"),
                "blocked_edge_count": topology.get("blocked_edge_count"),
                "orphan_entity_count": topology.get("orphan_entity_count"),
                "orphan_rule_count": topology.get("orphan_rule_count"),
                "unruled_event_count": topology.get("unruled_event_count"),
                "unknown_entity_event_count": topology.get("unknown_entity_event_count"),
            },
        ),
        _check(
            "locked_invariants_and_regression_clean",
            governor.get("invariant_failure_count") == 0
            and not invariant_failures
            and regression.get("regressed_metric_count") == 0
            and firewall.get("failure_count") == 0,
            {
                "invariant_failure_count": governor.get("invariant_failure_count"),
                "locked_invariant_count": len(locked_invariants),
                "locked_invariant_failure_count": len(invariant_failures),
                "regressed_metric_count": regression.get("regressed_metric_count"),
                "firewall_failure_count": firewall.get("failure_count"),
            },
        ),
        _check(
            "evolution_is_planning_only_and_controlled",
            governor.get("blocked_card_count") == 0
            and governor.get("controlled_debt_count") == len(controlled_debts)
            and not uncontrolled_debts
            and not unsafe_cards,
            {
                "controlled_debt_count": governor.get("controlled_debt_count"),
                "uncontrolled_debt_count": len(uncontrolled_debts),
                "evolution_card_count": governor.get("evolution_card_count"),
                "safe_to_plan_count": governor.get("safe_to_plan_count"),
                "blocked_card_count": governor.get("blocked_card_count"),
                "unsafe_card_count": len(unsafe_cards),
            },
        ),
        _check(
            "publication_boundary_admissible",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and publication.get("manifest_file_count", 0) >= 222
            and publication.get("checksum_count", 0) >= 221,
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
    ]

    failures = [item for item in checks if not item["pass"]]
    allowed_modes, denied_modes = _admission_modes(failures)
    classification = "PNVA_ROOT_RUNTIME_ADMISSION_READY" if not failures else "PNVA_ROOT_RUNTIME_ADMISSION_BLOCKED"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "allowed_modes": allowed_modes,
        "denied_modes": denied_modes,
        "event_count": no_tick.get("event_count"),
        "suppression_ratio": no_tick.get("suppression_ratio"),
        "entity_row_count": entities.get("entity_row_count"),
        "rule_count": heuristics.get("rule_count"),
        "r3_pair_failure_count": no_tick.get("r3_pair_failure_count"),
    }

    return {
        "schema_version": "pnva.root_runtime_admission_controller.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "runtime_admission_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "admission_decision": "ADMIT_RESTRICTED_ROOT_RUNTIME_PLANNING" if not failures else "BLOCK_RUNTIME_EXPANSION",
        "allowed_modes": allowed_modes,
        "denied_modes": denied_modes,
        "event_count": no_tick.get("event_count"),
        "suppressed_count": no_tick.get("suppressed_count"),
        "suppression_ratio": no_tick.get("suppression_ratio"),
        "strict_threshold_violation_count": no_tick.get("strict_threshold_violation_count"),
        "r3_chain_count": no_tick.get("r3_chain_count"),
        "r3_pair_failure_count": no_tick.get("r3_pair_failure_count"),
        "entity_row_count": entities.get("entity_row_count"),
        "blocked_entity_count": entities.get("blocked_entity_count"),
        "rule_count": heuristics.get("rule_count"),
        "blocked_rule_count": heuristics.get("blocked_rule_count"),
        "entity_rule_edge_count": topology.get("entity_rule_edge_count"),
        "blocked_edge_count": topology.get("blocked_edge_count"),
        "controlled_debt_count": governor.get("controlled_debt_count"),
        "safe_to_plan_count": governor.get("safe_to_plan_count"),
        "regressed_metric_count": regression.get("regressed_metric_count"),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "runtime_admission_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Turn root PNVA proof state into an explicit admission decision for future runtime evidence.",
            "sovereignty": "A runtime is sovereign when it knows which modes are allowed, which modes are denied and which evidence gates must remain closed.",
            "boundary": "This controller audits public evidence only. It does not execute actions, start services, stop services or change live gates.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root runtime admission controller.")
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
