# GCHD Web Application

Interactive dashboard for the Global Children's Hazard Database.

## Tech Stack

| Component | Technology |
|---|---|
| Web framework | [Python Dash](https://dash.plotly.com/) |
| Map layer | [dash-leaflet](https://dash-leaflet.onrender.com/) with GEE tile URLs |
| Charts | [Plotly](https://plotly.com/python/) |
| Hazard data | [Google Earth Engine](https://earthengine.google.com/) (Python API) |
| Boundary data | Local UNICEF GeoRepo cache |
| Server | Gunicorn + Nginx |

## File Structure

```
web_app/
├── app.py              # Main Dash layout and callbacks
├── gee_core.py         # GEE authentication, tile URL generation, exposure queries
├── exposure_math.py    # Child population arithmetic, no GEE import so it is testable
├── config.py           # Hazard list, topics, colour palettes, admin level config
├── georepo_core.py     # Local administrative-boundary queries
├── scripts/            # GeoRepo preprocessing utility
├── requirements.txt    # Python dependencies
├── nginx-pixel-aid.conf
├── credentials/        # Secret files — see setup below (NEVER committed to git)
└── assets/
    ├── style.css
    └── unicef_*.png
```

## Setup

### 1. Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional local settings can be placed in `web_app/.env`. For example,
`CARTO_API_KEY` is appended to CARTO basemap tile requests as the `key`
query parameter.

### 2. Earth Engine credentials

Create `credentials/service_account.json` containing a key for a service account in
your Earth Engine-registered Google Cloud project. The project ID is read from the
JSON file; it can be overridden with the `EARTH_ENGINE_PROJECT` environment variable.

### 3. Build the GeoRepo boundary cache

The GeoRepo API is retired and answers 410 on every endpoint, so the boundaries
come from the public blob exports instead. All three were published together on
16 September 2026 and carry real GeoRepo ucodes:

```bash
BASE=https://unidatadapmclimatechange.blob.core.windows.net/public/georepo
curl -L -o /tmp/adm0.geojson $BASE/adm0.geojson   # 224 MB
curl -L -o /tmp/adm1.geojson $BASE/adm1.geojson   # 539 MB
curl -L -o /tmp/adm2.geojson $BASE/adm2.geojson   # 1.4 GB

python scripts/build_georepo_cache.py \
  --adm0 /tmp/adm0.geojson \
  --adm1 /tmp/adm1.geojson \
  --adm2 /tmp/adm2.geojson \
  --output data/georepo/boundaries.sqlite
```

Take all three from the same export. Mixing vintages risks ucodes that no longer
match the ones case studies record. The build takes a couple of minutes and
produces roughly 289 countries, 3,578 provinces, and 41,092 districts.

The generated database is intentionally ignored by Git. It retains only current
(`is_latest`) boundaries, simplifies geometry for web display, and preserves UNICEF
GeoRepo `ucode` identifiers.

Build somewhere else first and swap the file in if one is already in place, and
remove any leftover `-wal` and `-shm` sidecars so they cannot pair with the new
database. `scripts/build_standin_boundary_cache.py` is a Natural Earth fallback
that covers ADM0 and ADM1 only; it is for making the app runnable, not for
analysis.

### 4. Public Earth Engine data

No access to `projects/unicef-ccri/assets` is required. The app uses public catalog
datasets: WorldPop 2020 population, ERA5-Land 2024 maximum temperature,
TerraClimate 2024 PDSI, and FIRMS 2024 active-fire detections.

### 5. Run (development)

```bash
python app.py
```

App runs at http://localhost:8502.

### 6. Deploy (production)

```bash
gunicorn -w 4 -b 127.0.0.1:8502 app:server
```

Configure Nginx using `nginx-pixel-aid.conf` as a template. Update the `server_name` directive to match your domain and update SSL certificate paths.

## Tests

Run from the repository root, not from here:

```bash
pip install -r ../requirements-dev.txt
pytest              # unit and data tests
pytest -m slow      # adds a live Earth Engine exposure check
```

The boundary tests skip when `data/georepo/boundaries.sqlite` is absent, so a
clean checkout still runs green.

## Environment Notes

- AI and email authentication are disabled in public-data mode.
- Administrative boundary data must be attributed to UNICEF GeoRepo under CC BY 4.0.
- The dashboard reports hazard and exposure only. It holds no vulnerability or
  coping-capacity data, so its figures are a screening aid rather than a measure
  of risk. Layer descriptions in `config.py` carry the limits of each input;
  keep them filled in for anything new.
