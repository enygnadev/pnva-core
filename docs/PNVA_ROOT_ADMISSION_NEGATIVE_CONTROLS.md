# PNVA Root Admission Negative Controls

Author: Gustavo de Aguiar Martins
Project: PNVA-Core
Edition: Open Research / Production Evidence Edition

## Purpose

The PNVA root admission negative controls prove that the no-tick causal contract, runtime admission controller and entity-heuristic admission matrix reject corrupted evidence.

The tool mutates temporary copies only. It never changes live evidence, gates, services or runtime workloads.

## Tool

```text
tools/pnva_root_admission_negative_controls.py
```

## Report

```text
reports/pnva-root-admission-negative-controls-2026-05-05.json
```

## Classification

```text
PNVA_ROOT_ADMISSION_NEGATIVE_CONTROLS_PASS
```

## Current Result

```text
clean_control_pass: true
control_count: 8
detected_count: 8
undetected_count: 0
failure_count: 0
root_release_hash: sha256:97f5c3f379db838784f864c312778a3afabea50ebb30acfffe4f6da2c97b65fc
```

## Mutations Detected

```text
r3_gate_delta_inversion
r3_unpaired_chain
r3_unknown_entity
r3_projected_proof
r3_unknown_rule
r3_duplicate_event_id
r3_invalid_proof_hash
native_source_path_leak
```

## Detection Chain

Each mutation must be rejected by:

```text
root no-tick causal contract
root runtime admission controller
root entity-heuristic admission matrix
```

The clean control must remain PASS. Every corrupted control must become blocked.

## Production Interpretation

This makes the admission layer more rigorous. A PASS is not only a positive report; it is tested against bad evidence:

```text
bad event -> contract fail -> admission blocked -> matrix fail
```

That pattern keeps runtime growth visible and prevents silent acceptance of invalid no-tick, entity or heuristic evidence.

## Boundary

All mutations happen in temporary copies. This report does not modify live evidence, execute runtime actions, change gates, alter mining workloads or publish private tuning.

## Command

```bash
python3 tools/pnva_root_admission_negative_controls.py \
  --write reports/pnva-root-admission-negative-controls-2026-05-05.json
```
