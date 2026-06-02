# Meteorological Drought

## Data Source

**TerraClimate**  
Climatology Lab, University of California, Merced  
https://www.climatologylab.org/terraclimate.html

## Metrics

Two standardised drought indices computed at 12-month accumulation period:

- **SPI-12** (Standardised Precipitation Index): measures precipitation deficit relative to long-term average
- **SPEI-12** (Standardised Precipitation-Evapotranspiration Index): measures water balance deficit accounting for temperature-driven evapotranspiration

The hazard indicator is an **empirical drought probability**: the number of months in which the index falls below the drought threshold (−1.5), divided by the total number of months in the full study period (1958–2025, 804 monthly time steps). This gives a dimensionless probability score between 0 and 1 representing how often a location experiences drought conditions.

## Processing

Monthly precipitation (and temperature/PET for SPEI) data is downloaded from TerraClimate. SPI-12 and SPEI-12 are computed across the full 1958–2025 record. For each pixel, the number of months where the index falls below the drought threshold (−1.5) is counted and divided by the total number of months (804) to produce an empirical probability score, which is then uploaded to Google Earth Engine.

**Processing repository:** [github.com/dohyung-kim/precip-index](https://github.com/dohyung-kim/precip-index)  
**GEE assets:**  
- `projects/unicef-ccri/assets/hazards/SPI12`  
- `projects/unicef-ccri/assets/hazards/SPEI12`

## Output Format

- GEE raster assets (continuous: standardised index values)
- Spatial resolution: 5 km
- Coverage: global (land areas)

## Update Cadence

Updated when TerraClimate releases new annual data.
