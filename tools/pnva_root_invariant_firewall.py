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
    "observability": "reports/pnva-root-observability-index-2026-05-05.json",
    "dependency_graph": "reports/pnva-root-dependency-graph-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
    "root_sovereignty": "reports/pnva-root-sovereignty-guard-2026-05-05.json",
    "root_causal_intelligence": "reports/pnva-root-causal-intelligence-2026-05-05.json",
    "root_traceability": "reports/pnva-root-traceability-matrix-2026-05-05.json",
    "root_adversarial": "reports/pnva-root-adversarial-sentry-2026-05-05.json",
    "runtime_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "runtime_contract": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
    "semantic_consistency": "reports/pnva-semantic-consistency-2026-05-05.json",
    "reproducibility": "reports/pnva-reproducibility-2026-05-05.json",
}

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

EXPECTED_CLASSIFICATIONS = {
    "observability": "PNVA_ROOT_OBSERVABILITY_INDEX_READY",
    "dependency_graph": "PNVA_ROOT_DEPENDENCY_GRAPH_READY",
    "publication_gate": "PNVA_ROOT_PUBLICATION_GATE_READY",
    "claim_boundary": "PNVA_ROOT_CLAIM_BOUNDARY_GUARD_READY",
    "release_verifier": "PNVA_ROOT_RELEASE_VERIFIED",
    "root_sovereignty": "PNVA_ROOT_SOVEREIGNTY_GUARD_READY",
    "root_causal_intelligence": "PNVA_ROOT_CAUSAL_INTELLIGENCE_READY",
    "root_traceability": "PNVA_ROOT_TRACEABILITY_MATRIX_READY",
    "root_adversarial": "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
    "runtime_guard": "R3_RUNTIME_EVIDENCE_ACCEPTED",
    "runtime_contract": "R3_RUNTIME_CONTRACT_VALIDATED_READY",
    "semantic_consistency": "SEMANTIC_CONSISTENCY_READY",
    "reproducibility": "REPRODUCIBILITY_READY",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_no, "error": str(exc)})
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
    return events, errors


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


def _event_stream_firewall(repo: Path) -> dict[str, Any]:
    streams: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    for name, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        proof_hashes = [str(_dig(event, "proof.proof_hash", "")) for event in events]
        proof_hashes = [value for value in proof_hashes if value]
        projected = [str(event.get("event_id", "")) for event in events if _dig(event, "proof.projection") is True]
        native_count = sum(1 for event in events if _dig(event, "proof.native") is True)
        missing_core = [
            str(event.get("event_id", ""))
            for event in events
            if not event.get("event_id")
            or not event.get("entity_id")
            or not event.get("causal_chain_id")
            or not _dig(event, "decision.kind")
            or not _dig(event, "proof.proof_hash")
        ]
        if errors:
            failures.append({"stream": name, "reason": "parse_errors", "count": len(errors)})
        if len(proof_hashes) != len(events) or len(set(proof_hashes)) != len(proof_hashes):
            failures.append(
                {
                    "stream": name,
                    "reason": "proof_hash_identity",
                    "event_count": len(events),
                    "proof_hash_count": len(proof_hashes),
                    "unique_proof_hash_count": len(set(proof_hashes)),
                }
            )
        if projected:
            failures.append({"stream": name, "reason": "projected_proof_present", "sample_event_ids": projected[:10]})
        if name in {"native", "runtime_r3"} and native_count != len(events):
            failures.append({"stream": name, "reason": "native_count_mismatch", "native_count": native_count, "event_count": len(events)})
        if missing_core:
            failures.append({"stream": name, "reason": "missing_core_fields", "sample_event_ids": missing_core[:10]})
        streams[name] = {
            "path": rel,
            "event_count": len(events),
            "parse_error_count": len(errors),
            "proof_hash_count": len(proof_hashes),
            "unique_proof_hash_count": len(set(proof_hashes)),
            "native_count": native_count,
            "projected_count": len(projected),
            "missing_core_count": len(missing_core),
        }
    return {"streams": streams, "failures": failures}


def _entity_catalog_firewall(repo: Path) -> dict[str, Any]:
    scopes: dict[str, Any] = {}
    failures: list[dict[str, Any]] = []
    total = 0
    for name, rel in ENTITY_CATALOGS.items():
        data = _read_json(repo / rel)
        entities = [item for item in data.get("entities", []) if isinstance(item, dict)]
        total += len(entities)
        missing_core = []
        for entity in entities:
            if (
                entity.get("schema_version") != "pnva.entity.v1"
                or not entity.get("entity_id")
                or not entity.get("entity_type")
                or not entity.get("state")
                or not _dig(entity, "evidence.proof_ref")
            ):
                missing_core.append(str(entity.get("entity_id", "")))
        if not entities:
            failures.append({"scope": name, "reason": "empty_catalog"})
        if missing_core:
            failures.append({"scope": name, "reason": "entity_core_contract", "sample_entity_ids": missing_core[:10]})
        scopes[name] = {
            "path": rel,
            "entity_count": len(entities),
            "schema_version": data.get("schema_version"),
            "missing_core_count": len(missing_core),
        }
    return {"scope_count": len(scopes), "total_entity_rows": total, "scopes": scopes, "failures": failures}


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    observability = reports["observability"]
    runtime_guard = reports["runtime_guard"]
    runtime_contract = reports["runtime_contract"]
    publication = reports["publication_gate"]
    claim_boundary = reports["claim_boundary"]
    dependency_graph = reports["dependency_graph"]
    verifier = reports["release_verifier"]

    event_firewall = _event_stream_firewall(repo)
    entity_firewall = _entity_catalog_firewall(repo)

    classification_failures = []
    for name, expected in EXPECTED_CLASSIFICATIONS.items():
        report = reports[name]
        if report.get("classification") != expected or report.get("pass") is not True:
            classification_failures.append(
                {
                    "name": name,
                    "classification": report.get("classification"),
                    "expected": expected,
                    "pass": report.get("pass"),
                }
            )

    root_hashes = {
        "observability": _dig(observability, "root_observability.root_release_hash"),
        "publication": publication.get("root_release_hash"),
        "claim_boundary": claim_boundary.get("root_release_hash"),
        "release_verifier": verifier.get("root_release_hash"),
        "release_verifier_recomputed": verifier.get("recomputed_root_release_hash"),
        "dependency_graph": dependency_graph.get("root_release_hash"),
    }
    root_hash_set = set(value for value in root_hashes.values() if value)

    no_tick = observability.get("no_tick_observability", {})
    no_tick_failures = []
    if int(_num(no_tick.get("aggregate_event_count"))) != 589:
        no_tick_failures.append({"field": "aggregate_event_count", "value": no_tick.get("aggregate_event_count")})
    if int(_num(no_tick.get("aggregate_suppressed_count"))) != 285:
        no_tick_failures.append({"field": "aggregate_suppressed_count", "value": no_tick.get("aggregate_suppressed_count")})
    if abs(_num(no_tick.get("aggregate_suppression_ratio")) - 0.483871) > 0.000001:
        no_tick_failures.append({"field": "aggregate_suppression_ratio", "value": no_tick.get("aggregate_suppression_ratio")})

    heuristic = observability.get("heuristic_observability", {})
    heuristic_failures = []
    if _num(heuristic.get("heuristic_coverage_ratio")) != 1.0:
        heuristic_failures.append({"field": "heuristic_coverage_ratio", "value": heuristic.get("heuristic_coverage_ratio")})
    if _num(heuristic.get("proof_event_coverage_ratio")) != 1.0:
        heuristic_failures.append({"field": "proof_event_coverage_ratio", "value": heuristic.get("proof_event_coverage_ratio")})
    if heuristic.get("native_influence_clean") is not True:
        heuristic_failures.append({"field": "native_influence_clean", "value": heuristic.get("native_influence_clean")})
    if int(_num(heuristic.get("heuristic_rule_count"))) < 9:
        heuristic_failures.append({"field": "heuristic_rule_count", "value": heuristic.get("heuristic_rule_count")})

    runtime_failures = []
    runtime_expectations = {
        "accepted_slot_count": 35,
        "pending_slot_count": 0,
        "rejected_event_count": 0,
        "no_tick_pair_failure_count": 0,
        "negative_control_detected_count": 63,
        "negative_control_count": 63,
    }
    for field, expected in runtime_expectations.items():
        if int(_num(runtime_guard.get(field))) != expected:
            runtime_failures.append({"field": f"runtime_guard.{field}", "expected": expected, "actual": runtime_guard.get(field)})
    if int(_num(runtime_contract.get("failure_count"))) != 0:
        runtime_failures.append({"field": "runtime_contract.failure_count", "actual": runtime_contract.get("failure_count")})
    if int(_num(runtime_contract.get("contract_check_count"))) < 315:
        runtime_failures.append({"field": "runtime_contract.contract_check_count", "actual": runtime_contract.get("contract_check_count")})

    root_score_failures = []
    for field, value in _dig(observability, "root_observability.root_scores", {}).items():
        if _num(value) != 100.0:
            root_score_failures.append({"field": field, "value": value})

    checks = [
        _check("required_reports_ready", not classification_failures, {"classification_failures": classification_failures}),
        _check("root_release_hashes_agree", len(root_hash_set) == 1, {"root_hashes": root_hashes}),
        _check("no_tick_budget_locked", not no_tick_failures, {"failures": no_tick_failures, "no_tick": {key: no_tick.get(key) for key in ["aggregate_event_count", "aggregate_suppressed_count", "aggregate_suppression_ratio"]}}),
        _check("event_stream_identity_locked", not event_firewall["failures"], event_firewall),
        _check("entity_catalog_contract_locked", not entity_firewall["failures"] and entity_firewall["total_entity_rows"] >= 13, entity_firewall),
        _check("heuristic_authority_visibility_locked", not heuristic_failures, {"failures": heuristic_failures, "heuristic": heuristic}),
        _check("runtime_r3_contract_locked", not runtime_failures, {"failures": runtime_failures}),
        _check("dependency_graph_locked", dependency_graph.get("cycle_count") == 0 and dependency_graph.get("unreachable_node_count") == 0 and dependency_graph.get("failure_count") == 0, {"cycle_count": dependency_graph.get("cycle_count"), "unreachable_node_count": dependency_graph.get("unreachable_node_count"), "failure_count": dependency_graph.get("failure_count")}),
        _check("root_scores_locked", not root_score_failures, {"root_score_failures": root_score_failures}),
        _check("publication_boundary_locked", publication.get("path_leak_count") == 0 and claim_boundary.get("unbounded_high_risk_occurrence_count") == 0, {"path_leak_count": publication.get("path_leak_count"), "unbounded_high_risk_occurrence_count": claim_boundary.get("unbounded_high_risk_occurrence_count")}),
        _check("semantic_and_reproducibility_locked", reports["semantic_consistency"].get("error_count") == 0 and reports["semantic_consistency"].get("warning_count") == 0 and reports["reproducibility"].get("failure_count") == 0, {"semantic_error_count": reports["semantic_consistency"].get("error_count"), "semantic_warning_count": reports["semantic_consistency"].get("warning_count"), "reproducibility_failure_count": reports["reproducibility"].get("failure_count")}),
        _check("adversarial_controls_locked", reports["root_adversarial"].get("detected_count") == reports["root_adversarial"].get("test_count") and runtime_guard.get("negative_control_detected_count") == runtime_guard.get("negative_control_count"), {"root_detected": reports["root_adversarial"].get("detected_count"), "root_test_count": reports["root_adversarial"].get("test_count"), "runtime_detected": runtime_guard.get("negative_control_detected_count"), "runtime_negative_count": runtime_guard.get("negative_control_count")}),
    ]
    failures = [item for item in checks if not item["pass"]]
    score = round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2)
    classification = "PNVA_ROOT_INVARIANT_FIREWALL_READY" if not failures else "PNVA_ROOT_INVARIANT_FIREWALL_BLOCKED"

    fingerprint = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "root_hashes": root_hashes,
        "no_tick": {key: no_tick.get(key) for key in ["aggregate_event_count", "aggregate_suppressed_count", "aggregate_suppression_ratio"]},
        "runtime": {key: runtime_guard.get(key) for key in runtime_expectations},
        "event_streams": event_firewall["streams"],
        "entity_catalogs": entity_firewall["scopes"],
    }

    return {
        "schema_version": "pnva.root_invariant_firewall.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "firewall_score": score,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "root_release_hash": next(iter(root_hash_set)) if len(root_hash_set) == 1 else "",
        "invariant_firewall_hash": _sha_text(json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))),
        "locked_invariants": {
            "aggregate_event_count": no_tick.get("aggregate_event_count"),
            "aggregate_suppressed_count": no_tick.get("aggregate_suppressed_count"),
            "aggregate_suppression_ratio": no_tick.get("aggregate_suppression_ratio"),
            "event_stream_count": len(EVENT_STREAMS),
            "entity_catalog_count": len(ENTITY_CATALOGS),
            "entity_catalog_rows": entity_firewall["total_entity_rows"],
            "heuristic_rule_count": heuristic.get("heuristic_rule_count"),
            "influence_edge_count": heuristic.get("influence_edge_count"),
            "runtime_accepted_slots": runtime_guard.get("accepted_slot_count"),
            "runtime_pending_slots": runtime_guard.get("pending_slot_count"),
            "runtime_rejected_events": runtime_guard.get("rejected_event_count"),
            "runtime_no_tick_pair_failures": runtime_guard.get("no_tick_pair_failure_count"),
            "root_dependency_cycles": dependency_graph.get("cycle_count"),
            "publication_path_leaks": publication.get("path_leak_count"),
            "unbounded_high_risk_claims": claim_boundary.get("unbounded_high_risk_occurrence_count"),
        },
        "event_stream_firewall": event_firewall,
        "entity_catalog_firewall": entity_firewall,
        "interpretation": {
            "purpose": "Block root regressions across PNVA/no-tick logs, entities, heuristics, runtime R3, publication hygiene and claim boundaries.",
            "sovereignty": "A root invariant firewall turns PASS into a guarded contract: future changes must preserve observable proof identity, entity identity, heuristic visibility and no-tick integrity.",
            "boundary": "This firewall validates the public evidence package and deterministic runtime sample. It does not change the root release seal.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the PNVA root invariant firewall.")
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
