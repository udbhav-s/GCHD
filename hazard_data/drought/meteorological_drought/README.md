# Meteorological Drought

## Data Source

**TerraClimate**  
Climatology Lab, University of California, Merced  
https://www.climatologylab.org/terraclimate.html

## Metrics

Two standardised drought indices computed at 12-month accumulation period:

- **SPI-12** (Standardised Precipitation Index): measures precipitation deficit relative to long-term average
- **SPEI-12** (Standardised Precipitation-Evapotranspiration Index): measures water balance deficit accounting for temperature-driven evapotranspiration

The 90th percentile of SPI-12 and SPEI-12 severity is used as the hazard indicator.

## Processing

Monthly precipitation (and temperature/PET for SPEI) data is downloaded from TerraClimate. SPI and SPEI are computed over a multi-decade baseline period, and the 90th percentile of drought severity is extracted and uploaded to Google Earth Engine.

**Script:** [`compute_SPI_SPEI.ipynb`](compute_SPI_SPEI.ipynb) (from CCRR `script/data_prep/`)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/SPI12`  
- `projects/unicef-ccri/assets/hazards/SPEI12`

## Output Format

- GEE raster assets (continuous: standardised index values)
- Spatial resolution: 5 km
- Coverage: global (land areas)

## Update Cadence

Updated when TerraClimate releases new annual data.
