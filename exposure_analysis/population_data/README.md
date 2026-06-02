# Population Data

## Data Source

**WorldPop Gridded Population — Children Under 18**  
WorldPop, University of Southampton  
https://www.worldpop.org/

## Dataset Used

| Layer | Description | GEE Asset |
|---|---|---|
| Children (under 18) | Total children under 18 per 100 m pixel, 2025 | `projects/unicef-ccri/assets/population/worldpop_T_U18_2025_CN_100m` |
| Total population | Total population per 100 m pixel, 2025 | `projects/unicef-ccri/assets/population/worldpop_T_2025_CN_100m` |

Sex-disaggregated layers (girls, boys) are derived from the same WorldPop source.

## Spatial Resolution

100 m (approximately 0.001°)

## Temporal Reference

2025 baseline estimates.

## Usage

Population layers are used in Google Earth Engine to compute population-weighted exposure for each hazard via `reduceRegions`. The result is the number and share of children exposed in each administrative unit.

See [`country_level/`](../country_level/) for the exposure computation script.
