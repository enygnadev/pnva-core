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
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "evolution_governor": "reports/pnva-root-evolution-governor-2026-05-05.json",
    "theorem_ledger": "reports/pnva-root-proof-theorem-ledger-2026-05-05.json",
    "firewall": "reports/pnva-root-invariant-firewall-2026-05-05.json",
    "regression": "reports/pnva-root-regression-sentinel-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "theorem_ledger": "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY",
    "firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "regression": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
}

RULE_AUTHORITY = {
    "legacy_observer": "H0",
    "veonic_layer": "H1",
    "memory4d": "H1",
    "native_event_emitter": "H2",
    "adaptive_threshold": "H2",
    "affinity_router": "H2",
    "field_scheduler": "H2",
    "power_orchestrator": "H2",
    "etev_guard": "H3",
}

AUTHORITY_WEIGHT = {"H0": 0.25, "H1": 0.5, "H2": 0.75, "H3": 1.0, "H4": 1.0}
SUPPRESSED_DECISIONS = {"observe", "block"}


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


def _num(value: Any, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return numeric if math.isfinite(numeric) else default


def _round(value: float, digits: int = 6) -> float:
    return round(float(value), digits)


def _ratio(part: int | float, total: int | float) -> float:
    return _round(float(part) / max(1.0, float(total)))


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


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


def _tension(event: dict[str, Any]) -> dict[str, Any]:
    tension = event.get("tension")
    return tension if isinstance(tension, dict) else {}


def _profile(rule: str) -> dict[str, Any]:
    return {
        "rule": rule,
        "authority": RULE_AUTHORITY.get(rule, "H1"),
        "event_count": 0,
        "proof_valid_count": 0,
        "native_count": 0,
        "projected_count": 0,
        "suppressed_count": 0,
        "collapse_count": 0,
        "block_count": 0,
        "observe_count": 0,
        "decision_mix": Counter(),
        "scope_mix": Counter(),
        "entity_mix": Counter(),
        "risk_mix": Counter(),
        "score_sum": 0.0,
        "score_count": 0,
        "gate_delta_sum": 0.0,
        "gate_delta_count": 0,
    }


def _counter_pairs(counter: Counter[str], limit: int = 10) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


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


def _collect_rule_profiles(repo: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], int]:
    profiles: dict[str, dict[str, Any]] = {}
    parse_errors: list[dict[str, Any]] = []
    total_rule_edges = 0
    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            decision = _decision(event)
            proof = _proof(event)
            tension = _tension(event)
            rules = _rules(event)
            total_rule_edges += len(rules)
            risk_flags = _dig(event, "heuristics.risk_flags", []) or []
            entity_id = str(event.get("entity_id") or "")
            for rule in rules:
                profile = profiles.setdefault(rule, _profile(rule))
                profile["event_count"] += 1
                profile["decision_mix"].update([decision])
                profile["scope_mix"].update([scope])
                if entity_id:
                    profile["entity_mix"].update([entity_id])
                profile["risk_mix"].update(str(flag) for flag in risk_flags if str(flag))
                if proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:"):
                    profile["proof_valid_count"] += 1
                if proof.get("native") is True:
                    profile["native_count"] += 1
                if proof.get("projection") is True:
                    profile["projected_count"] += 1
                if decision in SUPPRESSED_DECISIONS or _dig(event, "decision.action") == "NO_ACTION":
                    profile["suppressed_count"] += 1
                if decision == "collapse":
                    profile["collapse_count"] += 1
                if decision == "block":
                    profile["block_count"] += 1
                if decision == "observe":
                    profile["observe_count"] += 1
                score = _num(tension.get("score"), default=float("nan"))
                if math.isfinite(score):
                    profile["score_sum"] += score
                    profile["score_count"] += 1
                gate_delta = _num(tension.get("gate_delta"), default=float("nan"))
                if math.isfinite(gate_delta):
                    profile["gate_delta_sum"] += gate_delta
                    profile["gate_delta_count"] += 1
    return profiles, parse_errors, total_rule_edges


def _finalize_profile(profile: dict[str, Any], max_event_count: int, aggregate_suppression_ratio: float) -> dict[str, Any]:
    event_count = int(profile["event_count"])
    authority = str(profile["authority"])
    support_norm = _ratio(event_count, max_event_count)
    proof_coverage = _ratio(profile["proof_valid_count"], event_count)
    native_ratio = _ratio(profile["native_count"], event_count)
    projected_ratio = _ratio(profile["projected_count"], event_count)
    control_norm = _round(1.0 - projected_ratio)
    suppression_ratio = _ratio(profile["suppressed_count"], event_count)
    balance_norm = _round(max(0.0, 1.0 - abs(suppression_ratio - aggregate_suppression_ratio)))
    authority_norm = AUTHORITY_WEIGHT.get(authority, 0.5)
    public_weight = _round(
        0.30 * support_norm
        + 0.25 * proof_coverage
        + 0.20 * authority_norm
        + 0.15 * control_norm
        + 0.10 * balance_norm
    )
    if authority == "H0":
        governance_status = "CONTROLLED_LEGACY"
    elif projected_ratio > 0.0 or proof_coverage < 1.0:
        governance_status = "BLOCKED_FOR_RUNTIME_USE"
    else:
        governance_status = "PUBLIC_WEIGHT_READY"
    return {
        "rule": profile["rule"],
        "authority": authority,
        "governance_status": governance_status,
        "public_weight": public_weight,
        "weight_components": {
            "support_norm": support_norm,
            "proof_coverage": proof_coverage,
            "authority_norm": authority_norm,
            "control_norm": control_norm,
            "suppression_balance_norm": balance_norm,
        },
        "event_count": event_count,
        "proof_valid_count": int(profile["proof_valid_count"]),
        "native_count": int(profile["native_count"]),
        "projected_count": int(profile["projected_count"]),
        "suppressed_count": int(profile["suppressed_count"]),
        "collapse_count": int(profile["collapse_count"]),
        "block_count": int(profile["block_count"]),
        "observe_count": int(profile["observe_count"]),
        "suppression_ratio": suppression_ratio,
        "native_ratio": native_ratio,
        "projected_ratio": projected_ratio,
        "score_mean": _round(profile["score_sum"] / max(1, profile["score_count"])),
        "gate_delta_mean": _round(profile["gate_delta_sum"] / max(1, profile["gate_delta_count"])),
        "decision_mix": _counter_pairs(profile["decision_mix"]),
        "scope_mix": _counter_pairs(profile["scope_mix"]),
        "top_entities": _counter_pairs(profile["entity_mix"], 8),
        "risk_mix": _counter_pairs(profile["risk_mix"], 8),
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    obs = reports["observability"]
    claim = reports["claim_boundary"]
    publication = reports["publication_gate"]
    verifier = reports["release_verifier"]
    theorem = reports["theorem_ledger"]
    governor = reports["evolution_governor"]
    profiles, parse_errors, total_rule_edges = _collect_rule_profiles(repo)
    no_tick = obs.get("no_tick_observability", {})
    heuristics = obs.get("heuristic_observability", {})
    runtime = obs.get("runtime_observability", {})
    aggregate_suppression_ratio = _num(no_tick.get("aggregate_suppression_ratio"))
    max_event_count = max((int(profile["event_count"]) for profile in profiles.values()), default=1)
    rule_rows = [
        _finalize_profile(profile, max_event_count, aggregate_suppression_ratio)
        for profile in profiles.values()
    ]
    rule_rows = sorted(rule_rows, key=lambda item: (-item["public_weight"], item["rule"]))

    classification_checks = _classification_checks(reports)
    rule_count = len(rule_rows)
    proof_complete = all(item["weight_components"]["proof_coverage"] == 1.0 for item in rule_rows)
    projection_clean = all(item["projected_count"] == 0 for item in rule_rows)
    known_rule_count_matches = set(profiles) == set(RULE_AUTHORITY)
    controlled_legacy_count = sum(1 for item in rule_rows if item["governance_status"] == "CONTROLLED_LEGACY")
    ready_rule_count = sum(1 for item in rule_rows if item["governance_status"] == "PUBLIC_WEIGHT_READY")
    checks = [
        {
            "name": "source_classifications_ready",
            "pass": all(item["pass"] for item in classification_checks),
            "evidence": {"failures": [item for item in classification_checks if not item["pass"]]},
        },
        {
            "name": "rule_set_complete",
            "pass": rule_count == 9 and known_rule_count_matches,
            "evidence": {"rule_count": rule_count, "expected_rules": sorted(RULE_AUTHORITY), "observed_rules": sorted(profiles)},
        },
        {
            "name": "proof_coverage_complete",
            "pass": proof_complete,
            "evidence": {"incomplete_rules": [item["rule"] for item in rule_rows if item["weight_components"]["proof_coverage"] != 1.0]},
        },
        {
            "name": "projected_rule_evidence_absent",
            "pass": projection_clean,
            "evidence": {"projected_rule_events": sum(item["projected_count"] for item in rule_rows)},
        },
        {
            "name": "runtime_guard_clean",
            "pass": runtime.get("pending_slot_count") == 0 and runtime.get("rejected_event_count") == 0,
            "evidence": {"pending_slot_count": runtime.get("pending_slot_count"), "rejected_event_count": runtime.get("rejected_event_count")},
        },
        {
            "name": "public_boundaries_clean",
            "pass": claim.get("unbounded_high_risk_occurrence_count") == 0 and publication.get("path_leak_count") == 0,
            "evidence": {"unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"), "path_leak_count": publication.get("path_leak_count")},
        },
        {
            "name": "theorem_and_governor_ready",
            "pass": theorem.get("failed_theorem_count") == 0 and governor.get("invariant_failure_count") == 0,
            "evidence": {"failed_theorem_count": theorem.get("failed_theorem_count"), "invariant_failure_count": governor.get("invariant_failure_count")},
        },
        {
            "name": "parse_clean",
            "pass": not parse_errors,
            "evidence": {"parse_error_count": len(parse_errors), "parse_errors": parse_errors[:10]},
        },
        {
            "name": "root_hash_stable",
            "pass": verifier.get("root_release_hash") == ROOT_RELEASE_HASH and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            "evidence": {"root_release_hash": verifier.get("root_release_hash"), "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash")},
        },
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY" if not failures else "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_FAIL"
    ledger_seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "rules": [
            {
                "rule": item["rule"],
                "authority": item["authority"],
                "governance_status": item["governance_status"],
                "public_weight": item["public_weight"],
                "event_count": item["event_count"],
                "projected_count": item["projected_count"],
            }
            for item in rule_rows
        ],
    }
    return {
        "schema_version": "pnva.root_heuristic_weight_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "weight_ledger_score": _round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "rule_count": rule_count,
        "ready_rule_count": ready_rule_count,
        "controlled_legacy_rule_count": controlled_legacy_count,
        "blocked_rule_count": sum(1 for item in rule_rows if item["governance_status"] == "BLOCKED_FOR_RUNTIME_USE"),
        "total_rule_edge_count": total_rule_edges,
        "proof_complete": proof_complete,
        "projection_clean": projection_clean,
        "root_release_hash": ROOT_RELEASE_HASH,
        "heuristic_weight_ledger_hash": _sha_text(json.dumps(ledger_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "weight_model": {
            "type": "public_audit_weight_not_private_tuning",
            "formula": "0.30*support_norm + 0.25*proof_coverage + 0.20*authority_norm + 0.15*control_norm + 0.10*suppression_balance_norm",
            "authority_weight": AUTHORITY_WEIGHT,
            "boundary": "Public weights summarize evidence support and governance readiness. They are not private production thresholds.",
        },
        "checks": checks,
        "source_classification_checks": classification_checks,
        "rules": rule_rows,
        "observed_root_metrics": {
            "aggregate_event_count": no_tick.get("aggregate_event_count"),
            "aggregate_suppressed_count": no_tick.get("aggregate_suppressed_count"),
            "aggregate_suppression_ratio": no_tick.get("aggregate_suppression_ratio"),
            "heuristic_rule_count": heuristics.get("heuristic_rule_count"),
            "influence_edge_count": heuristics.get("influence_edge_count"),
            "heuristic_coverage_ratio": heuristics.get("heuristic_coverage_ratio"),
            "proof_event_coverage_ratio": heuristics.get("proof_event_coverage_ratio"),
            "native_influence_clean": heuristics.get("native_influence_clean"),
        },
        "interpretation": {
            "purpose": "Expose a deterministic public ledger of heuristic support, authority, proof coverage, no-tick behavior and entity links.",
            "sovereignty": "A heuristic becomes governable when its evidence weight, authority class and boundaries are visible.",
            "boundary": "This ledger is an audit layer. It does not publish private tuning, execute system actions or change live gates.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root heuristic weight ledger.")
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
