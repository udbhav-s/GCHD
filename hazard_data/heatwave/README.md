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

ERA5 Land daily maximum 2 m temperature is processed in Google Earth Engine to compute annual values of each indicator. Return levels are then derived pixel-by-pixel using an **empirical (non-parametric) method** based on the Weibull plotting position:

1. Annual values for each pixel are sorted in descending order
2. The empirical return period for each ranked value is estimated as `(n + 1) / rank`
3. Return levels for standard return periods (10, 30, 50, 100 years) are interpolated from this empirical distribution

This approach requires no parametric distribution fitting (e.g. GEV or Gumbel) and is applied directly to the observed annual record. A minimum of 5 years of valid data is required per pixel.

**Processing repository:** [github.com/unicef/heat](https://github.com/unicef/heat)  
**Script:** `heatwave_RP.ipynb`  
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
