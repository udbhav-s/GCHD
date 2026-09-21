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

Download the public ADM0–ADM2 exports linked from
[`georepo-data`](../../georepo-data/README.md), then run:

```bash
python scripts/build_georepo_cache.py \
  --adm0 /path/to/adm0.geojson \
  --adm1 /path/to/adm1.geojson \
  --adm2 /path/to/adm2.geojson \
  --output data/georepo/boundaries.sqlite
```

The generated database is intentionally ignored by Git. It retains only current
(`is_latest`) boundaries, simplifies geometry for web display, and preserves UNICEF
GeoRepo `ucode` identifiers.

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

## Environment Notes

- AI and email authentication are disabled in public-data mode.
- Administrative boundary data must be attributed to UNICEF GeoRepo under CC BY 4.0.
