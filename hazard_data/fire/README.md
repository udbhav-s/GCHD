# Wildfire

## Data Source

**NASA FIRMS (Fire Information for Resource Management System)**  
NASA / USFS  
https://firms.modaps.eosdis.nasa.gov/

## Metrics

Two fire hazard indicators derived from NASA FIRMS active fire detections:

| Indicator | Definition |
|---|---|
| Fire frequency | Number of fire events per year (90th percentile over the study period) |
| Fire radiative power (FRP) | Mean fire radiative power (MW) of detected fire events (90th percentile) |

## Processing

NASA FIRMS MODIS/VIIRS active fire detections are processed in Google Earth Engine to compute annual fire frequency and mean FRP per pixel. The 90th percentile is computed over a multi-year period and uploaded as GEE assets.

**Script:** [`Fire_90th_percentile.ipynb`](Fire_90th_percentile.ipynb) (from CCRR `script/data_prep/`)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/fire_frequency`  
- `projects/unicef-ccri/assets/hazards/fire_frp`

## Output Format

- GEE raster assets (continuous: 90th percentile scores)
- Spatial resolution: ~0.1°
- Coverage: global (land areas with fire detections)

## Update Cadence

Updated annually when new FIRMS data is available.
