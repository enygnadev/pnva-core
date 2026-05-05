#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


REQUIRED_PROOFS = {
    "guard-rail-report.json": "guard_rails",
    "prove-distribution-gate.json": "distribution_gate",
    "prove-long-run-live-gate.json": "long_run_live_gate",
    "prove-long-run-stability-12h-live.json": "12h",
    "prove-long-run-stability-15m-live.json": "15m",
    "prove-long-run-stability-24h-live.json": "24h",
    "prove-long-run-stability-8h-live.json": "8h",
    "prove-production-candidate.json": "production_candidate",
    "prove-real-stable-opportunity-capture.json": "g1",
}

DISCOVERY_TOKENS = [
    "OAI-SearchBot",
    "GPTBot",
    "ChatGPT-User",
    "Googlebot",
    "Bingbot",
    "Sitemap:",
]

PUBLIC_DOCS = [
    "docs/PNVA_ARCHITECTURE.md",
    "docs/VALIDATION_PROTOCOL.md",
    "docs/PROOF_MATRIX.md",
    "docs/LIMITATIONS.md",
    "docs/VEON_MODEL_VALIDATION.md",
    "docs/PNVA_SOVEREIGN_LOGS_ENTITIES_HEURISTICS.md",
    "docs/PNVA_CANONICAL_EVENT_BRIDGE.md",
    "docs/PNVA_ROBUSTNESS_EVOLUTION_REPORT_2026-05-05.md",
    "docs/PNVA_NO_TICK_INVARIANTS.md",
    "docs/PNVA_NATIVE_EVENT_EMITTER.md",
    "docs/PNVA_SOVEREIGN_POLICY_VALIDATION.md",
    "docs/PNVA_PROOF_CHAIN_SEALING.md",
    "docs/PNVA_CAUSAL_GRAPH_AUDIT.md",
    "docs/PNVA_SCHEMA_CONTRACT_VALIDATION.md",
    "docs/PNVA_CAUSAL_CHRONOLOGY_GUARD.md",
    "docs/PNVA_TENSION_DECISION_CALIBRATION.md",
    "docs/PNVA_SOVEREIGN_EVIDENCE_ATTESTATION.md",
    "docs/PNVA_ADVERSARIAL_VALIDATION.md",
    "docs/PNVA_ENTITY_HEURISTIC_MATURITY.md",
    "docs/PNVA_SEMANTIC_CONSISTENCY_GUARD.md",
    "docs/PNVA_REPRODUCIBILITY_GUARD.md",
    "paper/PNVA_CORE_OPEN_RESEARCH_PAPER.md",
]

SCHEMAS = [
    "schemas/pnva-event.schema.json",
    "schemas/pnva-entity.schema.json",
]

BRIDGE_FILES = [
    "tools/pnva_canonical_bridge.py",
    "reports/pnva-canonical-events-sample-2026-05-05.jsonl",
    "reports/pnva-entity-catalog-2026-05-05.json",
    "reports/pnva-canonical-bridge-summary-2026-05-05.json",
]

REPLAY_FILES = [
    "tools/pnva_replay_validator.py",
    "reports/pnva-replay-validation-2026-05-05.json",
    "docs/PNVA_REPLAY_VALIDATION.md",
]

NO_TICK_INVARIANT_FILES = [
    "tools/pnva_no_tick_invariant_analyzer.py",
    "reports/pnva-no-tick-invariants-2026-05-05.json",
    "docs/PNVA_NO_TICK_INVARIANTS.md",
]

NATIVE_EMITTER_FILES = [
    "tools/pnva_native_event_emitter.py",
    "docs/PNVA_NATIVE_EVENT_EMITTER.md",
    "reports/pnva-native-events-demo-2026-05-05.jsonl",
    "reports/pnva-native-entity-catalog-demo-2026-05-05.json",
    "reports/pnva-native-emitter-summary-2026-05-05.json",
    "reports/pnva-native-replay-validation-2026-05-05.json",
    "reports/pnva-native-no-tick-invariants-2026-05-05.json",
]

SOVEREIGN_POLICY_FILES = [
    "tools/pnva_sovereign_policy_validator.py",
    "docs/PNVA_SOVEREIGN_POLICY_VALIDATION.md",
    "reports/pnva-sovereign-policy-2026-05-05.json",
    "reports/pnva-native-sovereign-policy-2026-05-05.json",
]

PROOF_CHAIN_FILES = [
    "tools/pnva_proof_chain_sealer.py",
    "docs/PNVA_PROOF_CHAIN_SEALING.md",
    "reports/pnva-proof-chain-2026-05-05.json",
    "reports/pnva-native-proof-chain-2026-05-05.json",
]

CAUSAL_GRAPH_FILES = [
    "tools/pnva_causal_graph_auditor.py",
    "docs/PNVA_CAUSAL_GRAPH_AUDIT.md",
    "reports/pnva-causal-graph-2026-05-05.json",
    "reports/pnva-native-causal-graph-2026-05-05.json",
]

SCHEMA_CONTRACT_FILES = [
    "tools/pnva_schema_contract_validator.py",
    "docs/PNVA_SCHEMA_CONTRACT_VALIDATION.md",
    "reports/pnva-schema-contract-validation-2026-05-05.json",
]

CAUSAL_CHRONOLOGY_FILES = [
    "tools/pnva_causal_chronology_guard.py",
    "docs/PNVA_CAUSAL_CHRONOLOGY_GUARD.md",
    "reports/pnva-causal-chronology-2026-05-05.json",
]

TENSION_DECISION_FILES = [
    "tools/pnva_tension_decision_calibrator.py",
    "docs/PNVA_TENSION_DECISION_CALIBRATION.md",
    "reports/pnva-tension-decision-calibration-2026-05-05.json",
]

EVIDENCE_ATTESTATION_FILES = [
    "tools/pnva_evidence_attestor.py",
    "docs/PNVA_SOVEREIGN_EVIDENCE_ATTESTATION.md",
    "reports/pnva-sovereign-evidence-attestation-2026-05-05.json",
]

ADVERSARIAL_VALIDATION_FILES = [
    "tools/pnva_adversarial_validator.py",
    "docs/PNVA_ADVERSARIAL_VALIDATION.md",
    "reports/pnva-adversarial-validation-2026-05-05.json",
]

ENTITY_HEURISTIC_MATURITY_FILES = [
    "tools/pnva_entity_heuristic_maturity.py",
    "docs/PNVA_ENTITY_HEURISTIC_MATURITY.md",
    "reports/pnva-entity-heuristic-maturity-2026-05-05.json",
]

SEMANTIC_CONSISTENCY_FILES = [
    "tools/pnva_semantic_consistency_guard.py",
    "docs/PNVA_SEMANTIC_CONSISTENCY_GUARD.md",
    "reports/pnva-semantic-consistency-2026-05-05.json",
]

REPRODUCIBILITY_FILES = [
    "tools/pnva_reproducibility_guard.py",
    "docs/PNVA_REPRODUCIBILITY_GUARD.md",
    "reports/pnva-reproducibility-2026-05-05.json",
]

LOCAL_LOG_CANDIDATES = [
    Path.home() / ".local" / "state" / "miniggpueny" / "pnva_decisions.jsonl",
    Path.home() / ".local" / "state" / "miniggpueny" / "pnva_causal_events.jsonl",
    Path.home() / ".local" / "state" / "miniggpueny" / "zano_pnva_heuristics.jsonl",
    Path.home() / "logs" / "pnva-miner-events.jsonl",
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proof_pass(data: Any) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("pass") is True:
        return True
    if data.get("canonical_pass") is True:
        return True
    if data.get("overall_status") == "PASS":
        return True
    return False


def _safe_ratio(part: int | float, total: int | float) -> float:
    return float(part) / max(1.0, float(total))


def _round(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def audit_proofs(repo: Path) -> dict[str, Any]:
    proof_dir = repo / "proofs" / "sanitized"
    found: dict[str, Any] = {}
    missing: list[str] = []
    failed: list[str] = []
    classifications: dict[str, str] = {}
    for file_name, gate_name in REQUIRED_PROOFS.items():
        path = proof_dir / file_name
        if not path.exists():
            missing.append(file_name)
            continue
        data = _read_json(path)
        passed = _proof_pass(data)
        if not passed:
            failed.append(file_name)
        classification = ""
        if isinstance(data, dict):
            classification = str(data.get("classification") or "")
        classifications[gate_name] = classification
        found[gate_name] = {
            "file": str(path.relative_to(repo)),
            "pass": passed,
            "classification": classification,
            "sha256": _sha256(path),
        }
    index_path = proof_dir / "INDEX.json"
    index_ok = False
    if index_path.exists():
        index = _read_json(index_path)
        if isinstance(index, list):
            indexed = {str(item.get("artifact", "")) for item in index if isinstance(item, dict)}
            index_ok = set(REQUIRED_PROOFS).issubset(indexed)
    h24 = found.get("24h", {})
    h24_canonical = bool(h24.get("pass")) and h24.get("classification") == "PASS_EVENT_AWARE_24H_FINAL_TRANSIENT_STABLE_WINDOW"
    return {
        "proof_count": len(found),
        "required_count": len(REQUIRED_PROOFS),
        "missing": missing,
        "failed": failed,
        "index_ok": index_ok,
        "h24_canonical_pass_ok": h24_canonical,
        "gates": found,
    }


def audit_discovery(repo: Path) -> dict[str, Any]:
    robots_path = repo / "robots.txt"
    llms_path = repo / "llms.txt"
    sitemap_path = repo / "sitemap.xml"
    robots = robots_path.read_text(encoding="utf-8") if robots_path.exists() else ""
    llms = llms_path.read_text(encoding="utf-8") if llms_path.exists() else ""
    missing_tokens = [token for token in DISCOVERY_TOKENS if token not in robots]
    sitemap_ok = False
    sitemap_urls: list[str] = []
    if sitemap_path.exists():
        root = ET.parse(sitemap_path).getroot()
        sitemap_ok = root.tag.endswith("urlset")
        for node in root.iter():
            if node.tag.endswith("loc") and node.text:
                sitemap_urls.append(node.text.strip())
    return {
        "robots_ok": robots_path.exists() and not missing_tokens,
        "robots_missing_tokens": missing_tokens,
        "llms_ok": llms_path.exists() and "Gustavo de Aguiar Martins" in llms and "PNVA-Core" in llms,
        "sitemap_ok": sitemap_ok,
        "sitemap_url_count": len(sitemap_urls),
        "sitemap_urls": sitemap_urls,
    }


def audit_contract(repo: Path) -> dict[str, Any]:
    schema_results: dict[str, Any] = {}
    missing = []
    invalid = []
    for rel in SCHEMAS:
        path = repo / rel
        if not path.exists():
            missing.append(rel)
            continue
        try:
            data = _read_json(path)
            schema_results[rel] = {
                "ok": bool(data.get("$schema")) and bool(data.get("title")),
                "id": data.get("$id"),
                "required_count": len(data.get("required", [])),
            }
            if not schema_results[rel]["ok"]:
                invalid.append(rel)
        except Exception as exc:
            schema_results[rel] = {"ok": False, "error": str(exc)}
            invalid.append(rel)
    return {
        "schemas_ok": not missing and not invalid,
        "missing": missing,
        "invalid": invalid,
        "schemas": schema_results,
    }


def audit_canonical_bridge(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in BRIDGE_FILES if not (repo / rel).exists()]
    sample_path = repo / "reports" / "pnva-canonical-events-sample-2026-05-05.jsonl"
    entity_path = repo / "reports" / "pnva-entity-catalog-2026-05-05.json"
    summary_path = repo / "reports" / "pnva-canonical-bridge-summary-2026-05-05.json"
    event_count = 0
    bad_events = 0
    required = {
        "schema_version",
        "event_id",
        "timestamp",
        "causal_chain_id",
        "entity_id",
        "event_type",
        "field",
        "tension",
        "decision",
        "proof",
    }
    if sample_path.exists():
        with sample_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event_count += 1
                try:
                    data = json.loads(line)
                except Exception:
                    bad_events += 1
                    continue
                if not isinstance(data, dict) or data.get("schema_version") != "pnva.event.v1" or required.difference(data):
                    bad_events += 1
    entity_count = 0
    entity_catalog_ok = False
    if entity_path.exists():
        data = _read_json(entity_path)
        entity_count = int(data.get("entity_count", 0)) if isinstance(data, dict) else 0
        entity_catalog_ok = isinstance(data, dict) and data.get("schema_version") == "pnva.entity_catalog.v1" and entity_count > 0
    summary_ok = False
    public_safety_ok = False
    if summary_path.exists():
        data = _read_json(summary_path)
        summary_ok = isinstance(data, dict) and data.get("schema_version") == "pnva.canonical_bridge_summary.v1"
        safety = data.get("public_safety", {}) if isinstance(data, dict) else {}
        public_safety_ok = (
            safety.get("raw_ids_published") is False
            and safety.get("raw_paths_published") is False
            and safety.get("ids_hashed") is True
        )
    return {
        "bridge_ok": not missing and event_count > 0 and bad_events == 0 and entity_catalog_ok and summary_ok and public_safety_ok,
        "missing": missing,
        "event_count": event_count,
        "bad_events": bad_events,
        "entity_count": entity_count,
        "entity_catalog_ok": entity_catalog_ok,
        "summary_ok": summary_ok,
        "public_safety_ok": public_safety_ok,
    }


def audit_replay_validation(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in REPLAY_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-replay-validation-2026-05-05.json"
    if not report_path.exists():
        return {
            "replay_ok": False,
            "missing": missing,
            "event_count": 0,
            "proof_hash_ok": 0,
            "proof_hash_bad": 0,
            "errors": ["missing replay report"],
        }
    data = _read_json(report_path)
    summary = data.get("summary", {}) if isinstance(data, dict) else {}
    errors = data.get("errors", []) if isinstance(data, dict) else ["invalid replay report"]
    return {
        "replay_ok": not missing and data.get("pass") is True and not errors,
        "missing": missing,
        "classification": data.get("classification"),
        "event_count": int(summary.get("event_count", 0)),
        "chain_count": int(summary.get("chain_count", 0)),
        "proof_hash_ok": int(summary.get("proof_hash_ok", 0)),
        "proof_hash_bad": int(summary.get("proof_hash_bad", 0)),
        "guard_pass_ok": int(summary.get("guard_pass_ok", 0)),
        "guard_block_ok": int(summary.get("guard_block_ok", 0)),
        "warning_count": len(data.get("warnings", [])) if isinstance(data, dict) else 0,
        "errors": errors,
    }


def audit_no_tick_invariants(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in NO_TICK_INVARIANT_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-no-tick-invariants-2026-05-05.json"
    if not report_path.exists():
        return {
            "invariants_ok": False,
            "missing": missing,
            "classification": "NO_TICK_INVARIANTS_MISSING",
            "errors": ["missing no-tick invariant report"],
        }
    data = _read_json(report_path)
    failed = data.get("failed_invariants", []) if isinstance(data, dict) else ["invalid no-tick invariant report"]
    efficiency = data.get("no_tick_efficiency", {}) if isinstance(data, dict) else {}
    return {
        "invariants_ok": not missing and data.get("pass") is True and not failed,
        "missing": missing,
        "classification": data.get("classification"),
        "failed_invariants": failed,
        "event_count": int(efficiency.get("event_count", 0)),
        "suppressed_count": int(efficiency.get("suppressed_count", 0)),
        "no_tick_suppression_ratio": float(efficiency.get("no_tick_suppression_ratio", 0.0)),
        "guard_consistency_ratio": float(efficiency.get("guard_consistency_ratio", 0.0)),
        "proof_integrity_ratio": float(efficiency.get("proof_integrity_ratio", 0.0)),
    }


def audit_native_emitter(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in NATIVE_EMITTER_FILES if not (repo / rel).exists()]
    summary_path = repo / "reports" / "pnva-native-emitter-summary-2026-05-05.json"
    replay_path = repo / "reports" / "pnva-native-replay-validation-2026-05-05.json"
    invariants_path = repo / "reports" / "pnva-native-no-tick-invariants-2026-05-05.json"
    if not summary_path.exists():
        return {
            "native_ok": False,
            "missing": missing,
            "classification": "NATIVE_EMITTER_MISSING",
            "errors": ["missing native emitter summary"],
        }
    summary = _read_json(summary_path)
    replay = _read_json(replay_path) if replay_path.exists() else {}
    invariants = _read_json(invariants_path) if invariants_path.exists() else {}
    efficiency = invariants.get("no_tick_efficiency", {}) if isinstance(invariants, dict) else {}
    native_ok = (
        not missing
        and summary.get("pass") is True
        and summary.get("classification") == "NATIVE_EMITTER_READY"
        and replay.get("pass") is True
        and replay.get("classification") == "REPLAY_VALID"
        and invariants.get("pass") is True
        and invariants.get("classification") == "SOVEREIGN_NO_TICK_READY"
    )
    return {
        "native_ok": native_ok,
        "missing": missing,
        "classification": summary.get("classification"),
        "replay_classification": replay.get("classification"),
        "invariant_classification": invariants.get("classification"),
        "event_count": int(summary.get("event_count", 0)),
        "native_event_count": int(summary.get("native_event_count", 0)),
        "entity_count": int(summary.get("entity_count", 0)),
        "suppressed_count": int(summary.get("suppressed_count", 0)),
        "no_tick_suppression_ratio": float(efficiency.get("no_tick_suppression_ratio", 0.0)),
        "guard_consistency_ratio": float(efficiency.get("guard_consistency_ratio", 0.0)),
        "proof_integrity_ratio": float(efficiency.get("proof_integrity_ratio", 0.0)),
    }


def audit_sovereign_policy(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in SOVEREIGN_POLICY_FILES if not (repo / rel).exists()]
    canonical_path = repo / "reports" / "pnva-sovereign-policy-2026-05-05.json"
    native_path = repo / "reports" / "pnva-native-sovereign-policy-2026-05-05.json"
    if not canonical_path.exists() or not native_path.exists():
        return {
            "policy_ok": False,
            "missing": missing,
            "classification": "SOVEREIGN_POLICY_MISSING",
            "errors": ["missing sovereign policy reports"],
        }
    canonical = _read_json(canonical_path)
    native = _read_json(native_path)
    canonical_summary = canonical.get("summary", {}) if isinstance(canonical, dict) else {}
    native_summary = native.get("summary", {}) if isinstance(native, dict) else {}
    canonical_errors = canonical.get("errors", []) if isinstance(canonical, dict) else ["invalid canonical policy report"]
    native_errors = native.get("errors", []) if isinstance(native, dict) else ["invalid native policy report"]
    return {
        "policy_ok": not missing and canonical.get("pass") is True and native.get("pass") is True and not canonical_errors and not native_errors,
        "missing": missing,
        "classification": canonical.get("classification"),
        "native_classification": native.get("classification"),
        "canonical_event_count": int(canonical_summary.get("event_count", 0)),
        "canonical_strong_decision_count": int(canonical_summary.get("strong_decision_count", 0)),
        "canonical_low_authority_legacy_count": int(canonical_summary.get("low_authority_legacy_count", 0)),
        "canonical_warning_count": len(canonical.get("warnings", [])) if isinstance(canonical, dict) else 0,
        "native_event_count": int(native_summary.get("event_count", 0)),
        "native_strong_decision_count": int(native_summary.get("strong_decision_count", 0)),
        "native_low_authority_legacy_count": int(native_summary.get("low_authority_legacy_count", 0)),
        "native_warning_count": len(native.get("warnings", [])) if isinstance(native, dict) else 0,
        "errors": canonical_errors + native_errors,
    }


def audit_proof_chain(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in PROOF_CHAIN_FILES if not (repo / rel).exists()]
    canonical_path = repo / "reports" / "pnva-proof-chain-2026-05-05.json"
    native_path = repo / "reports" / "pnva-native-proof-chain-2026-05-05.json"
    if not canonical_path.exists() or not native_path.exists():
        return {
            "chain_ok": False,
            "missing": missing,
            "classification": "PROOF_CHAIN_MISSING",
            "errors": ["missing proof chain reports"],
        }
    canonical = _read_json(canonical_path)
    native = _read_json(native_path)
    canonical_seal = canonical.get("seal", {}) if isinstance(canonical, dict) else {}
    native_seal = native.get("seal", {}) if isinstance(native, dict) else {}
    canonical_errors = canonical.get("errors", []) if isinstance(canonical, dict) else ["invalid canonical proof chain report"]
    native_errors = native.get("errors", []) if isinstance(native, dict) else ["invalid native proof chain report"]
    return {
        "chain_ok": not missing and canonical.get("pass") is True and native.get("pass") is True and not canonical_errors and not native_errors,
        "missing": missing,
        "classification": canonical.get("classification"),
        "native_classification": native.get("classification"),
        "canonical_event_count": int(canonical_seal.get("event_count", 0)),
        "canonical_unique_event_ids": int(canonical_seal.get("unique_event_ids", 0)),
        "canonical_proof_bad": int(canonical_seal.get("proof_bad", 0)),
        "canonical_final_chain_hash": canonical_seal.get("final_chain_hash"),
        "canonical_checkpoint_count": len(canonical_seal.get("checkpoints", [])) if isinstance(canonical_seal.get("checkpoints", []), list) else 0,
        "native_event_count": int(native_seal.get("event_count", 0)),
        "native_unique_event_ids": int(native_seal.get("unique_event_ids", 0)),
        "native_proof_bad": int(native_seal.get("proof_bad", 0)),
        "native_final_chain_hash": native_seal.get("final_chain_hash"),
        "native_checkpoint_count": len(native_seal.get("checkpoints", [])) if isinstance(native_seal.get("checkpoints", []), list) else 0,
        "errors": canonical_errors + native_errors,
    }


def audit_causal_graph(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in CAUSAL_GRAPH_FILES if not (repo / rel).exists()]
    canonical_path = repo / "reports" / "pnva-causal-graph-2026-05-05.json"
    native_path = repo / "reports" / "pnva-native-causal-graph-2026-05-05.json"
    if not canonical_path.exists() or not native_path.exists():
        return {
            "graph_ok": False,
            "missing": missing,
            "classification": "CAUSAL_GRAPH_MISSING",
            "errors": ["missing causal graph reports"],
        }
    canonical = _read_json(canonical_path)
    native = _read_json(native_path)
    canonical_summary = canonical.get("summary", {}) if isinstance(canonical, dict) else {}
    native_summary = native.get("summary", {}) if isinstance(native, dict) else {}
    canonical_errors = canonical.get("errors", []) if isinstance(canonical, dict) else ["invalid canonical graph report"]
    native_errors = native.get("errors", []) if isinstance(native, dict) else ["invalid native graph report"]
    return {
        "graph_ok": not missing and canonical.get("pass") is True and native.get("pass") is True and not canonical_errors and not native_errors,
        "missing": missing,
        "classification": canonical.get("classification"),
        "native_classification": native.get("classification"),
        "canonical_event_count": int(canonical_summary.get("event_count", 0)),
        "canonical_observed_entity_count": int(canonical_summary.get("observed_entity_count", 0)),
        "canonical_catalog_entity_count": int(canonical_summary.get("catalog_entity_count", 0)),
        "canonical_chain_count": int(canonical_summary.get("chain_count", 0)),
        "canonical_relation_edge_count": int(canonical_summary.get("relation_edge_count", 0)),
        "canonical_chain_edge_count": int(canonical_summary.get("chain_edge_count", 0)),
        "canonical_graph_hash": canonical_summary.get("graph_hash"),
        "native_event_count": int(native_summary.get("event_count", 0)),
        "native_observed_entity_count": int(native_summary.get("observed_entity_count", 0)),
        "native_catalog_entity_count": int(native_summary.get("catalog_entity_count", 0)),
        "native_chain_count": int(native_summary.get("chain_count", 0)),
        "native_relation_edge_count": int(native_summary.get("relation_edge_count", 0)),
        "native_chain_edge_count": int(native_summary.get("chain_edge_count", 0)),
        "native_graph_hash": native_summary.get("graph_hash"),
        "errors": canonical_errors + native_errors,
    }


def audit_evidence_attestation(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in EVIDENCE_ATTESTATION_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-sovereign-evidence-attestation-2026-05-05.json"
    if not report_path.exists():
        return {
            "attestation_ok": False,
            "missing": missing,
            "classification": "EVIDENCE_ATTESTATION_MISSING",
            "errors": ["missing evidence attestation report"],
        }
    data = _read_json(report_path)
    artifacts = data.get("artifacts", []) if isinstance(data, dict) else []
    return {
        "attestation_ok": not missing and data.get("pass") is True and data.get("classification") == "PNVA_SOVEREIGN_EVIDENCE_ATTESTED",
        "missing": missing,
        "classification": data.get("classification"),
        "artifact_count": int(data.get("artifact_count", 0)),
        "failure_count": int(data.get("failure_count", 0)),
        "evidence_hash": data.get("evidence_hash"),
        "tracked_artifacts": len(artifacts) if isinstance(artifacts, list) else 0,
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["attestation failed"],
    }


def audit_adversarial_validation(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in ADVERSARIAL_VALIDATION_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-adversarial-validation-2026-05-05.json"
    if not report_path.exists():
        return {
            "adversarial_ok": False,
            "missing": missing,
            "classification": "ADVERSARIAL_VALIDATION_MISSING",
            "errors": ["missing adversarial validation report"],
        }
    data = _read_json(report_path)
    tests = data.get("tests", []) if isinstance(data, dict) else []
    failed = [item for item in tests if isinstance(item, dict) and item.get("detected") is not True]
    expected = [
        "PROOF_HASH_MISMATCH",
        "LOW_AUTHORITY_STRONG_DECISION",
        "EVENT_ENTITY_NOT_IN_CATALOG",
        "RELATION_TARGET_NOT_IN_CATALOG",
        "DUPLICATE_EVENT_IDS",
        "CHAIN_HASH_DRIFT",
        "JSON_PARSE_ERROR",
    ]
    observed = [str(item.get("expected_detection")) for item in tests if isinstance(item, dict)]
    return {
        "adversarial_ok": (
            not missing
            and data.get("pass") is True
            and data.get("classification") == "ADVERSARIAL_VALIDATION_PASS"
            and not failed
            and set(expected).issubset(set(observed))
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "test_count": int(data.get("test_count", 0)),
        "detected_count": int(data.get("detected_count", 0)),
        "failure_count": int(data.get("failure_count", 0)),
        "expected_detections": observed,
        "undetected_tests": [item.get("name") for item in failed],
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["adversarial validation failed"],
    }


def audit_entity_heuristic_maturity(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in ENTITY_HEURISTIC_MATURITY_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-entity-heuristic-maturity-2026-05-05.json"
    if not report_path.exists():
        return {
            "maturity_ok": False,
            "missing": missing,
            "classification": "ENTITY_HEURISTIC_MATURITY_MISSING",
            "errors": ["missing entity heuristic maturity report"],
        }
    data = _read_json(report_path)
    summary = data.get("summary", {}) if isinstance(data, dict) else {}
    allowed = {"ENTITY_HEURISTIC_MATURITY_READY", "ENTITY_HEURISTIC_MATURITY_READY_WITH_LEGACY_WARNINGS"}
    return {
        "maturity_ok": (
            not missing
            and data.get("pass") is True
            and data.get("classification") in allowed
            and int(data.get("error_count", 0)) == 0
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "maturity_score": float(data.get("maturity_score", 0.0)),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
        "total_event_count": int(summary.get("total_event_count", 0)),
        "total_suppressed_count": int(summary.get("total_suppressed_count", 0)),
        "aggregate_no_tick_suppression_ratio": float(summary.get("aggregate_no_tick_suppression_ratio", 0.0)),
        "aggregate_hard_authority_ratio": float(summary.get("aggregate_hard_authority_ratio", 0.0)),
        "canonical_low_authority_legacy_count": int(summary.get("canonical_low_authority_legacy_count", 0)),
        "native_low_authority_legacy_count": int(summary.get("native_low_authority_legacy_count", 0)),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["entity heuristic maturity failed"],
    }


def audit_semantic_consistency(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in SEMANTIC_CONSISTENCY_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-semantic-consistency-2026-05-05.json"
    if not report_path.exists():
        return {
            "consistency_ok": False,
            "missing": missing,
            "classification": "SEMANTIC_CONSISTENCY_MISSING",
            "errors": ["missing semantic consistency report"],
        }
    data = _read_json(report_path)
    return {
        "consistency_ok": (
            not missing
            and data.get("pass") is True
            and data.get("classification") == "SEMANTIC_CONSISTENCY_READY"
            and int(data.get("error_count", 0)) == 0
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "check_count": int(data.get("check_count", 0)),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["semantic consistency failed"],
    }


def audit_schema_contract_validation(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in SCHEMA_CONTRACT_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-schema-contract-validation-2026-05-05.json"
    if not report_path.exists():
        return {
            "contract_validation_ok": False,
            "missing": missing,
            "classification": "SCHEMA_CONTRACT_MISSING",
            "errors": ["missing schema contract validation report"],
        }
    data = _read_json(report_path)
    return {
        "contract_validation_ok": (
            not missing
            and data.get("pass") is True
            and str(data.get("classification", "")).startswith("SCHEMA_CONTRACT_READY")
            and int(data.get("error_count", 0)) == 0
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "event_count": int(data.get("event_count", 0)),
        "entity_count": int(data.get("entity_count", 0)),
        "relation_count": int(data.get("relation_count", 0)),
        "heuristic_rule_count": int(data.get("heuristic_rule_count", 0)),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["schema contract validation failed"],
    }


def audit_causal_chronology(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in CAUSAL_CHRONOLOGY_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-causal-chronology-2026-05-05.json"
    if not report_path.exists():
        return {
            "chronology_ok": False,
            "missing": missing,
            "classification": "CAUSAL_CHRONOLOGY_MISSING",
            "errors": ["missing causal chronology report"],
        }
    data = _read_json(report_path)
    return {
        "chronology_ok": (
            not missing
            and data.get("pass") is True
            and str(data.get("classification", "")).startswith("CAUSAL_CHRONOLOGY_READY")
            and int(data.get("error_count", 0)) == 0
            and data.get("native_chronology_clean") is True
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "event_count": int(data.get("event_count", 0)),
        "chain_count": int(data.get("chain_count", 0)),
        "global_backward_count": int(data.get("global_backward_count", 0)),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
        "native_chronology_clean": bool(data.get("native_chronology_clean")),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["causal chronology failed"],
    }


def audit_tension_decision_calibration(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in TENSION_DECISION_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-tension-decision-calibration-2026-05-05.json"
    if not report_path.exists():
        return {
            "calibration_ok": False,
            "missing": missing,
            "classification": "TENSION_DECISION_MISSING",
            "errors": ["missing tension-decision calibration report"],
        }
    data = _read_json(report_path)
    return {
        "calibration_ok": (
            not missing
            and data.get("pass") is True
            and str(data.get("classification", "")).startswith("TENSION_DECISION_READY")
            and int(data.get("error_count", 0)) == 0
            and data.get("native_calibration_clean") is True
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "event_count": int(data.get("event_count", 0)),
        "error_count": int(data.get("error_count", 0)),
        "warning_count": int(data.get("warning_count", 0)),
        "legacy_calibration_warning_count": int(data.get("legacy_calibration_warning_count", 0)),
        "native_calibration_clean": bool(data.get("native_calibration_clean")),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["tension-decision calibration failed"],
    }


def audit_reproducibility(repo: Path) -> dict[str, Any]:
    missing = [rel for rel in REPRODUCIBILITY_FILES if not (repo / rel).exists()]
    report_path = repo / "reports" / "pnva-reproducibility-2026-05-05.json"
    if not report_path.exists():
        return {
            "reproducibility_ok": False,
            "missing": missing,
            "classification": "REPRODUCIBILITY_MISSING",
            "errors": ["missing reproducibility report"],
        }
    data = _read_json(report_path)
    return {
        "reproducibility_ok": (
            not missing
            and data.get("pass") is True
            and data.get("classification") == "REPRODUCIBILITY_READY"
            and int(data.get("failure_count", 0)) == 0
        ),
        "missing": missing,
        "classification": data.get("classification"),
        "command_count": int(data.get("command_count", 0)),
        "comparison_count": int(data.get("comparison_count", 0)),
        "failure_count": int(data.get("failure_count", 0)),
        "command_failure_count": int(data.get("command_failure_count", 0)),
        "comparison_failure_count": int(data.get("comparison_failure_count", 0)),
        "errors": [] if isinstance(data, dict) and data.get("pass") is True else ["reproducibility failed"],
    }


def sample_jsonl(path: Path, *, max_lines: int = 50000) -> dict[str, Any]:
    events: Counter[str] = Counter()
    decisions: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    states: Counter[str] = Counter()
    keys: Counter[str] = Counter()
    tensions: list[float] = []
    freshness: list[float] = []
    hash4d: list[float] = []
    veon_records = 0
    sealed_records = 0
    bad_json = 0
    lines = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if lines >= max_lines:
                break
            if not line.strip():
                continue
            lines += 1
            try:
                data = json.loads(line)
            except Exception:
                bad_json += 1
                continue
            if not isinstance(data, dict):
                continue
            keys.update(data.keys())
            event_name = str(data.get("event") or data.get("kind") or "")
            decision_name = str(data.get("decision") or data.get("pnva_decision") or data.get("action") or "")
            reason_name = str(data.get("reason") or data.get("runtime_decision_reason") or "")
            state_name = str(data.get("state") or data.get("state_label") or "")
            events[event_name] += 1
            decisions[decision_name] += 1
            reasons[reason_name] += 1
            states[state_name] += 1
            if "seal" in data:
                sealed_records += 1
            if any(str(key).startswith("veon_") for key in data):
                veon_records += 1
            for key, bucket in (
                ("field_tension", tensions),
                ("job_freshness", freshness),
                ("hash4d_score", hash4d),
                ("runtime_hash4d_score", hash4d),
            ):
                if key in data:
                    try:
                        bucket.append(float(data[key]))
                    except Exception:
                        pass

    def stats(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "min": _round(min(values)),
            "median": _round(statistics.median(values)),
            "max": _round(max(values)),
        }

    return {
        "file": path.name,
        "available": True,
        "sampled_lines": lines,
        "bad_json": bad_json,
        "bad_json_ratio": _round(_safe_ratio(bad_json, lines)),
        "top_events": events.most_common(8),
        "top_decisions": decisions.most_common(8),
        "top_reasons": reasons.most_common(8),
        "top_states": states.most_common(8),
        "top_keys": keys.most_common(24),
        "sealed_records": sealed_records,
        "veon_records": veon_records,
        "field_tension": stats(tensions),
        "job_freshness": stats(freshness),
        "hash4d_score": stats(hash4d),
    }


def audit_local_logs(strict_public: bool) -> dict[str, Any]:
    if strict_public:
        return {
            "mode": "strict_public",
            "available": False,
            "note": "Local private logs intentionally skipped."
        }
    samples = []
    for path in LOCAL_LOG_CANDIDATES:
        if path.exists():
            samples.append(sample_jsonl(path))
    total_bad = sum(item.get("bad_json", 0) for item in samples)
    total_lines = sum(item.get("sampled_lines", 0) for item in samples)
    thermal_reason_count = 0
    resize_count = 0
    decision_total = 0
    for item in samples:
        for reason, count in item.get("top_reasons", []):
            if "thermal" in reason:
                thermal_reason_count += int(count)
        for decision, count in item.get("top_decisions", []):
            if decision == "RESIZE_BATCH":
                resize_count += int(count)
            if decision:
                decision_total += int(count)
    flags = []
    if total_bad:
        flags.append("LOCAL_JSON_PARSE_ERRORS")
    if _safe_ratio(resize_count, decision_total) > 0.45:
        flags.append("HIGH_RESIZE_BATCH_RATIO")
    if thermal_reason_count > 0:
        flags.append("THERMAL_PRESSURE_DOMINANT")
    return {
        "mode": "local_private_summary",
        "available": bool(samples),
        "sample_count": len(samples),
        "sampled_lines_total": total_lines,
        "bad_json_total": total_bad,
        "bad_json_ratio": _round(_safe_ratio(total_bad, total_lines)),
        "risk_flags": flags,
        "samples": samples,
    }


def audit_sovereignty(repo: Path) -> dict[str, Any]:
    missing_docs = [rel for rel in PUBLIC_DOCS if not (repo / rel).exists()]
    raw_dir_exists = (repo / "proofs" / "raw").exists()
    path_leaks = []
    personal_home_marker = "/" + "home" + "/" + "enyos"
    personal_desktop_marker = "Desktop/" + "document"
    for path in repo.rglob("*"):
        if path.is_dir() or ".git" in path.parts:
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".tar", ".gz"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if personal_home_marker in text or personal_desktop_marker in text:
            path_leaks.append(str(path.relative_to(repo)))
    return {
        "docs_ok": not missing_docs,
        "missing_docs": missing_docs,
        "raw_proofs_absent": not raw_dir_exists,
        "path_leaks": path_leaks,
        "citation_ok": (repo / "CITATION.cff").exists(),
        "licenses_ok": (repo / "LICENSE").exists() and (repo / "LICENSE-DOCS").exists(),
    }


def score_report(report: dict[str, Any]) -> dict[str, Any]:
    scores = {
        "proof_integrity": 0,
        "ai_search_discovery": 0,
        "log_contract": 0,
        "local_log_health": 0,
        "sovereignty_hygiene": 0,
        "actionability": 0,
    }
    proofs = report["proofs"]
    if proofs["proof_count"] == proofs["required_count"] and not proofs["missing"]:
        scores["proof_integrity"] += 10
    if not proofs["failed"]:
        scores["proof_integrity"] += 10
    if proofs["index_ok"]:
        scores["proof_integrity"] += 4
    if proofs["h24_canonical_pass_ok"]:
        scores["proof_integrity"] += 6

    discovery = report["discovery"]
    if discovery["robots_ok"]:
        scores["ai_search_discovery"] += 7
    if discovery["llms_ok"]:
        scores["ai_search_discovery"] += 5
    if discovery["sitemap_ok"] and discovery["sitemap_url_count"] >= 5:
        scores["ai_search_discovery"] += 3

    contract = report["contract"]
    if contract["schemas_ok"]:
        scores["log_contract"] += 10
    if report["sovereignty"].get("docs_ok"):
        scores["log_contract"] += 5
    if report.get("canonical_bridge", {}).get("bridge_ok"):
        scores["actionability"] += 2
    if report.get("replay_validation", {}).get("replay_ok"):
        scores["actionability"] += 2
    if report.get("no_tick_invariants", {}).get("invariants_ok"):
        scores["actionability"] += 2
    if report.get("native_emitter", {}).get("native_ok"):
        scores["actionability"] += 0
    if report.get("schema_contract_validation", {}).get("contract_validation_ok"):
        scores["actionability"] += 1
    if report.get("causal_chronology", {}).get("chronology_ok"):
        scores["actionability"] += 1
    if report.get("tension_decision_calibration", {}).get("calibration_ok"):
        scores["actionability"] += 0
    if report.get("sovereign_policy", {}).get("policy_ok"):
        scores["actionability"] += 0
    if report.get("proof_chain", {}).get("chain_ok"):
        scores["actionability"] += 0
    if report.get("causal_graph", {}).get("graph_ok"):
        scores["actionability"] += 0
    if report.get("evidence_attestation", {}).get("attestation_ok"):
        scores["actionability"] += 1
    if report.get("reproducibility", {}).get("reproducibility_ok"):
        scores["actionability"] += 1

    local = report["local_logs"]
    if local.get("mode") == "strict_public":
        scores["local_log_health"] += 6
    elif local.get("available"):
        if local.get("bad_json_total") == 0:
            scores["local_log_health"] += 6
        if local.get("sampled_lines_total", 0) >= 1000:
            scores["local_log_health"] += 4
        if any(item.get("veon_records", 0) > 0 for item in local.get("samples", [])):
            scores["local_log_health"] += 3
        if any(item.get("sealed_records", 0) > 0 for item in local.get("samples", [])):
            scores["local_log_health"] += 2

    sovereignty = report["sovereignty"]
    if sovereignty["raw_proofs_absent"]:
        scores["sovereignty_hygiene"] += 5
    if not sovereignty["path_leaks"]:
        scores["sovereignty_hygiene"] += 5
    if sovereignty["citation_ok"]:
        scores["sovereignty_hygiene"] += 2
    if sovereignty["licenses_ok"]:
        scores["sovereignty_hygiene"] += 3

    if (report["repo"] / ".github" / "workflows" / "validate.yml").exists():
        scores["actionability"] += 0
    if (report["repo"] / "tools" / "pnva_sovereign_audit.py").exists():
        scores["actionability"] += 0

    total = sum(scores.values())
    return {
        "sections": scores,
        "total": total,
        "max": 100,
        "classification": "SOVEREIGN_READY" if total >= 90 else "ROBUST" if total >= 80 else "NEEDS_HARDENING",
    }


def build_report(repo: Path, *, strict_public: bool = False) -> dict[str, Any]:
    repo = repo.resolve()
    report: dict[str, Any] = {
        "schema_version": "pnva.sovereign_audit.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "repo_path": str(repo),
        "repo": repo,
        "proofs": audit_proofs(repo),
        "discovery": audit_discovery(repo),
        "contract": audit_contract(repo),
        "canonical_bridge": audit_canonical_bridge(repo),
        "replay_validation": audit_replay_validation(repo),
        "no_tick_invariants": audit_no_tick_invariants(repo),
        "native_emitter": audit_native_emitter(repo),
        "sovereign_policy": audit_sovereign_policy(repo),
        "proof_chain": audit_proof_chain(repo),
        "causal_graph": audit_causal_graph(repo),
        "schema_contract_validation": audit_schema_contract_validation(repo),
        "causal_chronology": audit_causal_chronology(repo),
        "tension_decision_calibration": audit_tension_decision_calibration(repo),
        "evidence_attestation": audit_evidence_attestation(repo),
        "adversarial_validation": audit_adversarial_validation(repo),
        "entity_heuristic_maturity": audit_entity_heuristic_maturity(repo),
        "semantic_consistency": audit_semantic_consistency(repo),
        "reproducibility": audit_reproducibility(repo),
        "local_logs": audit_local_logs(strict_public),
        "sovereignty": audit_sovereignty(repo),
        "recommendations": [
            "Add schema_version, entity_id and causal_chain_id to every new JSONL event.",
            "Normalize legacy event/kind payloads into pnva.event.v1 before publishing.",
            "Prefer native pnva.event.v1 emission for new runtimes; use the bridge only for legacy evidence.",
            "Run no-tick invariant analysis after replay validation to prove causal suppression, not only execution.",
            "Run sovereign policy validation to separate production-grade authority from legacy-tolerated authority.",
            "Seal canonical and native event sequences with proof-chain hashes before public release.",
            "Audit causal graphs so entity topology is visible, not implicit.",
            "Run schema contract validation so event and entity envelopes are checked before attestation.",
            "Run causal chronology guard so time remains an audited trace, not a blind execution driver.",
            "Run tension-decision calibration so threshold/decision drift remains explicit.",
            "Publish one sovereign evidence attestation hash with every evidence release.",
            "Run adversarial validation so validators prove tamper detection, not only green-path acceptance.",
            "Track entity and heuristic maturity so no-tick suppression stays attributable to actors and authority.",
            "Run semantic consistency guard after attestation so cross-report drift blocks publication.",
            "Run reproducibility guard so current tools regenerate the stable public evidence fields.",
            "Keep raw local logs private and publish only sanitized proof summaries.",
            "Track thermal pressure provenance when thermal pressure is high but sensor temperature/power are unavailable.",
            "Treat high RESIZE_BATCH ratio as pressure intelligence, not as a proof failure by itself.",
        ],
    }
    score = score_report(report)
    report["score"] = score
    report.pop("repo", None)
    report["repo_path"] = "<REPO>"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit PNVA-Core proof, discovery, log contract and sovereignty readiness.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]), help="Repository root.")
    parser.add_argument("--write", default="", help="Write JSON report to this path.")
    parser.add_argument("--strict-public", action="store_true", help="Skip private local log sampling.")
    parser.add_argument("--min-score", type=int, default=80, help="Minimum acceptable score.")
    args = parser.parse_args()

    report = build_report(Path(args.repo), strict_public=bool(args.strict_public))
    raw = json.dumps(report, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = Path(args.repo) / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if int(report["score"]["total"]) >= int(args.min_score) else 1


if __name__ == "__main__":
    raise SystemExit(main())
