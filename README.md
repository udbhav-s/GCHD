# Global Children's Hazard Database (GCHD) — public-data fork

**Hazard and exposure screening. Not a risk assessment.**

This fork runs a working subset of UNICEF's GCHD dashboard using only public
Earth Engine datasets, so it needs no access to UNICEF's private assets. It maps
three hazard layers over a gridded child population and counts how many children
live where each hazard is flagged.

Under the UNDRR and [INFORM](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Methodology)
framing, risk is hazard combined with exposure, vulnerability and coping
capacity. This app now holds something of all four, thinly: hazard and exposure
in full, the share of children under five as vulnerability, and travel time to
the nearest health facility as coping capacity. It has no future scenarios and
no uncertainty measures. Read its numbers as a screen for where to look, not as
a measure of risk to children.

The three constructs are shown separately and never multiplied together. You can
ask for the intersection — children exposed to a hazard who are also more than an
hour from care — and get a count you can check. What you cannot get is a single
score, because that needs a weighting this app cannot defend, and the last
composite it carried turned out to be measuring nothing.

Travel time is about whether care can be reached, not whether it can treat
anyone. No global data exists on beds, staff or paediatric capability, so a
reachable clinic and a functioning hospital look identical here.

## What it runs

| Layer | Source | What it counts | Resolution |
|---|---|---|---|
| Extreme heat | ERA5-Land daily, 2024 | days above 35 °C | ~11 km |
| Drought | TerraClimate PDSI, 2024 | months below −2 | ~4 km |
| Fire | NASA FIRMS, 2024 | days with a detection | ~1 km |
| Child population | WorldPop 2020 age and sex bands | — | 100 m |

Children are the under-18 bands, with 15–19 counted at three fifths.

Two things to keep in mind when reading any figure this produces:

**You choose how long a hazard has to last.** Each layer counts the time steps
that met its condition, and you set the minimum before a place counts as
exposed — any, 7 days or 30 days for heat and fire; any, 2 months or 3 months
for drought. The units follow the source and are deliberately not normalised:
temperature and fire are recorded daily, drought monthly, so twelve readings a
year is the most drought can resolve.

The default is "any", which reproduces the older behaviour of asking only
whether a hazard ever occurred. It is worth moving off it. Globally, a third of
land saw at least one day above 35 °C in 2024, and among those places the count
runs from 2 days to 343 — figures at the default treat all of them alike.

**You can ask how typical 2024 was.** A period control switches between what
happened in 2024 and how often a year like it occurred across a longer record —
1991–2020 for heat and drought, 2001–2024 for fire, which is as far back as the
satellite fire record goes. In that second view you also choose how often a
qualifying year has to turn up: 1, 3 or 5 years in ten. Counts are stated per
ten years because the baselines are different lengths.

The difference matters. In Bang Rak, Bangkok, 36,414 children lived where 2024
brought 30 or more days above 35 °C. Where that happens in 3 years out of 10,
the figure is 6,457. At 5 years in 10 it is zero. 2024 was the warmest year on
record and the app can now show what that means locally.

**These are still not return periods.** Thirty years of record cannot support a
one-in-a-hundred-year claim, so nothing here makes one. The language throughout
is years in ten.

**Counting length is not measuring intensity.** A day at 35.1 °C counts the same
as a day at 45 °C, and the threshold is fixed worldwide, so it ignores that
people acclimatise to their own climate.

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
