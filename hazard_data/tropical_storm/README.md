# Tropical Storm

## Data Source

**GIRI (Global Intensity-based Risk Index) — Tropical Cyclone Wind Speed Hazard**  
UNDRR / Reask  
https://www.giri.unepgrid.ch/

## Metric

100-year return period maximum wind speed (1% annual probability of occurrence). Captures areas exposed to tropical cyclone-force winds.

## Processing

Data is downloaded directly from the GIRI platform and uploaded to Google Earth Engine as a raster asset. No additional statistical processing is applied.

**GEE asset:** `projects/unicef-ccri/assets/hazards/tropical_storm`

## Output Format

- GEE raster asset (continuous: wind speed in km/h at 100-year return)
- Spatial resolution: 10 km
- Coverage: tropical and sub-tropical regions (global where cyclone tracks exist)

## Update Cadence

Updated when GIRI releases a new version of the tropical cyclone hazard layer.
