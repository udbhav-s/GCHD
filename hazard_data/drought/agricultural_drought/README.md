# Agricultural Drought

## Data Source

**FAO Agricultural Stress Index (ASIS)**  
Food and Agriculture Organization of the United Nations  
https://www.fao.org/giews/earthobservation/asis/

## Metric

Return-level exceedance probability derived from the FAO Agricultural Stress Index. Captures frequency and severity of agricultural drought affecting crop-producing areas.

## Processing

Raw ASIS data is downloaded from FAO and processed to compute return levels. The result is uploaded to Google Earth Engine as a raster asset.

**Script:** [`ASI_RP.ipynb`](ASI_RP.ipynb) (from CCRR `script/data_prep/`)  
**GEE asset:** `projects/unicef-ccri/assets/hazards/agricultural_drought`

## Output Format

- GEE raster asset (continuous: return level score)
- Spatial resolution: 1 km
- Coverage: global (agricultural areas)

## Update Cadence

Updated annually when FAO ASIS data for the most recent growing season is available.
