# Multi-Hazard Count (MHC)

## Definition

The **Multi-Hazard Count (MHC)** quantifies the number of distinct climate hazard categories that a geographic area is exposed to. It provides a simple, interpretable measure of multi-hazard burden.

MHC is computed at 100 m resolution (matching the children's population grid) and aggregated to country and sub-national administrative levels using population-weighted methods.

## Hazard Categories Included

MHC counts exposure across the following climate hazard categories (maximum MHC = 8):

1. Flood (river or coastal)
2. Drought (agricultural or meteorological)
3. Heatwave / Extreme heat
4. Tropical storm
5. Wildfire
6. Air pollution (PM2.5)
7. Sand and dust storm
8. Malaria

A location is counted as exposed to a category if it exceeds the binary threshold for any hazard within that category.

## Use Cases

- Identifying geographic hotspots where children face disproportionately high multi-hazard burden
- Prioritising areas for compound disaster preparedness planning
- Informing UNICEF country programme targeting and climate finance applications

## Processing

**Script:** [`hazard_combination.ipynb`](hazard_combination.ipynb) (from CCRR `script/data_prep/`)  
**GEE asset:** `projects/unicef-ccri/assets/hazards/MHC`

The MHC raster is computed in Google Earth Engine by summing binary hazard layers per pixel, then uploaded as a GEE asset for use in country-level exposure computation.

## Output Format

- GEE raster asset (integer: 0–8)
- Spatial resolution: 100 m
- Coverage: global (land areas)

## Exposure Aggregation

Country and sub-national MHC exposure is reported as:
- Count and share of children exposed to 1, 2, 3, … 8+ hazard categories
- Available in `exposure_analysis/country_level/` and `exposure_analysis/subnational_level/`
