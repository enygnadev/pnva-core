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

ENTITY_CATALOGS = {
    "canonical": "reports/pnva-entity-catalog-2026-05-05.json",
    "native": "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
    "runtime_r3": "reports/pnva-r3-runtime-entity-catalog-2026-05-05.json",
}

REPORTS = {
    "no_tick_contract": "reports/pnva-root-no-tick-causal-contract-2026-05-05.json",
    "field_topology": "reports/pnva-root-field-topology-ledger-2026-05-05.json",
    "heuristic_weight": "reports/pnva-root-heuristic-weight-ledger-2026-05-05.json",
    "entity_capability": "reports/pnva-root-entity-capability-ledger-2026-05-05.json",
    "causal_mesh": "reports/pnva-root-causal-mesh-ledger-2026-05-05.json",
    "publication_gate": "reports/pnva-root-publication-gate-2026-05-05.json",
    "claim_boundary": "reports/pnva-root-claim-boundary-guard-2026-05-05.json",
    "release_verifier": "reports/pnva-root-release-verifier-2026-05-05.json",
}

EXPECTED_CLASSIFICATIONS = {
    "no_tick_contract": "PNVA_ROOT_NO_TICK_CAUSAL_CONTRACT_READY",
    "field_topology": "PNVA_ROOT_FIELD_TOPOLOGY_LEDGER_READY",
    "heuristic_weight": "PNVA_ROOT_HEURISTIC_WEIGHT_LEDGER_READY",
    "entity_capability": "PNVA_ROOT_ENTITY_CAPABILITY_LEDGER_READY",
    "causal_mesh": "PNVA_ROOT_CAUSAL_MESH_LEDGER_READY",
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
        if not isinstance(item, dict):
            errors.append({"line": line_no, "error": "jsonl item is not an object"})
            continue
        item["_scope"] = path.name
        item["_line"] = line_no
        rows.append(item)
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


def _catalog_ids(repo: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for scope, rel in ENTITY_CATALOGS.items():
        data = _read_json(repo / rel)
        result[scope] = {
            str(entity.get("entity_id"))
            for entity in data.get("entities", []) or []
            if isinstance(entity, dict) and entity.get("entity_id")
        }
    return result


def _counter_pairs(counter: Counter[str], limit: int = 12) -> list[list[Any]]:
    return [[key, count] for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def build_report(repo: Path) -> dict[str, Any]:
    reports = {name: _read_json(repo / rel) for name, rel in REPORTS.items()}
    source_checks = _source_checks(reports)
    catalogs = _catalog_ids(repo)

    all_events: list[tuple[str, dict[str, Any]]] = []
    parse_errors: list[dict[str, Any]] = []
    scope_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    rule_counts: Counter[str] = Counter()
    entity_counts: Counter[str] = Counter()
    chain_counts: Counter[str] = Counter()
    r3_chain_events: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    event_ids: list[str] = []
    proof_hashes: list[str] = []
    missing_core: list[dict[str, Any]] = []
    missing_catalog_entities: list[dict[str, Any]] = []
    invalid_tension: list[dict[str, Any]] = []
    invalid_proof: list[dict[str, Any]] = []
    projected_events: list[str] = []
    native_count = 0

    for scope, rel in EVENT_STREAMS.items():
        events, errors = _read_jsonl(repo / rel)
        parse_errors.extend({"scope": scope, **item} for item in errors)
        for event in events:
            event_id = str(event.get("event_id") or "")
            proof_hash = str(_dig(event, "proof.proof_hash", ""))
            chain_id = str(event.get("causal_chain_id") or "")
            entity_id = str(event.get("entity_id") or "")
            decision = str(_dig(event, "decision.kind", ""))
            rules = [str(rule) for rule in _dig(event, "heuristics.rules", []) or [] if str(rule)]
            all_events.append((scope, event))
            scope_counts[scope] += 1
            decision_counts[decision] += 1
            rule_counts.update(rules)
            entity_counts[f"{scope}:{entity_id}"] += 1
            chain_counts[chain_id] += 1
            if scope == "runtime_r3":
                r3_chain_events[chain_id].append(event)
            if event_id:
                event_ids.append(event_id)
            if proof_hash:
                proof_hashes.append(proof_hash)
            if not event_id or not proof_hash or not chain_id or not entity_id or not decision:
                missing_core.append({"scope": scope, "line": event.get("_line"), "event_id": event_id})
            if entity_id not in catalogs.get(scope, set()):
                missing_catalog_entities.append({"scope": scope, "event_id": event_id, "entity_id": entity_id})
            if _dig(event, "proof.valid") is not True or not str(proof_hash).startswith("sha256:"):
                invalid_proof.append({"scope": scope, "event_id": event_id, "proof_hash": proof_hash})
            if _dig(event, "proof.projection") is True:
                projected_events.append(event_id)
            if _dig(event, "proof.native") is True:
                native_count += 1
            for key in ("tension.score", "tension.threshold", "tension.gate_delta"):
                if not isinstance(_dig(event, key), (int, float)):
                    invalid_tension.append({"scope": scope, "event_id": event_id, "field": key})

    event_id_dupes = [event_id for event_id, count in Counter(event_ids).items() if count > 1]
    proof_hash_dupes = [proof_hash for proof_hash, count in Counter(proof_hashes).items() if count > 1]
    chain_unique_count = len([chain_id for chain_id in chain_counts if chain_id])
    r3_pair_failures = []
    for chain_id, events in sorted(r3_chain_events.items()):
        kinds = Counter(str(_dig(event, "decision.kind", "")) for event in events)
        event_types = Counter(str(event.get("event_type", "")) for event in events)
        if len(events) != 2 or kinds.get("observe") != 1 or kinds.get("collapse") != 1 or not any("precheck" in event_type for event_type in event_types) or not any("scan" in event_type for event_type in event_types):
            r3_pair_failures.append(
                {
                    "chain_id": chain_id,
                    "event_count": len(events),
                    "decision_counts": dict(kinds),
                    "event_types": dict(event_types),
                }
            )

    no_tick = reports["no_tick_contract"]
    topology = reports["field_topology"]
    heuristic = reports["heuristic_weight"]
    capability = reports["entity_capability"]
    mesh = reports["causal_mesh"]
    publication = reports["publication_gate"]
    claim = reports["claim_boundary"]
    verifier = reports["release_verifier"]

    checks = [
        _check("source_reports_ready", all(item["pass"] for item in source_checks), {"reports": source_checks}),
        _check(
            "event_streams_parse_and_count",
            not parse_errors
            and sum(scope_counts.values()) == no_tick.get("event_count") == topology.get("event_count") == mesh.get("event_count") == 589,
            {"parse_errors": parse_errors, "scope_counts": dict(scope_counts), "root_event_count": no_tick.get("event_count")},
        ),
        _check(
            "event_and_proof_identity_unique",
            len(event_ids) == len(set(event_ids)) == len(all_events)
            and len(proof_hashes) == len(set(proof_hashes)) == len(all_events)
            and not missing_core,
            {
                "event_id_count": len(event_ids),
                "unique_event_id_count": len(set(event_ids)),
                "event_id_duplicate_count": len(event_id_dupes),
                "proof_hash_count": len(proof_hashes),
                "unique_proof_hash_count": len(set(proof_hashes)),
                "proof_hash_duplicate_count": len(proof_hash_dupes),
                "missing_core_count": len(missing_core),
                "missing_core_sample": missing_core[:10],
            },
        ),
        _check(
            "entity_binding_complete",
            not missing_catalog_entities
            and len(entity_counts) == capability.get("entity_row_count") == mesh.get("entity_count") == 13,
            {
                "entity_event_binding_count": len(entity_counts),
                "catalog_scope_counts": {scope: len(ids) for scope, ids in catalogs.items()},
                "missing_catalog_entities": missing_catalog_entities[:10],
            },
        ),
        _check(
            "heuristic_rule_identity_bound",
            len(rule_counts) == heuristic.get("rule_count") == mesh.get("rule_count") == 9
            and sum(rule_counts.values()) == heuristic.get("total_rule_edge_count") == topology.get("rule_event_edge_count") == mesh.get("rule_event_edge_count") == 1350,
            {
                "rule_count": len(rule_counts),
                "rule_event_edge_count": sum(rule_counts.values()),
                "rule_counts": _counter_pairs(rule_counts, 12),
            },
        ),
        _check(
            "decision_and_tension_contract",
            decision_counts.get("collapse") == no_tick.get("collapse_count") == 303
            and decision_counts.get("observe") == no_tick.get("observe_count") == 250
            and decision_counts.get("block") == no_tick.get("block_count") == 35
            and decision_counts.get("prove") == no_tick.get("prove_count") == 1
            and not invalid_tension,
            {"decision_counts": dict(decision_counts), "invalid_tension_count": len(invalid_tension), "invalid_tension_sample": invalid_tension[:10]},
        ),
        _check(
            "proof_policy_clean",
            not invalid_proof
            and not projected_events
            and native_count == 77
            and no_tick.get("proof_valid_count") == len(all_events),
            {
                "invalid_proof_count": len(invalid_proof),
                "projected_event_count": len(projected_events),
                "native_count": native_count,
                "proof_valid_count": no_tick.get("proof_valid_count"),
            },
        ),
        _check(
            "r3_chain_shape_clean",
            not r3_pair_failures
            and len(r3_chain_events) == no_tick.get("r3_chain_count") == mesh.get("r3_chain_count") == 35,
            {
                "r3_chain_count": len(r3_chain_events),
                "r3_pair_failure_count": len(r3_pair_failures),
                "r3_pair_failures": r3_pair_failures[:10],
                "chain_unique_count": chain_unique_count,
            },
        ),
        _check(
            "public_surface_current",
            publication.get("path_leak_count") == 0
            and claim.get("unbounded_high_risk_occurrence_count") == 0
            and publication.get("manifest_file_count", 0) >= 243
            and publication.get("checksum_count", 0) + 1 == publication.get("manifest_file_count", 0),
            {
                "manifest_file_count": publication.get("manifest_file_count"),
                "checksum_count": publication.get("checksum_count"),
                "path_leak_count": publication.get("path_leak_count"),
                "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
            },
        ),
        _check(
            "root_hash_aligned",
            verifier.get("root_release_hash") == ROOT_RELEASE_HASH and verifier.get("recomputed_root_release_hash") == ROOT_RELEASE_HASH,
            {"root_release_hash": verifier.get("root_release_hash"), "recomputed_root_release_hash": verifier.get("recomputed_root_release_hash")},
        ),
    ]
    failures = [item for item in checks if not item["pass"]]
    classification = "PNVA_ROOT_EVENT_IDENTITY_LEDGER_READY" if not failures else "PNVA_ROOT_EVENT_IDENTITY_LEDGER_FAIL"
    seed = {
        "classification": classification,
        "checks": [{"name": item["name"], "pass": item["pass"]} for item in checks],
        "event_count": len(all_events),
        "event_id_count": len(event_ids),
        "proof_hash_count": len(proof_hashes),
        "entity_binding_count": len(entity_counts),
        "rule_count": len(rule_counts),
        "r3_chain_count": len(r3_chain_events),
        "root_release_hash": ROOT_RELEASE_HASH,
    }

    return {
        "schema_version": "pnva.root_event_identity_ledger.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": not failures,
        "event_identity_score": round(100.0 * (len(checks) - len(failures)) / max(1, len(checks)), 2),
        "check_count": len(checks),
        "failure_count": len(failures),
        "event_count": len(all_events),
        "event_id_count": len(event_ids),
        "unique_event_id_count": len(set(event_ids)),
        "proof_hash_count": len(proof_hashes),
        "unique_proof_hash_count": len(set(proof_hashes)),
        "entity_binding_count": len(entity_counts),
        "rule_count": len(rule_counts),
        "rule_event_edge_count": sum(rule_counts.values()),
        "r3_chain_count": len(r3_chain_events),
        "r3_pair_failure_count": len(r3_pair_failures),
        "decision_counts": dict(decision_counts),
        "scope_counts": dict(scope_counts),
        "native_count": native_count,
        "projected_event_count": len(projected_events),
        "path_leak_count": publication.get("path_leak_count"),
        "unbounded_high_risk_occurrence_count": claim.get("unbounded_high_risk_occurrence_count"),
        "root_release_hash": ROOT_RELEASE_HASH,
        "event_identity_ledger_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "checks": checks,
        "source_classification_checks": source_checks,
        "interpretation": {
            "purpose": "Prove that PNVA root event streams have unique event IDs, unique proof hashes, catalog-bound entities, bounded heuristic rules and clean R3 precheck/commit identity.",
            "sovereignty": "A root no-tick system is stronger when every event can be identified, replayed, linked to an entity and checked against proof identity.",
            "boundary": "This ledger audits public event identity only. It does not execute actions, change live gates or alter runtime workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA root event identity ledger.")
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
