# PNVA Entity No-Tick Matrix

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer turns PNVA no-tick evidence into an entity-by-heuristic matrix.

It answers a direct operational question:

```text
which entity executed, which entity suppressed execution, which heuristic decided, and which proof backs it?
```

## Current Public Result

Report:

```text
reports/pnva-entity-no-tick-matrix-2026-05-05.json
```

Current classification:

```text
ENTITY_NO_TICK_MATRIX_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
entity_row_count: 12
observed_entity_row_count: 12
entity_suppression_row_count: 9
suppressed_count: 250
aggregate_no_tick_suppression_ratio: 0.481696
aggregate_entity_suppression_coverage_ratio: 0.75
error_count: 0
warning_count: 35
native_matrix_clean: true
legacy_low_authority_warning_count: 35
```

## Scope Reading

Canonical legacy bridge:

```text
event_count: 512
matrix_entity_count: 6
suppressed_count: 246
entity_suppression_coverage_ratio: 0.833333
error_count: 0
warning_count: 35
```

Native emitter:

```text
event_count: 7
matrix_entity_count: 6
suppressed_count: 4
entity_suppression_coverage_ratio: 0.666667
error_count: 0
warning_count: 0
native_matrix_clean: true
```

## What It Validates

The matrix checks:

```text
entity catalog coverage
proof coverage per entity
decision mix per entity
suppression ratio per entity
collapse/block/observe/prove counts
heuristic rule attribution
authority level per entity
risk flags per entity
tension and gate_delta averages
legacy low-authority strong decisions
native matrix cleanliness
```

## Why This Matters

No-tick is not only a global metric. It must be attributable.

The matrix makes suppression visible as a first-class decision:

```text
entity -> heuristic rules -> authority -> decision -> suppression/execution -> proof
```

This gives PNVA a clearer engineering surface for future hardening. Instead of saying that the system suppressed unnecessary execution, the report shows which entities suppressed, which entities executed, and which rules produced the outcome.

## Warning Policy

The canonical bridge preserves 35 legacy low-authority strong decisions as warnings.

Meaning:

```text
old converted logs remain honest migration evidence
new native runtime evidence must remain clean
```

The native matrix currently has zero warnings and zero errors.

## Command

```bash
python3 tools/pnva_entity_no_tick_matrix.py \
  --write reports/pnva-entity-no-tick-matrix-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_entity_no_tick_matrix.py \
  --write /tmp/pnva-entity-no-tick-matrix.json
python3 -m json.tool /tmp/pnva-entity-no-tick-matrix.json >/dev/null
```

## Production Rule

Native PNVA events should keep:

```text
entity catalog present
proof coverage complete
heuristic rules visible
strong decisions backed by H2/H3/H4 authority
suppression represented as auditable no-tick proof
```

This turns no-tick from a runtime behavior into an entity-governed evidence model.
