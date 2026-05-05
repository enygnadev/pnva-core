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
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "regression": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "theorem_ledger": "reports/pnva-root-proof-theorem-ledger-2026-05-05.json",
    "causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "adversarial": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "regression": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "theorem_ledger": "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY",
    "causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "dependency_graph": "PNVA_ROOT_DEPENDENCY_GRAPH_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "adversarial": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
}

REQUIRED_GUARDS = [
    "root_hash_stable",
    "no_tick_budget_preserved",
    "runtime_native_non_projected",
    "entity_catalog_not_reduced",
    "heuristic_coverage_not_reduced",
    "claim_boundary_clean",
    "path_hygiene_clean",
    "negative_controls_preserved",
    "theorem_ledger_preserved",
]


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


def _invariant(name: str, value: Any, rule: str, expected: Any, guard: str) -> dict[str, Any]:
    numeric = _num(value)
    if rule == "eq":
        passed = value == expected
    elif rule == "min":
        passed = numeric >= _num(expected)
    elif rule == "max":
        passed = numeric <= _num(expected)
    elif rule == "between":
        low, high = expected
        passed = _num(low) <= numeric <= _num(high)
    else:
        raise ValueError(f"unknown invariant rule: {rule}")
    return {
        "name": name,
        "value": value,
        "rule": rule,
        "expected": expected,
        "guard": guard,
        "pass": bool(passed),
    }


def _debt(debt_id: str, signal: Any, impact: str, remediation: str, boundary: str) -> dict[str, Any]:
    return {
        "debt_id": debt_id,
        "status": "CONTROLLED",
        "signal": signal,
        "impact": impact,
        "remediation": remediation,
        "boundary": boundary,
    }


def _card(
    card_id: str,
    title: str,
    objective: str,
    impact_area: list[str],
    required_guards: list[str],
    success_metrics: dict[str, Any],
    execution_mode: str = "planning_only",
) -> dict[str, Any]:
    missing_guards = sorted(set(REQUIRED_GUARDS) - set(required_guards))
    return {
        "card_id": card_id,
        "status": "SAFE_TO_PLAN" if execution_mode == "planning_only" and not missing_guards else "BLOCKED",
        "title": title,
        "objective": objective,
        "impact_area": impact_area,
        "execution_mode": execution_mode,
        "required_guards": required_guards,
        "missing_required_guards": missing_guards,
        "success_metrics": success_metrics,
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    obs = reports["observability"]
    firewall = reports["firewall"]
    regression = reports["regression"]
    theorem = reports["theorem_ledger"]
    causal = reports["causal_intelligence"]
    traceability = reports["traceability"]
    dependency = reports["dependency_graph"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]
    adversarial = reports["adversarial"]

    no_tick = obs.get("no_tick_observability", {})
    logs = obs.get("log_observability", {})
    entities = obs.get("entity_observability", {})
    heuristics = obs.get("heuristic_observability", {})
    runtime = obs.get("runtime_observability", {})
    low_authority = heuristics.get("low_authority_legacy_context", {})

    classification_checks = [
        {
            "name": name,
            "classification": reports[name].get("classification"),
            "expected": expected,
            "pass": reports[name].get("classification") == expected and reports[name].get("pass") is True,
        }
        for name, expected in EXPECTED_CLASSIFICATIONS.items()
    ]

    root_hashes = {
        "firewall": firewall.get("root_release_hash"),
        "regression": regression.get("root_release_hash"),
        "theorem_ledger": theorem.get("root_release_hash"),
        "dependency_graph": dependency.get("root_release_hash"),
        "publication_gate": publication.get("root_release_hash"),
        "claim_boundary": claim.get("root_release_hash"),
        "release_verifier": verifier.get("root_release_hash"),
        "release_verifier_recomputed": verifier.get("recomputed_root_release_hash"),
    }
    root_hash_values = {value for value in root_hashes.values() if value}

    invariants = [
        _invariant("root_release_hash", next(iter(root_hash_values)) if len(root_hash_values) == 1 else "", "eq", ROOT_RELEASE_HASH, "root_hash_stable"),
        _invariant("aggregate_event_count", no_tick.get("aggregate_event_count"), "min", 589, "no_tick_budget_preserved"),
        _invariant("aggregate_suppressed_count", no_tick.get("aggregate_suppressed_count"), "min", 285, "no_tick_budget_preserved"),
        _invariant("aggregate_suppression_ratio", no_tick.get("aggregate_suppression_ratio"), "between", [0.45, 0.70], "no_tick_budget_preserved"),
        _invariant("runtime_r3_event_count", _dig(logs, "runtime_r3.event_count"), "eq", 70, "runtime_native_non_projected"),
        _invariant("runtime_r3_native_count", _dig(logs, "runtime_r3.native_count"), "eq", 70, "runtime_native_non_projected"),
        _invariant("runtime_r3_projected_count", _dig(logs, "runtime_r3.projected_count"), "eq", 0, "runtime_native_non_projected"),
        _invariant("runtime_accepted_slot_count", runtime.get("accepted_slot_count"), "eq", 35, "runtime_native_non_projected"),
        _invariant("runtime_pending_slot_count", runtime.get("pending_slot_count"), "eq", 0, "runtime_native_non_projected"),
        _invariant("runtime_rejected_event_count", runtime.get("rejected_event_count"), "eq", 0, "runtime_native_non_projected"),
        _invariant("entity_catalog_rows", entities.get("total_entity_rows"), "min", 13, "entity_catalog_not_reduced"),
        _invariant("entity_catalog_count", _dig(firewall, "locked_invariants.entity_catalog_count"), "min", 3, "entity_catalog_not_reduced"),
        _invariant("heuristic_rule_count", heuristics.get("heuristic_rule_count"), "min", 9, "heuristic_coverage_not_reduced"),
        _invariant("heuristic_coverage_ratio", heuristics.get("heuristic_coverage_ratio"), "eq", 1.0, "heuristic_coverage_not_reduced"),
        _invariant("proof_event_coverage_ratio", heuristics.get("proof_event_coverage_ratio"), "eq", 1.0, "heuristic_coverage_not_reduced"),
        _invariant("influence_edge_count", heuristics.get("influence_edge_count"), "min", 1136, "heuristic_coverage_not_reduced"),
        _invariant("unbounded_high_risk_occurrence_count", claim.get("unbounded_high_risk_occurrence_count"), "eq", 0, "claim_boundary_clean"),
        _invariant("publication_path_leak_count", publication.get("path_leak_count"), "eq", 0, "path_hygiene_clean"),
        _invariant("negative_control_detected_count", runtime.get("negative_control_detected_count"), "eq", 63, "negative_controls_preserved"),
        _invariant("adversarial_detected_count", adversarial.get("detected_count"), "eq", 8, "negative_controls_preserved"),
        _invariant("theorem_failed_count", theorem.get("failed_theorem_count"), "eq", 0, "theorem_ledger_preserved"),
        _invariant("theorem_proven_count", theorem.get("proven_theorem_count"), "min", 12, "theorem_ledger_preserved"),
    ]
    invariant_failures = [item for item in invariants if not item["pass"]]

    controlled_debts = [
        _debt(
            "D1_CANONICAL_LEGACY_AUTHORITY_CONTEXT",
            {
                "decision_trace_low_authority_trace_count": low_authority.get("decision_trace_low_authority_trace_count"),
                "entity_legacy_low_authority_warning_count": low_authority.get("entity_legacy_low_authority_warning_count"),
                "heuristic_low_authority_strong_edge_count": low_authority.get("heuristic_low_authority_strong_edge_count"),
            },
            "Legacy context is preserved as migration evidence and should not expand.",
            "Move legacy observer evidence toward native or R3 runtime evidence while keeping proof coverage at 1.0.",
            "Controlled warning context, not a current root failure.",
        ),
        _debt(
            "D2_RUNTIME_R3_SCOPE_IS_STILL_SMALL",
            {"runtime_r3_entity_count": _dig(entities, "scopes.runtime_r3.entity_count"), "accepted_slot_count": runtime.get("accepted_slot_count")},
            "The runtime sample is strong but intentionally narrow.",
            "Add more R3 runtime entities and slot pairs only under the evidence guard.",
            "This is a scope limit, not a contradiction of current PASS.",
        ),
        _debt(
            "D3_PUBLIC_CLAIM_DENSITY_REQUIRES_DISCIPLINE",
            {"high_risk_occurrence_count": claim.get("high_risk_occurrence_count"), "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count")},
            "Strong language is present but bounded.",
            "Keep every strong claim tied to a theorem ID and reduce unsupported rhetorical density.",
            "Bounded public language remains acceptable while unbounded claims stay zero.",
        ),
        _debt(
            "D4_EXTERNAL_REPLICATION_NOT_YET_SEPARATE",
            {"reproducibility_scope": "repository deterministic checks"},
            "The current package is reproducible locally from published reports, but independent external replication is future work.",
            "Publish a minimal reproduction capsule with expected report hashes and environment notes.",
            "This does not weaken current repository evidence.",
        ),
        _debt(
            "D5_HARDWARE_COUNTER_BENCHMARK_PENDING",
            {"current_metric_scope": "event, proof, entity, heuristic and runtime contracts"},
            "The current package proves causal execution discipline, not hardware energy counters.",
            "Add a separate perf or powertop benchmark harness with environment declaration.",
            "Do not claim hardware-level energy gain before separate counters exist.",
        ),
    ]

    guard_set = list(REQUIRED_GUARDS)
    evolution_cards = [
        _card(
            "E1_EXPAND_R3_ENTITY_FIELD",
            "Expand R3 runtime entity coverage",
            "Add more native runtime entities and keep each new slot bound to precheck, commit, proof hash and no-tick pair.",
            ["entities", "runtime", "no_tick"],
            guard_set,
            {"runtime_r3_entity_count_min_next": 3, "pending_slot_count_max": 0, "projected_count_max": 0},
        ),
        _card(
            "E2_ADD_RUNTIME_BLOCK_PATH_SAMPLE",
            "Add R3 block-path evidence",
            "Capture native block-path samples so runtime scope includes collapse, observe and block behavior under proof.",
            ["no_tick", "logs", "negative_controls"],
            guard_set,
            {"runtime_block_path_events_min_next": 2, "no_tick_pair_failure_count_max": 0},
        ),
        _card(
            "E3_MIGRATE_LEGACY_OBSERVER_CONTEXT",
            "Reduce canonical legacy authority reliance",
            "Move legacy observer paths into native/R3 authority while preserving historical evidence as controlled context.",
            ["heuristics", "authority", "logs"],
            guard_set,
            {"native_influence_clean": True, "proof_event_coverage_ratio": 1.0},
        ),
        _card(
            "E4_CREATE_HEURISTIC_WEIGHT_LEDGER",
            "Expose bounded heuristic weights",
            "Publish rule-level weights, thresholds and tension contribution summaries while keeping private tuning out of public artifacts.",
            ["heuristics", "tension", "proofs"],
            guard_set,
            {"heuristic_rule_count_min": 9, "proof_event_coverage_ratio": 1.0},
        ),
        _card(
            "E5_BUILD_REPRODUCTION_CAPSULE",
            "Package deterministic reproduction",
            "Add a compact reproduction script that reruns root validators and checks expected hashes for reviewers.",
            ["reproducibility", "publication"],
            guard_set,
            {"command_failure_count": 0, "checksum_mismatch_count": 0},
        ),
        _card(
            "E6_ADD_COUNTER_BENCH_HARNESS",
            "Separate hardware-counter benchmark",
            "Create an optional benchmark harness for wakeups, CPU and latency with environment metadata and no broad performance claims.",
            ["metrics", "benchmark", "publication_boundary"],
            guard_set,
            {"path_leak_count": 0, "unbounded_high_risk_occurrence_count": 0},
        ),
        _card(
            "E7_CREATE_DOMAIN_ADAPTER_TEMPLATES",
            "Map PNVA to sector adapters",
            "Define adapter schemas for legal, social, mental and operational systems as event-state-tension proof templates.",
            ["architecture", "documentation", "entities"],
            guard_set,
            {"claim_boundary_clean": True, "theorem_failed_count": 0},
        ),
        _card(
            "E8_BIND_PAPER_CLAIMS_TO_THEOREMS",
            "Tie paper claims to theorem IDs",
            "Make every strong public statement cite a theorem card or a boundary section.",
            ["paper", "llms", "publication"],
            guard_set,
            {"failed_theorem_count": 0, "unbounded_high_risk_occurrence_count": 0},
        ),
    ]
    unsafe_cards = [item for item in evolution_cards if item["status"] != "SAFE_TO_PLAN"]

    checks = [
        _check(
            "source_classifications_ready",
            all(item["pass"] for item in classification_checks),
            {"classification_failures": [item for item in classification_checks if not item["pass"]]},
        ),
        _check("root_invariants_locked", not invariant_failures, {"failure_count": len(invariant_failures), "failures": invariant_failures[:20]}),
        _check("controlled_debts_declared", bool(controlled_debts) and all(item.get("remediation") for item in controlled_debts), {"controlled_debt_count": len(controlled_debts)}),
        _check("evolution_cards_guarded", not unsafe_cards, {"evolution_card_count": len(evolution_cards), "unsafe_cards": unsafe_cards}),
        _check(
            "publication_hygiene_clean",
            publication.get("path_leak_count") == 0 and claim.get("unbounded_high_risk_occurrence_count") == 0,
            {"path_leak_count": publication.get("path_leak_count"), "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count")},
        ),
        _check(
            "theorem_ledger_ready",
            theorem.get("classification") == "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY" and theorem.get("failed_theorem_count") == 0,
            {"theorem_count": theorem.get("theorem_count"), "failed_theorem_count": theorem.get("failed_theorem_count")},
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_EVOLUTION_GOVERNOR_READY" if not failures else "PNVA_ROOT_EVOLUTION_GOVERNOR_BLOCKED"
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    fingerprint = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "invariants": [{"name": item["name"], "value": item["value"], "pass": item["pass"]} for item in invariants],
        "evolution_cards": [{"card_id": item["card_id"], "status": item["status"]} for item in evolution_cards],
        "root_hashes": root_hashes,
    }

    return {
        "schema_version": "pnva.root_evolution_governor.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "governor_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "invariant_count": len(invariants),
        "invariant_failure_count": len(invariant_failures),
        "controlled_debt_count": len(controlled_debts),
        "evolution_card_count": len(evolution_cards),
        "safe_to_plan_count": len(evolution_cards) - len(unsafe_cards),
        "blocked_card_count": len(unsafe_cards),
        "root_release_hash": ROOT_RELEASE_HASH,
        "evolution_governor_hash": _sha_text(json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": classification_checks,
        "root_hashes": root_hashes,
        "locked_invariants": invariants,
        "controlled_debts": controlled_debts,
        "evolution_cards": evolution_cards,
        "current_root_state": {
            "aggregate_event_count": no_tick.get("aggregate_event_count"),
            "aggregate_suppressed_count": no_tick.get("aggregate_suppressed_count"),
            "aggregate_suppression_ratio": no_tick.get("aggregate_suppression_ratio"),
            "runtime_r3_events": _dig(logs, "runtime_r3.event_count"),
            "runtime_r3_native_events": _dig(logs, "runtime_r3.native_count"),
            "runtime_r3_projected_events": _dig(logs, "runtime_r3.projected_count"),
            "entity_catalog_rows": entities.get("total_entity_rows"),
            "runtime_r3_entity_count": _dig(entities, "scopes.runtime_r3.entity_count"),
            "heuristic_rule_count": heuristics.get("heuristic_rule_count"),
            "influence_edge_count": heuristics.get("influence_edge_count"),
            "traceability_score": traceability.get("root_traceability_score"),
            "causal_intelligence_score": causal.get("root_causal_intelligence_score"),
            "dependency_score": dependency.get("dependency_score"),
            "publication_score": publication.get("publication_score"),
        },
        "interpretation": {
            "purpose": "Define safe PNVA root evolution steps while preserving no-tick, logs, entities, heuristics, proof identity and public boundaries.",
            "sovereignty": "A sovereign root improves only through guarded cards that preserve locked invariants.",
            "boundary": "This governor is advisory and deterministic. It does not execute system actions, change live gates or claim external deployment validation.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root evolution governor.")
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
