# Air Pollution (PM2.5)

## Data Source

**Annual PM2.5 Concentrations (satellite-derived)**  
Hammer et al. / Atmospheric Composition Analysis Group  
https://sites.wustl.edu/acag/datasets/surface-pm2-5/

## Metric

90th percentile of annual mean PM2.5 concentration (µg/m³) over the period 1998–2023. Captures chronic high-pollution exposure, which poses significant health risks especially for children.

## Processing

Annual PM2.5 rasters are downloaded and processed in Google Earth Engine to compute the 90th percentile over the full study period. The result is uploaded as a GEE asset.

**Script:** [`PM25_90th_percentile.ipynb`](PM25_90th_percentile.ipynb) (from CCRR `script/data_prep/`)  
**GEE asset:** `projects/unicef-ccri/assets/hazards/PM25`

## Output Format

- GEE raster asset (continuous: µg/m³)
- Spatial resolution: ~0.1° (native: ~1 km)
- Coverage: global (land areas)
- Temporal coverage: 1998–2023

## Note

PM2.5 is included in the exposure analysis but is excluded from the Multi-Hazard Intensity (MHI) PCA due to its fundamentally different nature (chronic ambient pollution vs. episodic hazard events).

## Update Cadence

Updated when a new version of the annual PM2.5 dataset is released (typically annually with ~2 year lag).
