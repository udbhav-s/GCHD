# Case study scrapers

Scripts that pull case studies from external collections into `case_studies/`, in the shape defined by [`schema/case-study.schema.json`](../schema/case-study.schema.json).

```bash
pip install -r scripts/requirements.txt
```

These are not the web app's dependencies; that list is in `web_app/requirements.txt`.

## Climate-ADAPT

[Climate-ADAPT](https://climate-adapt.eea.europa.eu/en/knowledge/tools/case-study-explorer) is the European Environment Agency's collection of European climate adaptation case studies. It runs on Plone, which exposes a JSON REST API, so the scraper reads structured fields instead of parsing pages.

```bash
python scripts/scrape_climate_adapt.py              # writes into case_studies/
python scripts/scrape_climate_adapt.py --dry-run    # convert and report, write nothing
python scripts/scrape_climate_adapt.py --refresh    # re-fetch instead of using the cache
```

Responses are cached under `.cache/climate_adapt/` (gitignored). A re-run without `--refresh` reuses the cache, so the output is stable. Records are written one file per study, with IDs prefixed `climate-adapt-`.

The mapping decisions live in `climate_adapt_mapping.py` so they can be reviewed apart from the fetching code.

### What maps cleanly

| Climate-ADAPT field | Case-study field |
|---|---|
| `title`, `description` | `title`, `summary` |
| `climate_impacts` | `hazards` and `source_hazard_tags` |
| `geochars.countries` | `locations[].adm0`, with GeoRepo ucodes from `countries_info.csv` |
| `geolocation` | `point` |
| `websites` | `data_sources` |
| `UID`, `@type`, `cca_last_modified` | `provenance.source_*` |

### What does not

**Five impact tokens have no GCHD hazard.** `STORM` (39 studies) is European windstorm, which is not the `tropical_storm` hazard; `WATERSCARCE` (31) is a supply condition rather than a hazard layer; `ICEANDSNOW`, `EXTREMECOLD`, and `NONSPECIFIC` have no layer at all. These map to nothing and survive only in `source_hazard_tags`, which leaves 15 studies with an empty `hazards` array. The dashboard has no matching layer for any of them, so adding hazard IDs would create filters that correlate against nothing.

**`EXTREMEHEAT` maps to `extreme_heat`, not `heatwave`.** The source uses one token for both GCHD concepts. `extreme_heat` is the literal match and the one that corresponds to a layer the public app serves.

**Subnational units have no ucode.** Climate-ADAPT reports subnational coverage as NUTS-2 region *names* (`"Puglia (IT)"`), not codes. They are written at `adm1` with `ucode: null`, carrying `source_name` and `source_code`. Run `resolve_ucodes.py` once a GeoRepo boundary cache exists; NUTS-2 is `adm1` in some countries and `adm2` in others, so the resolver moves units between levels on match.

**Analytical inputs are not published.** `data_sources` holds the websites a study links to, tagged `contextual_input`. The API does not expose the datasets a study actually used. The bibliographic `source` field is left unread; it is free-text citations and would need parsing.

**SDG and indicator arrays are empty.** This scraper is structural only. Mapping UN Data Commons DCIDs per study is a separate enrichment pass.

## Schema 2.2 migrations

Two scripts bring older records up to 2.2, split by where the new fields can come from.

```bash
python scripts/migrate_c40_schema_22.py                 # the 630 scraped C40 records
python scripts/migrate_legacy_schema_22.py --apply      # the 8 hand-authored records
```

`migrate_c40_schema_22.py` refills every 2.2 field from the C40 API, keyed on each record's slug. The hand-authored records have no slug there and no manifest entry, so it cannot run on them at all.

`migrate_legacy_schema_22.py` covers those instead. It derives `population_focus` by scanning each record's own title and summary with the same term list the Climate-ADAPT scraper uses, and leaves `intervention`, `point`, and the tag arrays empty. Nothing in the source was captured to fill them, and guessing would put invented text behind a schema version that claims it was extracted.

These eight are the only records carrying `indicators_measured[].dcid` and `indicators_targeted[].rationale`. The migration leaves those untouched; they are the reference for the DCID enrichment the scrapers still lack.

## Resolving ucodes

```bash
python scripts/resolve_ucodes.py --db web_app/data/georepo/boundaries.sqlite          # dry run
python scripts/resolve_ucodes.py --db web_app/data/georepo/boundaries.sqlite --apply  # write
```

Matches region names against the boundary cache built by `web_app/scripts/build_georepo_cache.py`, within the record's country. Names are compared with accents, punctuation, and administrative prefixes (`Prov.`, `Regierungsbezirk`) stripped. A unit is only rewritten on an unambiguous match; everything else is printed for a human to resolve.

## Validating

```bash
python -c "
import json, glob, jsonschema
v = jsonschema.Draft202012Validator(json.load(open('schema/case-study.schema.json')))
for p in sorted(glob.glob('case_studies/*.json')):
    for e in v.iter_errors(json.load(open(p))):
        print(p, list(e.path), e.message)
"
```
