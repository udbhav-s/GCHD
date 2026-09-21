# Case study schema

Mirror Worlds case studies use [`case-study.schema.json`](case-study.schema.json), a JSON Schema Draft 2020-12 document. Version `2.0` adds administrative coverage, Global Children's Hazard Database (GCHD) hazard tags, analytical data sources, and record provenance while retaining the existing SDG and UN Data Commons indicator fields.

## Geographic coverage

`location_scope` records the most specific geography supported by the source: `global`, `adm0`, `adm1`, `adm2`, or `non_administrative`.

`locations` is an array of complete administrative paths. Each path contains `adm0`, `adm1`, and `adm2`; levels below the study's documented scope are `null`. A study covering several districts has one location object per district. Keeping the full hierarchy together avoids ambiguous parallel arrays.

Administrative units use UNICEF GeoRepo `ucode` values so the GCHD application can join a case study to its existing ADM0-ADM2 boundary cache. `dcid` is optional in practice and is `null` when UN Data Commons does not expose a matching geography. Do not copy boundary polygons into case-study files.

For named places that are not administrative regions, such as a refugee camp or watershed, use `location_scope: "non_administrative"`, put the name in `place_name`, and include only the containing administrative units that can be verified.

Global studies have `location_scope: "global"` and an empty `locations` array.

## Hazards

`hazards` is an array of controlled GCHD hazard concepts. It is intentionally separate from `indicators_measured` and `indicators_targeted`:

- Hazard IDs select or filter GCHD physical hazard layers.
- Indicator DCIDs identify statistical measures and outcomes available through UN Data Commons.

The allowed hazard IDs are defined by the schema. An empty array is valid for legacy case studies that are useful historical twins but do not analyze a GCHD hazard.

GCHD's more specific raster codes—such as `river_flood_100yr`, `heatwave_frequency`, and `drought_spi_tc`—belong in a shared application-level hazard taxonomy rather than being repeated in every case-study record.

## Sources and provenance

`data_sources` lists inputs used by the analysis itself, such as satellite imagery, household surveys, population grids, or operational records. `role` uses a small controlled vocabulary so sources can be filtered consistently.

`provenance` describes where Mirror Worlds found the case-study record. It distinguishes the hosting collection (for example, NASA DEVELOP, UNICEF Data for Action, or weADAPT) from datasets used by the study. `retrieved_at` records when the source was indexed, and `extraction_method` records how the JSON entry was produced.

The top-level `url` intentionally duplicates `provenance.document_url` for compatibility with the current application.

## Minimal example

```json
{
  "schema_version": "2.0",
  "id": "example-flood-study",
  "url": "https://example.org/study",
  "title": "Example flood study",
  "summary": "A district used flood and population data to prioritize shelters.",
  "location_scope": "adm2",
  "locations": [
    {
      "level": "adm2",
      "place_name": null,
      "adm0": {
        "name": "Example Country",
        "iso3": "EXA",
        "ucode": "EXA_V1",
        "dcid": "country/EXA"
      },
      "adm1": {
        "name": "Example Province",
        "ucode": "EXA_0001_V1",
        "dcid": null
      },
      "adm2": {
        "name": "Example District",
        "ucode": "EXA_0001_0001_V1",
        "dcid": null
      }
    }
  ],
  "hazards": ["river_flood"],
  "data_sources": [
    {
      "name": "Flood extent raster",
      "url": null,
      "role": "hazard_input"
    }
  ],
  "provenance": {
    "collection_name": "Example collection",
    "collection_url": "https://example.org/",
    "publisher": "Example publisher",
    "document_url": "https://example.org/study",
    "publication_date": null,
    "retrieved_at": "2026-09-21",
    "extraction_method": "manual"
  },
  "sdgs": [],
  "indicators_measured": [],
  "indicators_targeted": []
}
```

## Validation

Any JSON Schema Draft 2020-12 validator can validate the records. From the repository root, one option is:

```bash
check-jsonschema --schemafile schema/case-study.schema.json case_studies/*.json
```

In addition to schema validation, reviewers should verify that every GeoRepo `ucode` exists in the boundary release used by the GCHD application and that no location is more specific than the source document supports.
