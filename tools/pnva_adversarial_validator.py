#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from copy import deepcopy
from pathlib import Path
from typing import Any


CANONICAL_EVENTS = "reports/pnva-canonical-events-sample-2026-05-05.jsonl"
CANONICAL_ENTITIES = "reports/pnva-entity-catalog-2026-05-05.json"
NATIVE_EVENTS = "reports/pnva-native-events-demo-2026-05-05.jsonl"
NATIVE_ENTITIES = "reports/pnva-native-entity-catalog-demo-2026-05-05.json"
CANONICAL_CHAIN_REPORT = "reports/pnva-proof-chain-2026-05-05.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            data = json.loads(line)
            if isinstance(data, dict):
                events.append(data)
    return events


def _write_jsonl(path: Path, events: list[dict[str, Any]], *, invalid_tail: bool = False) -> None:
    raw = "\n".join(json.dumps(event, ensure_ascii=True, sort_keys=True) for event in events) + "\n"
    if invalid_tail:
        raw += "{invalid pnva json\n"
    path.write_text(raw, encoding="utf-8")


def _collect_codes(value: Any) -> list[str]:
    codes: list[str] = []
    if isinstance(value, dict):
        code = value.get("code")
        if code:
            codes.append(str(code))
        for item in value.values():
            codes.extend(_collect_codes(item))
    elif isinstance(value, list):
        for item in value:
            codes.extend(_collect_codes(item))
    return codes


def _redact_temp_paths(value: str) -> str:
    return re.sub(r"/tmp/pnva-adversarial-[^/]+", "<TEMP>", value)


def _run_json_tool(repo: Path, args: list[str]) -> dict[str, Any]:
    command = [sys.executable, *args]
    completed = subprocess.run(
        command,
        cwd=repo,
        check=False,
        text=True,
        capture_output=True,
    )
    parsed: dict[str, Any] = {}
    parse_error = ""
    if completed.stdout.strip():
        try:
            data = json.loads(completed.stdout)
            if isinstance(data, dict):
                parsed = data
        except Exception as exc:
            parse_error = str(exc)
    return {
        "command": " ".join(args),
        "exit_code": completed.returncode,
        "stdout_json": parsed,
        "stdout_parse_error": parse_error,
        "stderr_tail": completed.stderr[-1200:],
    }


def _tool_result(
    *,
    name: str,
    mutation: str,
    target_tool: str,
    expected_detection: str,
    run: dict[str, Any],
    require_nonzero: bool = True,
    hash_changed: bool | None = None,
    baseline_hash: str = "",
    observed_hash: str = "",
) -> dict[str, Any]:
    report = run.get("stdout_json", {}) if isinstance(run.get("stdout_json"), dict) else {}
    error_codes = _collect_codes(report.get("errors", []))
    warning_codes = _collect_codes(report.get("warnings", []))
    detected = expected_detection in error_codes or expected_detection in warning_codes
    if expected_detection == "CHAIN_HASH_DRIFT":
        detected = bool(hash_changed)
    if require_nonzero and int(run.get("exit_code", 0)) == 0:
        detected = False
    result: dict[str, Any] = {
        "name": name,
        "mutation": mutation,
        "target_tool": target_tool,
        "expected_detection": expected_detection,
        "detected": bool(detected),
        "command": _redact_temp_paths(str(run.get("command") or "")),
        "command_exit_code": int(run.get("exit_code", 0)),
        "observed_pass": report.get("pass"),
        "observed_classification": report.get("classification"),
        "observed_error_codes": sorted(set(error_codes)),
        "observed_warning_codes": sorted(set(warning_codes)),
    }
    if run.get("stdout_parse_error"):
        result["stdout_parse_error"] = run["stdout_parse_error"]
    if run.get("stderr_tail"):
        result["stderr_tail"] = _redact_temp_paths(str(run["stderr_tail"]))
    if hash_changed is not None:
        result["hash_changed"] = bool(hash_changed)
        result["baseline_hash"] = baseline_hash
        result["observed_hash"] = observed_hash
    return result


def _first_strong_decision(events: list[dict[str, Any]]) -> int:
    for index, event in enumerate(events):
        decision = event.get("decision", {}) if isinstance(event.get("decision"), dict) else {}
        if str(decision.get("kind") or "") in {"collapse", "block", "prove", "reclassify"}:
            return index
    raise ValueError("native event sample does not contain a strong decision")


def _first_relation(events: list[dict[str, Any]]) -> int:
    for index, event in enumerate(events):
        relations = event.get("relations", {}) if isinstance(event.get("relations"), dict) else {}
        if relations.get("target_entity_id"):
            return index
    raise ValueError("event sample does not contain relation target")


def build_report(repo: Path) -> dict[str, Any]:
    repo = repo.resolve()
    canonical_events = _load_jsonl(repo / CANONICAL_EVENTS)
    native_events = _load_jsonl(repo / NATIVE_EVENTS)
    baseline_chain = _load_json(repo / CANONICAL_CHAIN_REPORT)
    baseline_hash = str((baseline_chain.get("seal", {}) if isinstance(baseline_chain, dict) else {}).get("final_chain_hash") or "")
    tests: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="pnva-adversarial-") as tmp_raw:
        tmp = Path(tmp_raw)

        proof_tamper = deepcopy(canonical_events)
        proof_tamper[0].setdefault("proof", {})["proof_hash"] = "sha256:" + ("0" * 64)
        proof_tamper_path = tmp / "proof-hash-tamper.jsonl"
        _write_jsonl(proof_tamper_path, proof_tamper)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_replay_validator.py",
                "--events",
                str(proof_tamper_path),
                "--entity-catalog",
                CANONICAL_ENTITIES,
            ],
        )
        tests.append(
            _tool_result(
                name="replay_proof_hash_tamper",
                mutation="Changed the first canonical event proof_hash to an impossible sha256 value.",
                target_tool="tools/pnva_replay_validator.py",
                expected_detection="PROOF_HASH_MISMATCH",
                run=run,
            )
        )

        low_authority = deepcopy(native_events)
        strong_index = _first_strong_decision(low_authority)
        low_authority[strong_index].setdefault("heuristics", {})["rules"] = ["legacy_observer"]
        low_authority_path = tmp / "native-low-authority.jsonl"
        _write_jsonl(low_authority_path, low_authority)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_sovereign_policy_validator.py",
                "--events",
                str(low_authority_path),
                "--entity-catalog",
                NATIVE_ENTITIES,
            ],
        )
        tests.append(
            _tool_result(
                name="native_low_authority_strong_decision",
                mutation="Downgraded a native collapse/block/prove event to legacy_observer authority.",
                target_tool="tools/pnva_sovereign_policy_validator.py",
                expected_detection="LOW_AUTHORITY_STRONG_DECISION",
                run=run,
            )
        )

        missing_entity = deepcopy(native_events)
        missing_entity[0]["entity_id"] = "ghost-entity-not-in-catalog"
        missing_entity_path = tmp / "graph-missing-entity.jsonl"
        _write_jsonl(missing_entity_path, missing_entity)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_causal_graph_auditor.py",
                "--events",
                str(missing_entity_path),
                "--entity-catalog",
                NATIVE_ENTITIES,
            ],
        )
        tests.append(
            _tool_result(
                name="graph_missing_entity",
                mutation="Moved one native event onto an entity_id absent from the catalog.",
                target_tool="tools/pnva_causal_graph_auditor.py",
                expected_detection="EVENT_ENTITY_NOT_IN_CATALOG",
                run=run,
            )
        )

        bad_relation = deepcopy(native_events)
        relation_index = _first_relation(bad_relation)
        bad_relation[relation_index].setdefault("relations", {})["target_entity_id"] = "ghost-relation-target"
        bad_relation_path = tmp / "graph-bad-relation.jsonl"
        _write_jsonl(bad_relation_path, bad_relation)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_causal_graph_auditor.py",
                "--events",
                str(bad_relation_path),
                "--entity-catalog",
                NATIVE_ENTITIES,
            ],
        )
        tests.append(
            _tool_result(
                name="graph_bad_relation_target",
                mutation="Changed a relation target to an entity absent from the catalog.",
                target_tool="tools/pnva_causal_graph_auditor.py",
                expected_detection="RELATION_TARGET_NOT_IN_CATALOG",
                run=run,
            )
        )

        duplicate = deepcopy(native_events)
        duplicate.append(deepcopy(native_events[0]))
        duplicate_path = tmp / "proof-chain-duplicate-event-id.jsonl"
        _write_jsonl(duplicate_path, duplicate)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_proof_chain_sealer.py",
                "--events",
                str(duplicate_path),
            ],
        )
        tests.append(
            _tool_result(
                name="proof_chain_duplicate_event_id",
                mutation="Appended a duplicate native event_id to the sequence.",
                target_tool="tools/pnva_proof_chain_sealer.py",
                expected_detection="DUPLICATE_EVENT_IDS",
                run=run,
            )
        )

        order_tamper = deepcopy(canonical_events)
        order_tamper[0], order_tamper[1] = order_tamper[1], order_tamper[0]
        order_tamper_path = tmp / "proof-chain-order-tamper.jsonl"
        _write_jsonl(order_tamper_path, order_tamper)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_proof_chain_sealer.py",
                "--events",
                str(order_tamper_path),
            ],
        )
        observed_report = run.get("stdout_json", {}) if isinstance(run.get("stdout_json"), dict) else {}
        observed_hash = str((observed_report.get("seal", {}) if isinstance(observed_report, dict) else {}).get("final_chain_hash") or "")
        hash_changed = bool(baseline_hash and observed_hash and baseline_hash != observed_hash)
        tests.append(
            _tool_result(
                name="proof_chain_order_tamper",
                mutation="Swapped the first two canonical events without changing their contents.",
                target_tool="tools/pnva_proof_chain_sealer.py",
                expected_detection="CHAIN_HASH_DRIFT",
                run=run,
                require_nonzero=False,
                hash_changed=hash_changed,
                baseline_hash=baseline_hash,
                observed_hash=observed_hash,
            )
        )

        parse_error = deepcopy(canonical_events[:8])
        parse_error_path = tmp / "json-parse-error.jsonl"
        _write_jsonl(parse_error_path, parse_error, invalid_tail=True)
        run = _run_json_tool(
            repo,
            [
                "tools/pnva_replay_validator.py",
                "--events",
                str(parse_error_path),
                "--entity-catalog",
                CANONICAL_ENTITIES,
            ],
        )
        tests.append(
            _tool_result(
                name="json_parse_error",
                mutation="Appended one malformed JSON line to an otherwise valid event sequence.",
                target_tool="tools/pnva_replay_validator.py",
                expected_detection="JSON_PARSE_ERROR",
                run=run,
            )
        )

    detected_count = sum(1 for item in tests if item["detected"])
    failed = [item for item in tests if not item["detected"]]
    classification = "ADVERSARIAL_VALIDATION_PASS" if not failed else "ADVERSARIAL_VALIDATION_FAIL"
    return {
        "schema_version": "pnva.adversarial_validation.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": "Gustavo de Aguiar Martins",
        "project": "PNVA-Core",
        "classification": classification,
        "pass": not failed,
        "test_count": len(tests),
        "detected_count": detected_count,
        "failure_count": len(failed),
        "tests": tests,
        "interpretation": {
            "purpose": "Negative controls prove that PNVA validators reject or expose controlled evidence mutations.",
            "boundary": "This is adversarial validation over the public evidence package; it is not a universal security proof for every deployment.",
            "sovereignty": "A sovereign validator must fail on bad proof hashes, weak authority, unknown entities, invalid graph relations, duplicate event IDs and malformed logs.",
        },
        "recommendations": [
            "Run adversarial validation before every public evidence release.",
            "Treat a missing adversarial detection as a validator bug or a documented blind spot.",
            "Keep mutated test files temporary so public evidence stays clean and auditable.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PNVA adversarial negative controls against public validators.")
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
