# Malaria

## Data Source

**Malaria Atlas Project (MAP)**  
Big Data Institute, University of Oxford  
https://malariaatlas.org/

## Metrics

Two malaria prevalence indicators:

| Indicator | Definition |
|---|---|
| Pf prevalence | *Plasmodium falciparum* parasite rate (PfPR₂₋₁₀), multi-year average 2013–2022 |
| Pv prevalence | *Plasmodium vivax* parasite rate (PvPR₁₋₉₉), multi-year average 2013–2022 |

## Processing

Annual malaria prevalence rasters are downloaded from MAP and averaged over the 2013–2022 period. Results are uploaded to Google Earth Engine.

**Script:** [`malaria_average.ipynb`](malaria_average.ipynb) (from CCRR `script/data_prep/`)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/malaria_pf`  
- `projects/unicef-ccri/assets/hazards/malaria_pv`

## Output Format

- GEE raster assets (continuous: prevalence rate 0–1)
- Spatial resolution: ~0.1° (native: ~5 km)
- Coverage: malaria-endemic regions (global)
- Temporal coverage: 2013–2022 average

## Note

Malaria is included in exposure analysis but is excluded from the Multi-Hazard Intensity (MHI) PCA, as it represents a climate-sensitive disease rather than a direct physical hazard.

## Update Cadence

Updated when MAP releases new annual prevalence estimates.
