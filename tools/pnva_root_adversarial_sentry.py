#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import pnva_root_causal_intelligence as causal_intelligence
from tools import pnva_root_sovereignty_guard as root_sovereignty


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
RUNTIME_EVENTS = "reports/pnva-r3-runtime-events-2026-05-05.jsonl"
ROOT_GUARD_REPORT = "reports/pnva-root-sovereignty-guard-2026-05-05.json"


Mutation = Callable[[list[dict[str, Any]]], str]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                events.append(json.loads(line))
    return events


def _write_jsonl(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _copy_inputs(src: Path, dst: Path) -> None:
    required = set(root_sovereignty.REPORTS.values()) | set(causal_intelligence.REPORTS.values())
    for rel in sorted(required):
        source = src / rel
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _runtime_events_path(repo: Path) -> Path:
    return repo / RUNTIME_EVENTS


def _commit_index(events: list[dict[str, Any]]) -> int:
    for index, event in enumerate(events):
        if str(event.get("event_id", "")).endswith("_commit"):
            return index
    return 1


def mutate_projection_true(events: list[dict[str, Any]]) -> str:
    events[0].setdefault("proof", {})["projection"] = True
    return "Set proof.projection=true on a native runtime precheck."


def mutate_missing_entity(events: list[dict[str, Any]]) -> str:
    events[0]["entity_id"] = "entity_missing_from_catalog"
    return "Moved a runtime event onto an entity_id absent from the entity catalog."


def mutate_state_continuity(events: list[dict[str, Any]]) -> str:
    index = _commit_index(events)
    events[index].setdefault("field", {})["state_before"] = "observed"
    return "Broke precheck-to-commit state continuity inside one no-tick pair."


def mutate_weak_authority(events: list[dict[str, Any]]) -> str:
    index = _commit_index(events)
    events[index].setdefault("tension", {}).setdefault("components", {})["authority_delta"] = 1.0
    return "Downgraded a runtime collapse commit below H2 authority."


def mutate_unsafe_source(events: list[dict[str, Any]]) -> str:
    events[0].setdefault("source", {})["file_name"] = "/private/runtime.py"
    return "Injected an unsafe local path into source.file_name."


def mutate_duplicate_event_id(events: list[dict[str, Any]]) -> str:
    events[1]["event_id"] = events[0]["event_id"]
    return "Duplicated a runtime event_id."


def mutate_gate_delta_inversion(events: list[dict[str, Any]]) -> str:
    events[0].setdefault("tension", {})["gate_delta"] = 0.25
    return "Made a no-tick precheck cross the positive execution gate."


def mutate_legacy_rule(events: list[dict[str, Any]]) -> str:
    index = _commit_index(events)
    events[index].setdefault("heuristics", {}).setdefault("rules", []).append("legacy_observer")
    return "Injected legacy_observer into a runtime commit heuristic set."


MUTATIONS: list[tuple[str, Mutation]] = [
    ("projection_true", mutate_projection_true),
    ("missing_entity", mutate_missing_entity),
    ("state_continuity_break", mutate_state_continuity),
    ("weak_authority", mutate_weak_authority),
    ("unsafe_source_path", mutate_unsafe_source),
    ("duplicate_event_id", mutate_duplicate_event_id),
    ("gate_delta_inversion", mutate_gate_delta_inversion),
    ("legacy_rule_injection", mutate_legacy_rule),
]


def _build_reports(temp_repo: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    root_report = root_sovereignty.build_report(temp_repo)
    _write_json(temp_repo / ROOT_GUARD_REPORT, root_report)
    causal_report = causal_intelligence.build_report(temp_repo)
    return root_report, causal_report


def _case(repo: Path, mutation_id: str, mutate: Mutation | None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pnva-root-adversarial-") as raw_tmp:
        temp_repo = Path(raw_tmp)
        _copy_inputs(repo, temp_repo)
        events = _read_jsonl(_runtime_events_path(temp_repo))
        mutation_description = "No mutation; clean control."
        if mutate:
            events = copy.deepcopy(events)
            mutation_description = mutate(events)
            _write_jsonl(_runtime_events_path(temp_repo), events)
        root_report, causal_report = _build_reports(temp_repo)

    root_failures = root_report.get("failures", [])
    causal_failures = causal_report.get("failures", [])
    expected_clean = mutate is None
    if expected_clean:
        detected = root_report.get("pass") is True and causal_report.get("pass") is True
    else:
        detected = root_report.get("pass") is False and causal_report.get("pass") is False
    return {
        "id": mutation_id,
        "mutation": mutation_description,
        "expected_clean": expected_clean,
        "detected": detected,
        "root_classification": root_report.get("classification"),
        "root_pass": root_report.get("pass"),
        "root_failure_count": root_report.get("failure_count"),
        "root_failure_names": [item.get("name") for item in root_failures[:8]],
        "causal_classification": causal_report.get("classification"),
        "causal_pass": causal_report.get("pass"),
        "causal_failure_count": causal_report.get("failure_count"),
        "causal_failures": causal_failures[:8],
    }


def build_report(repo: Path) -> dict[str, Any]:
    clean_control = _case(repo, "clean_control", None)
    controls = [_case(repo, mutation_id, mutate) for mutation_id, mutate in MUTATIONS]
    detected_count = sum(1 for item in controls if item["detected"])
    failure_count = sum(1 for item in controls if not item["detected"])
    clean_pass = clean_control["detected"]
    classification = "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS" if clean_pass and failure_count == 0 else "PNVA_ROOT_ADVERSARIAL_SENTRY_FAIL"
    return {
        "schema_version": "pnva.root_adversarial_sentry.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": classification == "PNVA_ROOT_ADVERSARIAL_SENTRY_PASS",
        "clean_control_pass": clean_pass,
        "test_count": len(controls),
        "detected_count": detected_count,
        "failure_count": failure_count,
        "controls": controls,
        "clean_control": clean_control,
        "mutation_targets": [
            "proof.projection",
            "entity_id",
            "field.state_before",
            "tension.components.authority_delta",
            "source.file_name",
            "event_id",
            "tension.gate_delta",
            "heuristics.rules",
        ],
        "interpretation": {
            "purpose": "Prove that PNVA root validators reject controlled runtime evidence corruption.",
            "sovereignty": "A root PASS is stronger when projection, missing entity identity, broken no-tick continuity, weak authority, unsafe source paths, duplicate identity, gate inversion and legacy heuristic injection all fail.",
            "boundary": "This is adversarial validation over the public deterministic R3 runtime sample; it is not a universal security proof for private deployments.",
        },
        "recommendations": [
            "Run this sentry before public root-readiness claims.",
            "Treat any undetected mutation as a release-blocking validator gap.",
            "Keep mutations temporary so public evidence files remain intact.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run root adversarial negative controls for PNVA runtime evidence.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--write", default="")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    report = build_report(repo)
    raw = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    if args.write:
        out = Path(args.write)
        if not out.is_absolute():
            out = repo / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
    print(raw, end="")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
