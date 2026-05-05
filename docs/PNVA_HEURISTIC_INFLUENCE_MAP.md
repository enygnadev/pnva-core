# PNVA Heuristic Influence Map

Author: Gustavo de Aguiar Martins  
Project: PNVA-Core / Enygnalab / EnyOS  
Edition: Open Research / Production Evidence Edition, 2026

## Objective

This layer maps how PNVA heuristic rules influence decisions and entities.

It answers:

```text
which rules are influencing collapse, block, observe and prove decisions, under which authority level and with which proof coverage?
```

## Current Public Result

Report:

```text
reports/pnva-heuristic-influence-map-2026-05-05.json
```

Current classification:

```text
HEURISTIC_INFLUENCE_MAP_READY_WITH_LEGACY_WARNINGS
```

Current result:

```text
event_count: 519
heuristic_rule_count: 9
heuristic_coverage_ratio: 1.0
proof_event_coverage_ratio: 1.0
influence_edge_count: 1136
hard_authority_edge_count: 776
low_authority_edge_count: 360
low_authority_strong_edge_count: 164
uncompensated_low_authority_strong_event_count: 35
hard_authority_edge_ratio: 0.683099
error_count: 0
warning_count: 70
native_influence_clean: true
```

## Scope Reading

Canonical legacy bridge:

```text
event_count: 512
heuristic_rule_count: 8
influence_edge_count: 1120
hard_authority_edge_count: 762
low_authority_edge_count: 358
low_authority_strong_edge_count: 163
uncompensated_low_authority_strong_event_count: 35
error_count: 0
warning_count: 70
```

Native emitter:

```text
event_count: 7
heuristic_rule_count: 7
influence_edge_count: 16
hard_authority_edge_count: 14
low_authority_edge_count: 2
low_authority_strong_edge_count: 1
uncompensated_low_authority_strong_event_count: 0
error_count: 0
warning_count: 0
native_influence_clean: true
```

## What It Validates

For every event, the map checks:

```text
entity exists in catalog
heuristic rules are present
proof is valid
rule authority is known
strong decisions have hard-authority coverage
native strong decisions are not controlled only by low-authority rules
```

## Why This Matters

The decision trace index answers whether every event is traceable.

The heuristic influence map answers which rules are carrying the system:

```text
rule -> authority -> decision mix -> entity reach -> suppression/execution -> proof
```

This turns heuristic intelligence into an auditable control surface instead of an opaque label.

## Warning Policy

The canonical bridge preserves `70` warnings related to historical low-authority strong influence.

The native path has:

```text
0 errors
0 warnings
native_influence_clean: true
```

Low-authority rules may appear as supporting context, but native strong decisions must be covered by H2/H3/H4 authority.

## Command

```bash
python3 tools/pnva_heuristic_influence_map.py \
  --write reports/pnva-heuristic-influence-map-2026-05-05.json
```

For CI or temporary validation:

```bash
python3 tools/pnva_heuristic_influence_map.py \
  --write /tmp/pnva-heuristic-influence-map.json
python3 -m json.tool /tmp/pnva-heuristic-influence-map.json >/dev/null
```

## Production Rule

Every future PNVA runtime should keep:

```text
heuristic coverage at 1.0
proof coverage at 1.0
native influence clean
strong decisions covered by H2/H3/H4 authority
legacy observer rules out of production authority
```

That is how PNVA turns heuristic intelligence into disciplined runtime governance.
