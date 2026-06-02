# Exposure Analysis

This folder contains documentation and scripts for computing children's exposure to GCHD hazard layers at country and sub-national levels.

Exposure is computed by overlaying hazard layers with gridded children's population data using Google Earth Engine's `reduceRegions` function over administrative boundaries.

## Sub-folders

| Folder | Contents |
|---|---|
| [`population_data/`](population_data/) | Children's population grid and documentation |
| [`boundary_files/`](boundary_files/) | Administrative boundary layers used for aggregation |
| [`country_level/`](country_level/) | Country-level (ADM0) exposure outputs and scripts |
| [`subnational_level/`](subnational_level/) | Sub-national (ADM1/ADM2) exposure outputs |

## Exposure Metrics

For each hazard layer, exposure is reported as:

| Metric | Description |
|---|---|
| `n_children_exposed` | Absolute number of children under 18 exposed |
| `pct_children_exposed` | Percentage of national/subnational child population exposed |
| `n_girls_exposed` | Absolute number of girls exposed |
| `n_boys_exposed` | Absolute number of boys exposed |
| `n_people_exposed` | Total population exposed |
| `pct_people_exposed` | Percentage of total population exposed |

Multi-hazard exposure (MHC and MHI) is additionally reported as:
- Children exposed to 1–8+ hazard categories (MHC distribution)
- Children above global MHI percentile thresholds (p75 through p95)
