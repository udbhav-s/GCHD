# Global Children's Hazard Database (GCHD) — public-data fork

**Hazard and exposure screening. Not a risk assessment.**

This fork runs a working subset of UNICEF's GCHD dashboard using only public
Earth Engine datasets, so it needs no access to UNICEF's private assets. It maps
three hazard layers over a gridded child population and counts how many children
live where each hazard is flagged.

It stops there. Under the UNDRR and [INFORM](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Methodology)
framing, risk is hazard combined with exposure, vulnerability and coping
capacity. This app holds the first two. It carries nothing on vulnerability,
nothing on coping capacity, no likelihood or return periods, no future
scenarios, and no uncertainty measures. Read its numbers as a screen for where
to look, not as a measure of risk to children.

## What it runs

| Layer | Source | Flagged when | Resolution |
|---|---|---|---|
| Extreme heat | ERA5-Land daily, 2024 | the highest daily maximum went above 35 °C | ~11 km |
| Drought | TerraClimate PDSI, 2024 | the lowest monthly PDSI fell below −2 | ~4 km |
| Fire | NASA FIRMS, 2024 | at least one daily detection landed in the cell | ~1 km |
| Child population | WorldPop 2020 age and sex bands | — | 100 m |

Children are the under-18 bands, with 15–19 counted at three fifths.

Two things to keep in mind when reading any figure this produces:

**The hazard flags are occurrence, not severity.** A place with two days above
35 °C and a place above 35 °C for most of the year are the same pixel. Measured
across the land this flags, days above 35 °C run from 2 at the 10th percentile
to 343 at the maximum, and every one of them counts equally.

**They are single-year statistics, not return periods.** Each layer describes
2024 and says nothing about how likely those conditions are in any other year.
2024 was the warmest year on record, so the heat layer reads hot against a
longer baseline.

The **Multi Hazard Count** is how many of the three topics flag a pixel. It is a
tally, not a score: two topics does not mean twice the harm of one.

Alongside the map, 638 case studies drawn from C40, Climate-ADAPT and other
sources are joined to administrative boundaries as a discovery layer. 217 of
them carry no hazard tag and so cannot be reached by a hazard filter — mostly
C40 records about waste, transport and energy efficiency that address no hazard.

## Run it

```bash
cd web_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Put an Earth Engine service-account key at
`web_app/credentials/service_account.json`, then build the boundary cache. The
raw downloads total about 2.2 GB and the build takes a couple of minutes:

```bash
BASE=https://unidatadapmclimatechange.blob.core.windows.net/public/georepo
curl -L -o /tmp/adm0.geojson $BASE/adm0.geojson
curl -L -o /tmp/adm1.geojson $BASE/adm1.geojson
curl -L -o /tmp/adm2.geojson $BASE/adm2.geojson

python scripts/build_georepo_cache.py \
  --adm0 /tmp/adm0.geojson --adm1 /tmp/adm1.geojson --adm2 /tmp/adm2.geojson \
  --output data/georepo/boundaries.sqlite
```

Take all three from one export — mixing vintages risks ucodes that no longer
match what the case studies record. A good build gives 289 countries, 3,578
provinces and 41,092 districts.

```bash
python app.py     # http://localhost:8502
```

To avoid watermarked basemap tiles, put a
[CARTO Basemaps API key](https://carto.com/basemaps/apikey/) in `web_app/.env`
as `CARTO_API_KEY`. See [`web_app/README.md`](web_app/README.md) for production
notes.

## Tests

```bash
pip install -r requirements-dev.txt
pytest              # unit and data tests
pytest -m slow      # adds one live Earth Engine check, needs credentials
```

The boundary tests skip themselves when no cache has been built.

## Repository layout

```
GCHD/
├── case_studies/            # 638 records, schema 2.2
├── schema/                  # Case-study schema and hazard taxonomy
├── web_app/                 # The dashboard (Dash + Earth Engine)
├── hazard_data/             # Per-hazard source documentation
├── multi_hazard_indicators/ # Upstream multi-hazard work, not wired in here
├── exposure_analysis/       # Separate pipeline with its own boundary inputs
├── scripts/                 # Scrapers, migrations, ucode resolution
└── tests/
```

## The wider GCHD programme

This section describes UNICEF's GCHD, **not the code in this fork.** The full
database catalogues children's exposure to climate, geophysical and conflict
hazards worldwide across many more layers than the three here, at return periods
this fork does not carry, and it supplies the hazard pillar of UNICEF's
[Children's Climate Risk Report](https://unicef.github.io/CCRR/). For that work
see [unicef/GCHD](https://github.com/unicef/GCHD).

The CCRR pairs that hazard pillar with a child vulnerability pillar built from
17 indicators. Compositing hazard with vulnerability happens there, not here.

> UNICEF (2025). *Global Children's Hazard Database (GCHD)*. UNICEF Office of
> Strategy and Evidence, Climate & Environment Data Team.
> https://github.com/unicef/GCHD

**Contact** — Dohyung Kim, Data Science Specialist, UNICEF · dokim@unicef.org
