#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


REPORTS = {
    "robustness_gate": "reports/pnva-sovereign-robustness-gate-2026-05-05.json",
    "r3_migration_plan": "reports/pnva-r3-migration-plan-2026-05-05.json",
    "authority_migration_ledger": "reports/pnva-authority-migration-ledger-2026-05-05.json",
    "r3_authority_projection": "reports/pnva-r3-authority-projection-summary-2026-05-05.json",
    "r3_authority_projection_replay": "reports/pnva-r3-authority-projection-replay-2026-05-05.json",
    "r3_authority_projection_policy": "reports/pnva-r3-authority-projection-policy-2026-05-05.json",
    "r3_authority_projection_no_tick": "reports/pnva-r3-authority-projection-no-tick-2026-05-05.json",
    "r3_authority_projection_entities": "reports/pnva-r3-authority-projection-entities-2026-05-05.json",
    "r3_runtime_capture_matrix": "reports/pnva-r3-runtime-capture-matrix-2026-05-05.json",
    "r3_runtime_evidence_guard": "reports/pnva-r3-runtime-evidence-guard-2026-05-05.json",
    "r3_runtime_contract_validation": "reports/pnva-r3-runtime-contract-validation-2026-05-05.json",
    "r3_runtime_replay": "reports/pnva-r3-runtime-replay-2026-05-05.json",
    "r3_runtime_policy": "reports/pnva-r3-runtime-policy-2026-05-05.json",
    "r3_runtime_no_tick": "reports/pnva-r3-runtime-no-tick-2026-05-05.json",
    "r3_runtime_proof_chain": "reports/pnva-r3-runtime-proof-chain-2026-05-05.json",
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_optional_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return _read_json(path)


def _dig(data: Any, path: list[str], default: Any = None) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def _ratio(part: int | float, total: int | float) -> float:
    return round(float(part) / max(1.0, float(total)), 6)


def _condition(name: str, passed: bool, evidence: dict[str, Any], *, required: bool = True) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "required": bool(required),
        "evidence": evidence,
    }


def _top_entity(entity_catalog: dict[str, Any]) -> dict[str, Any]:
    entities = entity_catalog.get("entities", []) if isinstance(entity_catalog, dict) else []
    if not entities:
        return {}
    first = entities[0] if isinstance(entities[0], dict) else {}
    stats = first.get("stats", {}) if isinstance(first, dict) else {}
    return {
        "entity_id": first.get("entity_id"),
        "entity_type": first.get("entity_type"),
        "state": first.get("state"),
        "sovereignty_domain": first.get("sovereignty_domain"),
        "event_count": int(stats.get("event_count", 0)) if isinstance(stats, dict) else 0,
        "top_actions": stats.get("top_actions", []) if isinstance(stats, dict) else [],
        "top_rules": stats.get("top_rules", []) if isinstance(stats, dict) else [],
        "risk_flags": stats.get("risk_flags", []) if isinstance(stats, dict) else [],
    }


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    data = {name: _read_optional_json(repo / rel) for name, rel in REPORTS.items()}

    robustness = data["robustness_gate"]
    r3 = data["r3_migration_plan"]
    ledger = data["authority_migration_ledger"]
    projection = data["r3_authority_projection"]
    replay = data["r3_authority_projection_replay"]
    policy = data["r3_authority_projection_policy"]
    no_tick = data["r3_authority_projection_no_tick"]
    entity_catalog = data["r3_authority_projection_entities"]
    runtime_matrix = data["r3_runtime_capture_matrix"]
    runtime_guard = data["r3_runtime_evidence_guard"]
    runtime_contract = data["r3_runtime_contract_validation"]
    runtime_replay = data["r3_runtime_replay"]
    runtime_policy = data["r3_runtime_policy"]
    runtime_no_tick = data["r3_runtime_no_tick"]
    runtime_proof_chain = data["r3_runtime_proof_chain"]

    legacy_debt = int(robustness.get("legacy_debt_count", 0))
    authority_candidates = int(ledger.get("candidate_event_count", 0))
    mapped_candidates = int(ledger.get("mapped_candidate_count", 0))
    projected_commits = int(projection.get("projected_commit_count", 0))
    projected_prechecks = int(projection.get("projected_precheck_count", 0))
    projected_events = int(projection.get("projected_event_count", 0))
    projected_suppressed = int(projection.get("projected_no_tick_suppression_count", 0))
    projected_low_authority = int(projection.get("projected_low_authority_strong_count", 0))
    proof_coverage = float(projection.get("proof_coverage_ratio", 0.0))

    fresh_runtime_evidence_present = runtime_guard.get("runtime_evidence_approved") is True
    verified_runtime_replacement_count = int(runtime_matrix.get("verified_runtime_slot_count", 0))
    remaining_runtime_replacement_count = max(0, authority_candidates - verified_runtime_replacement_count)

    preconditions = [
        _condition(
            "robustness_gate_pass",
            robustness.get("pass") is True and str(robustness.get("classification", "")).startswith("SOVEREIGN_ROBUSTNESS_GATE_READY"),
            {"classification": robustness.get("classification"), "readiness_level": robustness.get("readiness_level")},
        ),
        _condition(
            "r3_plan_pass",
            r3.get("pass") is True and r3.get("classification") == "R3_MIGRATION_PLAN_READY",
            {"classification": r3.get("classification"), "primary_blocking_debt_count": r3.get("primary_blocking_debt_count")},
        ),
        _condition(
            "authority_ledger_full_mapping",
            ledger.get("pass") is True
            and int(ledger.get("unmapped_candidate_count", 1)) == 0
            and float(ledger.get("migration_coverage_ratio", 0.0)) == 1.0,
            {
                "classification": ledger.get("classification"),
                "candidate_event_count": authority_candidates,
                "mapped_candidate_count": mapped_candidates,
                "migration_coverage_ratio": ledger.get("migration_coverage_ratio"),
            },
        ),
        _condition(
            "projection_covers_authority_debt",
            projection.get("pass") is True
            and projection.get("classification") == "R3_AUTHORITY_PROJECTION_READY"
            and projected_commits == authority_candidates
            and projected_prechecks == authority_candidates,
            {
                "classification": projection.get("classification"),
                "projected_precheck_count": projected_prechecks,
                "projected_commit_count": projected_commits,
                "authority_candidate_count": authority_candidates,
            },
        ),
        _condition(
            "projection_has_no_low_authority_strong_decisions",
            projected_low_authority == 0,
            {"projected_low_authority_strong_count": projected_low_authority},
        ),
        _condition(
            "projection_replay_policy_no_tick_pass",
            replay.get("classification") == "REPLAY_VALID"
            and replay.get("pass") is True
            and policy.get("classification") == "SOVEREIGN_POLICY_READY"
            and policy.get("pass") is True
            and no_tick.get("classification") == "SOVEREIGN_NO_TICK_READY"
            and no_tick.get("pass") is True,
            {
                "replay": replay.get("classification"),
                "policy": policy.get("classification"),
                "no_tick": no_tick.get("classification"),
            },
        ),
        _condition(
            "projection_no_tick_pairing",
            projected_suppressed == projected_prechecks and projected_events == projected_prechecks + projected_commits,
            {
                "projected_event_count": projected_events,
                "projected_precheck_count": projected_prechecks,
                "projected_commit_count": projected_commits,
                "projected_no_tick_suppression_count": projected_suppressed,
            },
        ),
        _condition(
            "projection_proof_full_coverage",
            proof_coverage == 1.0,
            {"proof_coverage_ratio": proof_coverage},
        ),
    ]

    precondition_failures = [item for item in preconditions if item["required"] and not item["pass"]]
    contract_ready = not precondition_failures

    runtime_matrix_complete = (
        runtime_matrix.get("pass") is True
        and runtime_matrix.get("classification") == "R3_RUNTIME_CAPTURE_MATRIX_COMPLETE"
        and runtime_matrix.get("runtime_capture_complete") is True
        and runtime_matrix.get("runtime_capture_approved") is True
        and verified_runtime_replacement_count == authority_candidates
        and int(runtime_matrix.get("pending_slot_count", -1)) == 0
    )
    runtime_guard_accepted = (
        runtime_guard.get("pass") is True
        and runtime_guard.get("classification") == "R3_RUNTIME_EVIDENCE_ACCEPTED"
        and runtime_guard.get("runtime_evidence_approved") is True
        and int(runtime_guard.get("accepted_slot_count", 0)) == authority_candidates
        and int(runtime_guard.get("rejected_event_count", -1)) == 0
    )
    runtime_validators_ready = (
        runtime_replay.get("pass") is True
        and runtime_replay.get("classification") == "REPLAY_VALID"
        and runtime_policy.get("pass") is True
        and runtime_policy.get("classification") == "SOVEREIGN_POLICY_READY"
        and runtime_no_tick.get("pass") is True
        and runtime_no_tick.get("classification") == "SOVEREIGN_NO_TICK_READY"
        and runtime_proof_chain.get("pass") is True
        and runtime_proof_chain.get("classification") == "PROOF_CHAIN_SEALED"
        and runtime_contract.get("pass") is True
        and runtime_contract.get("contract_validation_ready") is True
        and runtime_contract.get("runtime_evidence_approved") is True
    )

    runtime_requirements = [
        {
            "requirement_id": "CUTOVER-R1",
            "status": "complete" if runtime_guard_accepted and runtime_matrix_complete else "pending",
            "title": "Capture fresh native runtime evidence for the mapped authority debt.",
            "required_count": authority_candidates,
            "verified_count": verified_runtime_replacement_count,
            "remaining_count": remaining_runtime_replacement_count,
            "validation": "Run replay, sovereign policy and no-tick invariant analysis over the fresh native runtime event sample.",
        },
        {
            "requirement_id": "CUTOVER-R2",
            "status": "complete" if runtime_guard_accepted else "pending",
            "title": "Replace projected candidate events with runtime-emitted pnva.event.v1 events.",
            "required_count": projected_events,
            "verified_count": int(runtime_guard.get("runtime_event_count", 0)),
            "remaining_count": max(0, projected_events - int(runtime_guard.get("runtime_event_count", 0))),
            "validation": "Published runtime events must not contain proof.projection=true for the final R3 claim.",
        },
        {
            "requirement_id": "CUTOVER-R3",
            "status": "complete" if runtime_validators_ready else "pending",
            "title": "Re-run robustness, maturity, semantic consistency and reproducibility after the fresh sample is published.",
            "required_count": 4,
            "verified_count": 4 if runtime_validators_ready else 0,
            "remaining_count": 0 if runtime_validators_ready else 4,
            "validation": "R3 can only be claimed when the new public package remains internally consistent and reproducible.",
        },
    ]

    runtime_blocker_count = sum(1 for item in runtime_requirements if item["status"] != "complete")
    cutover_approved = (
        contract_ready
        and fresh_runtime_evidence_present
        and runtime_matrix_complete
        and runtime_guard_accepted
        and runtime_validators_ready
        and runtime_blocker_count == 0
        and remaining_runtime_replacement_count == 0
    )
    legacy_free_claim_allowed = cutover_approved

    classification = "R3_CUTOVER_GATE_FAIL"
    if contract_ready and cutover_approved:
        classification = "R3_CUTOVER_APPROVED"
    elif contract_ready:
        classification = "R3_CUTOVER_GATE_READY_RUNTIME_REQUIRED"

    contract_score = 100 if contract_ready else round(100 * (len(preconditions) - len(precondition_failures)) / max(1, len(preconditions)))
    runtime_replacement_coverage_ratio = _ratio(verified_runtime_replacement_count, authority_candidates)

    return {
        "schema_version": "pnva.r3_cutover_gate.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": contract_ready,
        "contract_ready": contract_ready,
        "cutover_approved": cutover_approved,
        "legacy_free_claim_allowed": legacy_free_claim_allowed,
        "fresh_runtime_evidence_present": fresh_runtime_evidence_present,
        "runtime_evidence_required": not fresh_runtime_evidence_present,
        "source_readiness_level": robustness.get("readiness_level"),
        "target_readiness_level": "R3_NATIVE_CLEAN_LEGACY_FREE",
        "source_event_count": int(robustness.get("event_count", 0)),
        "legacy_debt_count": legacy_debt,
        "authority_candidate_count": authority_candidates,
        "mapped_candidate_count": mapped_candidates,
        "projected_event_count": projected_events,
        "projected_native_event_count": int(projection.get("projected_native_event_count", 0)),
        "projected_precheck_count": projected_prechecks,
        "projected_commit_count": projected_commits,
        "projected_low_authority_strong_count": projected_low_authority,
        "projected_no_tick_suppression_count": projected_suppressed,
        "projected_no_tick_suppression_ratio": float(projection.get("projected_no_tick_suppression_ratio", 0.0)),
        "proof_coverage_ratio": proof_coverage,
        "verified_runtime_replacement_count": verified_runtime_replacement_count,
        "remaining_runtime_replacement_count": remaining_runtime_replacement_count,
        "runtime_replacement_coverage_ratio": runtime_replacement_coverage_ratio,
        "runtime_requirement_count": len(runtime_requirements),
        "runtime_blocker_count": runtime_blocker_count,
        "precondition_count": len(preconditions),
        "precondition_failure_count": len(precondition_failures),
        "contract_score": contract_score,
        "dominant_entity": _top_entity(entity_catalog),
        "preconditions": preconditions,
        "runtime_requirements": runtime_requirements,
        "reports_checked": REPORTS,
        "summary": {
            "contract_ready": contract_ready,
            "cutover_approved": cutover_approved,
            "legacy_free_claim_allowed": legacy_free_claim_allowed,
            "authority_candidate_count": authority_candidates,
            "projected_commit_count": projected_commits,
            "projected_precheck_count": projected_prechecks,
            "remaining_runtime_replacement_count": remaining_runtime_replacement_count,
            "runtime_blocker_count": runtime_blocker_count,
            "runtime_replacement_coverage_ratio": runtime_replacement_coverage_ratio,
        },
        "interpretation": {
            "purpose": "Decide whether PNVA can safely move from projected R3 authority replacement into a real runtime cutover.",
            "sovereignty": "A release is stronger when it separates implementation contract readiness from the final legacy-free claim.",
            "boundary": "This gate does not erase historical H0 evidence. It approves R3 cutover only for the slot-bound native runtime replacement sample while preserving older legacy evidence as historical migration context.",
        },
        "recommendations": [
            "Use this gate as the final checklist for the public R3 runtime package.",
            "Keep the deterministic runtime sample and its validators published with the attestation.",
            "Preserve historical legacy evidence instead of deleting it from the R2 migration trail.",
            "Use the same slot-bound guard for any future private production runtime captures.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the PNVA R3 runtime cutover gate.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    raw = json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
