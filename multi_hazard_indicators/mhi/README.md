# Multi-Hazard Intensity (MHI)

## Definition

The **Multi-Hazard Intensity (MHI)** is a continuous pixel-level composite score (0–10) that captures the combined intensity of climate hazards at each location. Unlike MHC, which counts the number of hazards, MHI weights hazards by their severity and distinguishes between areas with frequent mild events and those exposed to less frequent but more catastrophic events.

## Methodology

MHI is constructed from **13 climate hazard layers** using Principal Component Analysis (PCA):

| Hazard Layers in MHI |
|---|
| River flood |
| Coastal flood |
| Agricultural drought |
| Meteorological drought SPI-12 |
| Meteorological drought SPEI-12 |
| Heatwave frequency |
| Heatwave duration |
| Heatwave severity |
| Extreme heat degree-days |
| Tropical storm |
| Wildfire frequency |
| Wildfire radiative power |
| Sand and dust storm |

**Excluded from MHI:** Air pollution (PM2.5) and malaria — these represent chronic or disease-based exposures rather than episodic physical hazard events.

### Construction Steps

1. **Export** 13 hazard rasters + land-sea mask from GEE at ~0.1° resolution
2. **Log-transform** each hazard layer to reduce skewness
3. **Z-score normalise** across land pixels only (ocean pixels excluded)
4. **PCA** — fit on land pixels, derive principal component weights
5. **MinMax scale** to 0–10 range
6. **Output:** `MHI_climate.tif` → uploaded to GEE as `projects/unicef-ccri/assets/hazards/MHI_climate`

## Processing

**GEE export script:** [`MHI_input_gee.js`](MHI_input_gee.js) (from CCRR `script/multi_hazard/`)  
**PCA construction:** [`mhi_construction.ipynb`](mhi_construction.ipynb) (from CCRR `script/multi_hazard/`)

```
# Run PCA and construct MHI
# Requires: data/misc/ccri_pixel/*.tif (13 hazard TIFs + landSeaMask.tif)
jupyter nbconvert --to notebook --execute mhi_construction.ipynb
```

**Output file:** `MHI_climate.tif`

## Exposure Aggregation

Country and sub-national MHI exposure is reported as:
- Share of children above global MHI percentile thresholds: p75, p80, p85, p90, p95
- Available in `exposure_analysis/country_level/`
