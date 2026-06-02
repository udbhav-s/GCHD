# Hazard Data

This folder contains per-hazard documentation and processing scripts for all hazard layers in the Global Children's Hazard Database.

Each subfolder corresponds to one hazard and contains:
- A `README.md` describing the data source, processing methodology, output format, and update cadence
- Processing script(s) (Jupyter notebooks or GEE JavaScript) used to prepare the hazard layer

Raw source data is not stored in this repository (files are too large). Final processed layers are hosted as Google Earth Engine assets under `projects/unicef-ccri/assets/hazards/`.

---

## Hazard Inventory

| Folder | Hazard | Source | Spatial Resolution | Processing Script |
|---|---|---|---|---|
| `flood/river_flood/` | River flood | JRC Global Flood Maps | ~0.1° | `flood_download.ipynb` |
| `flood/coastal_flood/` | Coastal flood | JRC Global Flood Maps | ~0.1° | `flood_download.ipynb` |
| `drought/agricultural_drought/` | Agricultural drought | FAO ASIS | ~0.1° | `ASI_RP.ipynb` |
| `drought/meteorological_drought/` | Meteorological drought (SPI-12, SPEI-12) | TerraClimate | ~0.1° | `compute_SPI_SPEI.ipynb` |
| `heatwave/` | Heatwave (frequency, duration, severity, extreme heat) | ERA5 / ECMWF | ~0.1° | `heatwave_RP.ipynb` |
| `tropical_storm/` | Tropical storm | GIRI | ~0.1° | Direct download |
| `fire/` | Wildfire (frequency, radiative power) | NASA FIRMS | ~0.1° | `Fire_90th_percentile.ipynb` |
| `air_pollution/` | PM2.5 air pollution | Satellite-derived | ~0.1° | `PM25_90th_percentile.ipynb` |
| `sand_dust_storm/` | Sand and dust storm | UNCCD | ~0.1° | Direct download |
| `malaria/` | Malaria (Pf, Pv) | MAP (Malaria Atlas Project) | ~0.1° | `malaria_average.ipynb` |
| `earthquake/` | Earthquake | *(planned Q3 2025)* | — | — |
| `volcano/` | Volcano | *(planned Q3 2025)* | — | — |
| `landslide/` | Landslide | *(planned Q3 2025)* | — | — |
| `conflict/` | Armed conflict | *(planned Q3 2025)* | — | — |

---

## Adding a New Hazard

1. Create a subfolder with a descriptive name (lowercase, underscores)
2. Add a `README.md` following the template used in existing hazard folders
3. Include or link the processing script used to prepare the GEE asset
4. Update this table
