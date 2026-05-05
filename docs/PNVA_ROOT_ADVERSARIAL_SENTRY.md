# PNVA Root Adversarial Sentry

Author: Gustavo de Aguiar Martins
Project: PNVA-Core / Enygnalab / EnyOS
Edition: Open Research / Production Evidence Edition, 2026

## Objective

The root adversarial sentry proves that the root validators reject corrupted runtime evidence.

It creates temporary copies of the public evidence inputs, mutates the R3 runtime JSONL, regenerates the root sovereignty guard and root causal intelligence report, and expects the mutated package to fail.

```text
clean runtime evidence -> root PASS
mutated runtime evidence -> root FAIL
```

## Current Public Result

Report:

```text
reports/pnva-root-adversarial-sentry-2026-05-05.json
```

Expected classification:

```text
PNVA_ROOT_ADVERSARIAL_SENTRY_PASS
```

Expected result:

```text
clean_control_pass: true
test_count: 8
detected_count: 8
failure_count: 0
```

## Controlled Mutations

The sentry currently mutates:

```text
proof.projection=true
missing entity_id in the catalog
broken precheck-to-commit state continuity
weak runtime authority
unsafe source.file_name local path
duplicate event_id
positive gate_delta on no-tick precheck
legacy_observer heuristic injection
```

Each mutation must make:

```text
PNVA_ROOT_SOVEREIGNTY_GUARD_FAIL
PNVA_ROOT_CAUSAL_INTELLIGENCE_NEEDS_HARDENING
```

## Boundary

This sentry is adversarial validation over the public deterministic R3 runtime sample.

It does not claim universal security for private deployments. It proves that the current public root validators reject the most important root-level evidence corruptions.

## Command

```bash
python3 tools/pnva_root_adversarial_sentry.py \
  --write reports/pnva-root-adversarial-sentry-2026-05-05.json
```

## Sovereign Rule

A root PASS is not enough. PNVA must also prove that corrupted root evidence does not pass silently.
