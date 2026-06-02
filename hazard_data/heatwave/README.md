# Heatwave and Extreme Heat

## Data Source

**ERA5 Reanalysis**  
European Centre for Medium-Range Weather Forecasts (ECMWF) via Google Earth Engine  
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

## Metrics

Four heat hazard indicators are derived from ERA5 daily maximum temperature data:

| Indicator | Definition |
|---|---|
| Heatwave frequency | Number of heatwave events per year (3+ consecutive days above the 90th percentile threshold) |
| Heatwave duration | Mean duration (days) of heatwave events |
| Heatwave severity | Mean temperature anomaly above threshold during heatwave events |
| Extreme heat degree-days | Cumulative temperature above 35°C per year |

The return-level exceedance is computed for each indicator.

## Processing

ERA5 daily maximum 2 m temperature is processed in Google Earth Engine to compute each indicator over a multi-decade baseline. Return levels are derived and uploaded as GEE assets.

**Script:** [`heatwave_RP.ipynb`](heatwave_RP.ipynb) (from CCRR `script/data_prep/`)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/heatwave_frequency`  
- `projects/unicef-ccri/assets/hazards/heatwave_duration`  
- `projects/unicef-ccri/assets/hazards/heatwave_severity`  
- `projects/unicef-ccri/assets/hazards/extreme_heat`

## Output Format

- GEE raster assets (continuous: return level scores)
- Spatial resolution: ~0.1° (native ERA5 resolution: 0.25°)
- Coverage: global (land areas)

## Update Cadence

Updated annually when ERA5 data for the most recent year is available.
