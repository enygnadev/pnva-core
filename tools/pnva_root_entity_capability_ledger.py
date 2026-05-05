#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
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

ENTITY_CATALOGS = {
    "canonical": "reports/pnva-entity-catalog-2026-05-05.json",
    "native": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
    "runtime_r3": "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json",
}

REPORTS = {
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "heuristic_weight_ledger": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
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
    "heuristic_weight_ledger": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "evolution_governor": "PNVA_ROOT_EVOLUTION_GOVERNOR_READY",
    "theorem_ledger": "PNVA_ROOT_PROOF_THEOREM_LEDGER_READY",
    "firewall": "PNVA_ROOT_INVARIANT_FIREWALL_READY",
    "regression": "PNVA_ROOT_REGRESSION_SENTINEL_READY",
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


def _risk_flags(event: dict[str, Any]) -> list[str]:
    heuristics = event.get("heuristics")
    if not isinstance(heuristics, dict):
        return []
    flags = heuristics.get("risk_flags")
    if not isinstance(flags, list):
        return []
    return [str(flag) for flag in flags if str(flag)]


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


def _load_catalog_rows(repo: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rows: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    for scope, rel in ENTITY_CATALOGS.items():
        try:
            data = _read_json(repo / rel)
        except Exception as exc:
            errors.append({"scope": scope, "path": rel, "error": str(exc)})
            continue
        for entity in data.get("entities", []) or []:
            if not isinstance(entity, dict) or not entity.get("entity_id"):
                errors.append({"scope": scope, "path": rel, "error": "invalid entity row"})
                continue
            key = f"{scope}:{entity['entity_id']}"
            rows[key] = {
                "ledger_key": key,
                "scope": scope,
                "catalog_path": rel,
                "entity_id": str(entity.get("entity_id")),
                "entity_type": str(entity.get("entity_type") or ""),
                "state": str(entity.get("state") or ""),
                "capabilities": [str(item) for item in entity.get("capabilities", []) or []],
                "sovereignty_domain": str(entity.get("sovereignty_domain") or ""),
                "catalog_confidence": _dig(entity, "evidence.confidence"),
                "proof_ref": _dig(entity, "evidence.proof_ref"),
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
                "rule_mix": Counter(),
                "risk_mix": Counter(),
                "source_line_count": 0,
            }
    return rows, errors


def _collect_events(repo: Path, rows: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    parse_errors: list[dict[str, Any]] = []
    total_event_count = 0
    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        total_event_count += len(events)
        for event in events:
            key = f"{scope}:{event.get('entity_id')}"
            if key not in rows:
                continue
            row = rows[key]
            decision = _decision(event)
            proof = _proof(event)
            row["event_count"] += 1
            row["decision_mix"].update([decision])
            row["rule_mix"].update(_rules(event))
            row["risk_mix"].update(_risk_flags(event))
            row["source_line_count"] += 1
            if proof.get("valid") is True and str(proof.get("proof_hash") or "").startswith("sha256:"):
                row["proof_valid_count"] += 1
            if proof.get("native") is True:
                row["native_count"] += 1
            if proof.get("projection") is True:
                row["projected_count"] += 1
            if decision in {"observe", "block"} or _dig(event, "decision.action") == "NO_ACTION":
                row["suppressed_count"] += 1
            if decision == "collapse":
                row["collapse_count"] += 1
            if decision == "observe":
                row["observe_count"] += 1
            if decision == "block":
                row["block_count"] += 1
            if decision == "prove":
                row["prove_count"] += 1
    return parse_errors, total_event_count


def _finalize_entity(row: dict[str, Any], max_event_count: int, aggregate_suppression_ratio: float) -> dict[str, Any]:
    event_count = int(row["event_count"])
    proof_coverage = _ratio(row["proof_valid_count"], event_count)
    native_ratio = _ratio(row["native_count"], event_count)
    projected_ratio = _ratio(row["projected_count"], event_count)
    suppression_ratio = _ratio(row["suppressed_count"], event_count)
    support_norm = _ratio(event_count, max_event_count)
    capability_norm = _ratio(len(row["capabilities"]), 4)
    control_norm = _round(1.0 - projected_ratio)
    balance_norm = _round(max(0.0, 1.0 - abs(suppression_ratio - aggregate_suppression_ratio)))
    readiness_score = _round(
        0.25 * support_norm
        + 0.25 * proof_coverage
        + 0.20 * capability_norm
        + 0.15 * control_norm
        + 0.15 * balance_norm
    )
    if event_count == 0 or proof_coverage < 1.0 or projected_ratio > 0.0:
        governance_status = "BLOCKED_FOR_RUNTIME_USE"
    elif row["scope"] == "runtime_r3":
        governance_status = "R3_RUNTIME_READY"
    elif row["scope"] == "native":
        governance_status = "NATIVE_READY"
    else:
        governance_status = "CONTROLLED_CANONICAL"
    return {
        "ledger_key": row["ledger_key"],
        "scope": row["scope"],
        "entity_id": row["entity_id"],
        "entity_type": row["entity_type"],
        "state": row["state"],
        "capabilities": row["capabilities"],
        "capability_count": len(row["capabilities"]),
        "sovereignty_domain": row["sovereignty_domain"],
        "catalog_confidence": row["catalog_confidence"],
        "proof_ref": row["proof_ref"],
        "governance_status": governance_status,
        "readiness_score": readiness_score,
        "readiness_components": {
            "support_norm": support_norm,
            "proof_coverage": proof_coverage,
            "capability_norm": capability_norm,
            "control_norm": control_norm,
            "suppression_balance_norm": balance_norm,
        },
        "event_count": event_count,
        "proof_valid_count": int(row["proof_valid_count"]),
        "native_count": int(row["native_count"]),
        "projected_count": int(row["projected_count"]),
        "suppressed_count": int(row["suppressed_count"]),
        "collapse_count": int(row["collapse_count"]),
        "observe_count": int(row["observe_count"]),
        "block_count": int(row["block_count"]),
        "prove_count": int(row["prove_count"]),
        "suppression_ratio": suppression_ratio,
        "native_ratio": native_ratio,
        "projected_ratio": projected_ratio,
        "decision_mix": _counter_pairs(row["decision_mix"]),
        "rule_mix": _counter_pairs(row["rule_mix"]),
        "risk_mix": _counter_pairs(row["risk_mix"]),
    }


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    obs = reports["observability"]
    heuristic_weight = reports["heuristic_weight_ledger"]
    governor = reports["evolution_governor"]
    theorem = reports["theorem_ledger"]
    firewall = reports["firewall"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]
    catalog_rows, catalog_errors = _load_catalog_rows(repo)
    parse_errors, total_event_count = _collect_events(repo, catalog_rows)
    no_tick = obs.get("no_tick_observability", {})
    entity_obs = obs.get("entity_observability", {})
    aggregate_suppression_ratio = _num(no_tick.get("aggregate_suppression_ratio"))
    max_event_count = max((int(row["event_count"]) for row in catalog_rows.values()), default=1)
    entity_rows = [
        _finalize_entity(row, max_event_count, aggregate_suppression_ratio)
        for row in catalog_rows.values()
    ]
    entity_rows = sorted(entity_rows, key=lambda item: (item["scope"], -item["readiness_score"], item["entity_id"]))
    status_counts = Counter(row["governance_status"] for row in entity_rows)
    scope_counts = Counter(row["scope"] for row in entity_rows)
    capability_mix: Counter[str] = Counter()
    type_mix: Counter[str] = Counter()
    state_mix: Counter[str] = Counter()
    for row in entity_rows:
        capability_mix.update(row["capabilities"])
        type_mix.update([row["entity_type"]])
        state_mix.update([row["state"]])

    classification_checks = _classification_checks(reports)
    total_profile_event_count = sum(row["event_count"] for row in entity_rows)
    proof_complete = all(row["readiness_components"]["proof_coverage"] == 1.0 for row in entity_rows if row["event_count"] > 0)
    projection_clean = all(row["projected_count"] == 0 for row in entity_rows)
    blocked_count = status_counts.get("BLOCKED_FOR_RUNTIME_USE", 0)
    checks = [
        {
            "name": "source_classifications_ready",
            "pass": all(item["pass"] for item in classification_checks),
            "evidence": {"failures": [item for item in classification_checks if not item["pass"]]},
        },
        {
            "name": "catalog_scope_count_ready",
            "pass": len(scope_counts) == 3 and len(entity_rows) == 13 and not catalog_errors,
            "evidence": {"scope_counts": dict(scope_counts), "entity_row_count": len(entity_rows), "catalog_errors": catalog_errors},
        },
        {
            "name": "event_coverage_complete",
            "pass": total_profile_event_count == int(_num(no_tick.get("aggregate_event_count"))) == total_event_count,
            "evidence": {
                "profile_event_count": total_profile_event_count,
                "no_tick_event_count": no_tick.get("aggregate_event_count"),
                "jsonl_event_count": total_event_count,
            },
        },
        {
            "name": "proof_coverage_complete",
            "pass": proof_complete,
            "evidence": {"incomplete_entities": [row["ledger_key"] for row in entity_rows if row["event_count"] > 0 and row["readiness_components"]["proof_coverage"] != 1.0]},
        },
        {
            "name": "projection_clean",
            "pass": projection_clean,
            "evidence": {"projected_entity_events": sum(row["projected_count"] for row in entity_rows)},
        },
        {
            "name": "runtime_r3_entity_ready",
            "pass": status_counts.get("R3_RUNTIME_READY", 0) == 1 and _dig(entity_obs, "scopes.runtime_r3.entity_count") == 1,
            "evidence": {"r3_ready_count": status_counts.get("R3_RUNTIME_READY", 0), "observability_r3_entity_count": _dig(entity_obs, "scopes.runtime_r3.entity_count")},
        },
        {
            "name": "blocked_entities_absent",
            "pass": blocked_count == 0,
            "evidence": {"blocked_entity_count": blocked_count},
        },
        {
            "name": "heuristic_weight_layer_ready",
            "pass": heuristic_weight.get("blocked_rule_count") == 0 and heuristic_weight.get("rule_count") == 9,
            "evidence": {"blocked_rule_count": heuristic_weight.get("blocked_rule_count"), "rule_count": heuristic_weight.get("rule_count")},
        },
        {
            "name": "governor_and_theorems_intact",
            "pass": governor.get("invariant_failure_count") == 0 and theorem.get("failed_theorem_count") == 0,
            "evidence": {"invariant_failure_count": governor.get("invariant_failure_count"), "failed_theorem_count": theorem.get("failed_theorem_count")},
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
    classification = "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY" if not failures else "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_FAIL"
    ledger_seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "entities": [
            {
                "ledger_key": item["ledger_key"],
                "governance_status": item["governance_status"],
                "readiness_score": item["readiness_score"],
                "event_count": item["event_count"],
                "projected_count": item["projected_count"],
            }
            for item in entity_rows
        ],
    }
    return {
        "schema_version": "pnva.root_entity_capability_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "entity_capability_score": _round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "entity_row_count": len(entity_rows),
        "scope_count": len(scope_counts),
        "profile_event_count": total_profile_event_count,
        "capability_edge_count": sum(len(row["capabilities"]) for row in entity_rows),
        "r3_runtime_ready_count": status_counts.get("R3_RUNTIME_READY", 0),
        "native_ready_count": status_counts.get("NATIVE_READY", 0),
        "controlled_canonical_count": status_counts.get("CONTROLLED_CANONICAL", 0),
        "blocked_entity_count": blocked_count,
        "proof_complete": proof_complete,
        "projection_clean": projection_clean,
        "root_release_hash": ROOT_RELEASE_HASH,
        "entity_capability_ledger_hash": _sha_text(json.dumps(ledger_seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": classification_checks,
        "status_counts": dict(sorted(status_counts.items())),
        "scope_counts": dict(sorted(scope_counts.items())),
        "type_mix": _counter_pairs(type_mix),
        "state_mix": _counter_pairs(state_mix),
        "capability_mix": _counter_pairs(capability_mix, 20),
        "entities": entity_rows,
        "observed_root_metrics": {
            "aggregate_event_count": no_tick.get("aggregate_event_count"),
            "aggregate_suppressed_count": no_tick.get("aggregate_suppressed_count"),
            "aggregate_suppression_ratio": no_tick.get("aggregate_suppression_ratio"),
            "observability_entity_rows": entity_obs.get("total_entity_rows"),
            "firewall_entity_catalog_count": _dig(firewall, "locked_invariants.entity_catalog_count"),
            "firewall_entity_catalog_rows": _dig(firewall, "locked_invariants.entity_catalog_rows"),
        },
        "interpretation": {
            "purpose": "Expose entity capability readiness across canonical, native and R3 runtime evidence.",
            "sovereignty": "An entity becomes governable when its capabilities, no-tick behavior, proof coverage, heuristic links and runtime status are visible.",
            "boundary": "This ledger is an audit layer. It does not execute system actions, change live gates or expand claims beyond public evidence.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root entity capability ledger.")
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
