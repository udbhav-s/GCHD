# River Flood

## Data Source

**JRC Global River Flood Hazard Maps**  
Joint Research Centre (JRC), European Commission  
https://global-flood-database.cloudnaturalresource.org/

## Metric

100-year return period inundation depth (1% annual probability of occurrence). Binary threshold applied to identify flood-prone areas.

## Processing

Data is downloaded and uploaded to Google Earth Engine as a raster asset. No additional statistical processing is applied beyond the return-period calculation embedded in the source data.

**Script:** [`flood_download.ipynb`](flood_download.ipynb) (from CCRR `script/data_prep/`)  
**GEE asset:** `projects/unicef-ccri/assets/hazards/river_flood`

## Output Format

- GEE raster asset (binary: 1 = flood-prone, 0 = not flood-prone)
- Spatial resolution: 90 m
- Coverage: global

## Known Data Caveats

- Fiji is force-nulled for river flood due to unreliable model outputs for small island geographies.

## Update Cadence

Updated when JRC releases a new version of the flood hazard maps.
