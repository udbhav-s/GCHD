# Global Children's Hazard Database (GCHD)

**UNICEF Data Science | Climate & Environment Data Unit**

The Global Children's Hazard Database (GCHD) is an open, spatially explicit database cataloguing children's exposure to climate, geophysical, and conflict hazards worldwide. It provides the foundational hazard data layer for UNICEF's [Children's Climate Risk Report (CCRR)](https://www.unicef.org/reports/climate-crisis-child-rights-crisis) and sub-national risk assessments.

---

## What is GCHD?

GCHD compiles globally consistent hazard datasets — each standardised, documented, and linked to a children's population exposure layer — to answer a single question:

> *How many children, and where, are exposed to each hazard?*

The database covers four hazard categories:

| Category | Hazards |
|---|---|
| **Climate** | River flood, coastal flood, tropical storm, agricultural drought, meteorological drought, heatwave, extreme heat, wildfire, air pollution (PM2.5), sand & dust storm, malaria |
| **Geophysical** | Earthquake, volcano, landslide *(planned Q3 2025)* |
| **Environmental** | *(planned Q4 2025)* |
| **Conflict** | Armed conflict *(planned Q3 2025)* |

---

## Repository Structure

```
GCHD/
├── hazard_data/             # Per-hazard source documentation and processing scripts
├── multi_hazard_indicators/ # Multi-Hazard Count (MHC) and Multi-Hazard Intensity (MHI)
├── exposure_analysis/       # Population and boundary data for exposure computation
├── web_app/                 # Interactive dashboard (Python Dash + Google Earth Engine)
└── index.html               # Public landing page
```

---

## Hazard Coverage

### Spatial Resolution
All hazard layers are processed at a globally consistent resolution (approximately 0.1° / ~10 km) for country-level exposure aggregation, and at 100 m for pixel-level multi-hazard composite scores.

### Population Reference
Children's exposure is computed using **WorldPop gridded population estimates for children under 18, 2025 baseline**, at 100 m spatial resolution.

### Exposure Computation
Population-weighted exposure is computed via Google Earth Engine using `reduceRegions` over country and sub-national boundaries. Results are expressed as:
- Absolute count of children exposed
- Share of the national/subnational child population exposed
- Separate estimates for girls and boys

---

## Multi-Hazard Indicators

Two composite indicators summarise multi-hazard exposure:

**Multi-Hazard Count (MHC)** — the number of distinct hazard categories a location is exposed to. Identifies hotspots where children face multiple simultaneous hazards.

**Multi-Hazard Intensity (MHI)** — a continuous 0–10 pixel-level score derived from Principal Component Analysis (PCA) across 13 climate hazard layers. Distinguishes areas with frequent mild events from those with infrequent but extreme events.

See [`multi_hazard_indicators/`](multi_hazard_indicators/) for methodology and scripts.

---

## Web Application

An interactive dashboard built in Python Dash with Google Earth Engine map tiles is available at **[gchd.pixel-aid.com](https://gchd.pixel-aid.com)**.

Source code is in [`web_app/`](web_app/).

---

## Data Sources

| Hazard | Source | Return Period / Metric |
|---|---|---|
| River flood | JRC Global Flood Maps | 100-year return level|
| Coastal flood | JRC Global Flood Maps | 100-year return level|
| Tropical storm | GIRI | 100-year return level |
| Agricultural drought | FAO ASIS | 100-year return level|
| Meteorological drought | TerraClimate (SPI-12, SPEI-12) | emprical probability |
| Heatwave | ERA5 / ECMWF | Frequency, duration, severity  100-year return level|
| Extreme heat | ERA5 / ECMWF | Degree-days 100-year return level|
| Wildfire | NASA FIRMS | 90th percentile |
| Air pollution (PM2.5) | Satellite-derived | 90th percentile, 1998–2023 |
| Sand & dust storm | UNCCD | Occurrence frequency |
| Malaria | MAP (Malaria Atlas Project) | Multi-year average, 2013–2022 |

---

## Citing GCHD

> UNICEF (2025). *Global Children's Hazard Database (GCHD)*. UNICEF Office of Strategy and Evidence, Climate & Environment Data Team. https://github.com/unicef/GCHD

---

## Contact

**Dohyung Kim** — Data Science Specialist, UNICEF  
dokim@unicef.org
