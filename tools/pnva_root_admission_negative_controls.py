#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable


sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import pnva_root_entity_heuristic_admission_matrix as admission_matrix
from tools import pnva_root_no_tick_causal_contract as no_tick_contract
from tools import pnva_root_runtime_admission_controller as runtime_admission


AUTHOR = "Gustavo de Aguiar Martins"
PROJECT = "PNVA-Core"
ROOT_RELEASE_HASH = "sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc"

R3_EVENTS = "reports/pnva-r3-runtime-events-2026-05-05.jsonl"
NATIVE_EVENTS = "reports/pnva-native-events-demo-2026-05-05.jsonl"


Mutation = Callable[[Path], str]


def _sha_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def _copy_inputs(src: Path, dst: Path) -> None:
    required = set(no_tick_contract.EVENT_STREAMS.values())
    required.update(no_tick_contract.NO_TICK_REPORTS.values())
    required.update(no_tick_contract.ROOT_REPORTS.values())
    required.update(runtime_admission.REPORTS.values())
    required.update(admission_matrix.REPORTS.values())
    for rel in sorted(required):
        source = src / rel
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _r3_events(repo: Path) -> list[dict[str, Any]]:
    return _read_jsonl(repo / R3_EVENTS)


def _native_events(repo: Path) -> list[dict[str, Any]]:
    return _read_jsonl(repo / NATIVE_EVENTS)


def _write_r3_events(repo: Path, events: list[dict[str, Any]]) -> None:
    _write_jsonl(repo / R3_EVENTS, events)


def _write_native_events(repo: Path, events: list[dict[str, Any]]) -> None:
    _write_jsonl(repo / NATIVE_EVENTS, events)


def _first_precheck(events: list[dict[str, Any]]) -> int:
    for index, event in enumerate(events):
        if str(event.get("event_id", "")).endswith("_precheck"):
            return index
    return 0


def _first_commit(events: list[dict[str, Any]]) -> int:
    for index, event in enumerate(events):
        if str(event.get("event_id", "")).endswith("_commit"):
            return index
    return min(1, len(events) - 1)


def mutate_r3_gate_delta_inversion(repo: Path) -> str:
    events = _r3_events(repo)
    index = _first_precheck(events)
    events[index].setdefault("tension", {})["gate_delta"] = 0.25
    _write_r3_events(repo, events)
    return "Made an R3 precheck cross a positive execution gate."


def mutate_r3_unpaired_chain(repo: Path) -> str:
    events = _r3_events(repo)
    index = _first_commit(events)
    removed = events.pop(index)
    _write_r3_events(repo, events)
    return f"Removed one R3 commit event: {removed.get('event_id')}."


def mutate_r3_unknown_entity(repo: Path) -> str:
    events = _r3_events(repo)
    events[_first_precheck(events)]["entity_id"] = "entity_not_admitted_to_root"
    _write_r3_events(repo, events)
    return "Moved an R3 event onto an unknown entity."


def mutate_r3_projected_proof(repo: Path) -> str:
    events = _r3_events(repo)
    events[_first_precheck(events)].setdefault("proof", {})["projection"] = True
    _write_r3_events(repo, events)
    return "Marked an R3 proof as projected evidence."


def mutate_r3_unknown_rule(repo: Path) -> str:
    events = _r3_events(repo)
    events[_first_commit(events)].setdefault("heuristics", {}).setdefault("rules", []).append("unknown_runtime_rule")
    _write_r3_events(repo, events)
    return "Injected an unknown heuristic rule into an R3 commit."


def mutate_r3_duplicate_event_id(repo: Path) -> str:
    events = _r3_events(repo)
    events[_first_commit(events)]["event_id"] = events[_first_precheck(events)].get("event_id")
    _write_r3_events(repo, events)
    return "Duplicated an R3 event_id across precheck and commit."


def mutate_r3_invalid_proof_hash(repo: Path) -> str:
    events = _r3_events(repo)
    event = events[_first_commit(events)]
    event.setdefault("proof", {})["valid"] = False
    event.setdefault("proof", {})["proof_hash"] = "invalid-proof-hash"
    _write_r3_events(repo, events)
    return "Invalidated a proof hash on an R3 commit."


def mutate_native_source_path_leak(repo: Path) -> str:
    events = _native_events(repo)
    events[0].setdefault("source", {})["file_name"] = "/private/pnva/native-runtime-demo"
    _write_native_events(repo, events)
    return "Injected an unsafe local path into a native source reference."


MUTATIONS: list[tuple[str, Mutation]] = [
    ("r3_gate_delta_inversion", mutate_r3_gate_delta_inversion),
    ("r3_unpaired_chain", mutate_r3_unpaired_chain),
    ("r3_unknown_entity", mutate_r3_unknown_entity),
    ("r3_projected_proof", mutate_r3_projected_proof),
    ("r3_unknown_rule", mutate_r3_unknown_rule),
    ("r3_duplicate_event_id", mutate_r3_duplicate_event_id),
    ("r3_invalid_proof_hash", mutate_r3_invalid_proof_hash),
    ("native_source_path_leak", mutate_native_source_path_leak),
]


def _build_chain(temp_repo: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract_report = no_tick_contract.build_report(temp_repo)
    _write_json(temp_repo / "reports/pnva-root-no-tick-causal-contract-2026-05-05.json", contract_report)
    admission_report = runtime_admission.build_report(temp_repo)
    _write_json(temp_repo / "reports/pnva-root-runtime-admission-controller-2026-05-05.json", admission_report)
    matrix_report = admission_matrix.build_report(temp_repo)
    _write_json(temp_repo / "reports/pnva-root-entity-heuristic-admission-matrix-2026-05-05.json", matrix_report)
    return contract_report, admission_report, matrix_report


def _case(repo: Path, control_id: str, mutate: Mutation | None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pnva-root-admission-negative-") as raw_tmp:
        temp_repo = Path(raw_tmp)
        _copy_inputs(repo, temp_repo)
        mutation = "No mutation; clean control."
        if mutate is not None:
            mutation = mutate(temp_repo)
        contract_report, admission_report, matrix_report = _build_chain(temp_repo)

    expected_clean = mutate is None
    if expected_clean:
        detected = contract_report.get("pass") is True and admission_report.get("pass") is True and matrix_report.get("pass") is True
    else:
        detected = contract_report.get("pass") is False and admission_report.get("pass") is False and matrix_report.get("pass") is False
    return {
        "id": control_id,
        "mutation": mutation,
        "expected_clean": expected_clean,
        "detected": detected,
        "contract_classification": contract_report.get("classification"),
        "contract_pass": contract_report.get("pass"),
        "contract_failure_count": contract_report.get("failure_count"),
        "contract_failure_names": [item.get("name") for item in contract_report.get("checks", []) if item.get("pass") is not True],
        "admission_classification": admission_report.get("classification"),
        "admission_pass": admission_report.get("pass"),
        "admission_failure_count": admission_report.get("failure_count"),
        "admission_failure_names": [item.get("name") for item in admission_report.get("checks", []) if item.get("pass") is not True],
        "matrix_classification": matrix_report.get("classification"),
        "matrix_pass": matrix_report.get("pass"),
        "matrix_failure_count": matrix_report.get("failure_count"),
        "matrix_failure_names": [item.get("name") for item in matrix_report.get("checks", []) if item.get("pass") is not True],
    }


def build_report(repo: Path) -> dict[str, Any]:
    clean_control = _case(repo, "clean_control", None)
    controls = [_case(repo, control_id, copy.deepcopy(mutate)) for control_id, mutate in MUTATIONS]
    detected_count = sum(1 for item in controls if item["detected"])
    undetected = [item for item in controls if not item["detected"]]
    clean_pass = clean_control["detected"]
    classification = "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS" if clean_pass and not undetected else "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_FAIL"
    seed = {
        "classification": classification,
        "clean_control_pass": clean_pass,
        "controls": [{"id": item["id"], "detected": item["detected"]} for item in controls],
    }
    return {
        "schema_version": "pnva.root_admission_negative_controls.v1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "author": AUTHOR,
        "project": PROJECT,
        "classification": classification,
        "pass": classification == "PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS",
        "clean_control_pass": clean_pass,
        "control_count": len(controls),
        "detected_count": detected_count,
        "undetected_count": len(undetected),
        "failure_count": len(undetected) + (0 if clean_pass else 1),
        "root_release_hash": ROOT_RELEASE_HASH,
        "admission_negative_controls_hash": _sha_text(json.dumps(seed, sort_keys=True, separators=(",", ":"), ensure_ascii=True)),
        "mutation_targets": [
            "r3.tension.gate_delta",
            "r3.precheck_commit_pair",
            "r3.entity_id",
            "r3.proof.projection",
            "r3.heuristics.rules",
            "r3.event_id",
            "r3.proof.hash",
            "native.source.file_name",
        ],
        "clean_control": clean_control,
        "controls": controls,
        "interpretation": {
            "purpose": "Prove that the no-tick contract, runtime admission controller and entity-heuristic admission matrix reject corrupted evidence.",
            "sovereignty": "Admission is stronger when bad events are denied before runtime growth can become invisible.",
            "boundary": "All mutations happen in temporary copies. This tool does not modify live evidence, runtime services, gates or mining workloads.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PNVA root admission negative controls.")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]), help="Repository root.")
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
