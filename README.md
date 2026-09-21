# Global Children's Hazard Database (GCHD)

**UNICEF Data Science | Climate & Environment Data Unit**

## Local public-data version

This fork adapts the original web application so its basic mapping and exposure
features can run without access to UNICEF's private Earth Engine assets. It:

- uses public Earth Engine datasets for WorldPop 2020 total population,
  ERA5-Land temperature, TerraClimate drought, and NASA FIRMS fire detections;
- uses a compact local cache built from the public UNICEF GeoRepo ADM0–ADM2
  exports for map boundaries, point selection, and `ucode` lookup;
- adds ADM2 code search (for example, `THA_0056_0005_V1`); and
- disables the AI assistant and email/login gate in this public-data mode.

These public layers provide a runnable subset of the original application. They
do not reproduce the complete private hazard catalog or its under-18 population
products.

### Run locally

1. Create the Python environment:

   ```bash
   cd web_app
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Put a Google Earth Engine service-account key from an Earth Engine-enabled
   Google Cloud project at `web_app/credentials/service_account.json`.

3. Download the public GeoRepo exports and build the local boundary cache
   (the raw downloads total roughly 2.2 GB):

   ```bash
   curl -L -o /tmp/adm0.geojson https://unidatadapmclimatechange.blob.core.windows.net/public/georepo/adm0.geojson
   curl -L -o /tmp/adm1.geojson https://unidatadapmclimatechange.blob.core.windows.net/public/georepo/adm1.geojson
   curl -L -o /tmp/adm2.geojson https://unidatadapmclimatechange.blob.core.windows.net/public/georepo/adm2.geojson

   python scripts/build_georepo_cache.py \
     --adm0 /tmp/adm0.geojson \
     --adm1 /tmp/adm1.geojson \
     --adm2 /tmp/adm2.geojson \
     --output data/georepo/boundaries.sqlite
   ```

4. To avoid watermarked CARTO basemap tiles, create `web_app/.env` with a
   [CARTO Basemaps API key](https://carto.com/basemaps/apikey/):

   ```dotenv
   CARTO_API_KEY=your-key
   ```

5. Start the app and open <http://localhost:8502>:

   ```bash
   python app.py
   ```

See [`web_app/README.md`](web_app/README.md) for additional configuration and
production-server notes. Credentials, `.env`, the virtual environment, and the
generated boundary database are excluded from Git.

The Global Children's Hazard Database (GCHD) is an open, spatially explicit database cataloguing children's exposure to climate, geophysical, and conflict hazards worldwide. It provides the foundational hazard data layer for UNICEF's [Children's Climate Risk Report (CCRR)](https://www.unicef.org/reports/climate-crisis-child-rights-crisis) and sub-national risk assessments.

---

## What is GCHD?

GCHD compiles globally consistent hazard datasets — each standardised, documented, and linked to a children's population exposure layer — to answer a single question:

> *How many children, and where, are exposed to each hazard?*

The database covers four hazard categories:

| Category | Hazards |
|---|---|
| **Climate** | River flood, coastal flood, tropical storm, agricultural drought, meteorological drought, heatwave, extreme heat, wildfire, sand & dust storm |
| **Climate-related** | Air pollution (PM2.5), malaria |
| **Geophysical** | Earthquake, volcano, landslide *(planned Q3 2026)* |
| **Environmental** | *(planned Q4 2026)* |
| **Conflict** | Armed conflict *(planned Q3 2026)* |

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
All hazard layers are processed at their original resolution (varying from 100 m to ~15 km depending on the source dataset) then overlaid with 100 m gridded children's population data for exposure computation.

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

An interactive dashboard built in Python Dash with Google Earth Engine map tiles is available at **[gchd.unicef.org](https://gchd.unicef.org)**.

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
