# Heatwave and Extreme Heat

## Data Source

**ERA5 Land / ERA5 Reanalysis**  
European Centre for Medium-Range Weather Forecasts (ECMWF)  
https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

ERA5 Land is used as the primary data source for the majority of land areas. For small island states where ERA5 Land coverage is missing, ERA5 Reanalysis data is used as a supplement.

## Metrics

Four heat hazard indicators are derived from ERA5 daily maximum temperature data:

| Indicator | Definition |
|---|---|
| Heatwave frequency | Any period of three days or more when the maximum temperature each day is in the top 10 per cent of the local 15-day average between 1960 and 1990 |
| Heatwave duration | Average length of heatwave event (number of days) |
| Heatwave severity | Average exceedance in degrees Celsius of the heatwave threshold for each event |
| Extreme high temperature | Annual average number of days in which 35°C is exceeded |

## Processing

ERA5 daily maximum 2 m temperature is processed in Google Earth Engine to compute each indicator over a multi-decade baseline. Return levels are derived and uploaded as GEE assets.

**Processing repository:** [github.com/unicef/heat](https://github.com/unicef/heat)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/heatwave_frequency`  
- `projects/unicef-ccri/assets/hazards/heatwave_duration`  
- `projects/unicef-ccri/assets/hazards/heatwave_severity`  
- `projects/unicef-ccri/assets/hazards/extreme_heat`

## Output Format

- GEE raster assets (continuous: return level scores)
- Spatial resolution: 10 km
- Coverage: global (land areas)

## Update Cadence

Updated annually when ERA5 data for the most recent year is available.
