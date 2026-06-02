# Country-Level Exposure (ADM0)

## Overview

This folder contains scripts for computing and storing country-level (ADM0) children's exposure to all GCHD hazard layers.

## Processing

Population-weighted exposure is computed in Google Earth Engine using `reduceRegions` over ADM0 country boundaries.

**Scripts** (from CCRR `script/data_prep/`):
- [`hazard_exposure_new.ipynb`](hazard_exposure_new.ipynb) — Country-level exposure computation (primary script)
- [`adm2_hazard_exposure_updated.ipynb`](adm2_hazard_exposure_updated.ipynb) — Sub-national exposure (also used for ADM0 aggregation)

## Output

**File:** `Hazard_Population_Exposure.csv`

Columns include, for each of 17 hazards:
- `{hazard}_n_children` — absolute children exposed
- `{hazard}_pct_children` — % of national child population exposed
- `{hazard}_n_girls`, `{hazard}_n_boys` — sex-disaggregated counts

Plus MHC distribution columns and MHI threshold columns (p75–p95).

Coverage: 229 countries and territories.

## Running the Script

Requires:
- Google Earth Engine Python API authenticated with a service account
- GEE assets: all 17 hazard layers, MHI raster, population layers, ADM0 boundaries

```bash
jupyter nbconvert --to notebook --execute hazard_exposure_new.ipynb
```
