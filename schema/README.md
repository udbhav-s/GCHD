# Case study schema

Mirror Worlds case studies use [`case-study.schema.json`](case-study.schema.json), a JSON Schema Draft 2020-12 document. Version `2.0` adds administrative coverage, Global Children's Hazard Database (GCHD) hazard tags, analytical data sources, and record provenance while retaining the existing SDG and UN Data Commons indicator fields.

Version `2.1` adds what bulk scraping of an external collection needs. Every addition is optional, so `2.0` records stay valid:

- `ucode` may be `null`, and an administrative unit may carry `source_code` and `source_name`. A source that names its regions instead of coding them can now be recorded without inventing a GeoRepo identifier.
- `source_hazard_tags` keeps the source's own hazard vocabulary, including tags with no GCHD equivalent.
- `point` holds a representative coordinate so a study can be mapped before any boundary is resolved.
- `provenance` gains `source_record_id`, `source_api_url`, `source_content_type`, `source_modified`, and `extracted_by`, which together let a re-run find the same record and tell whether it has changed since.

## Geographic coverage

`location_scope` records the most specific geography supported by the source: `global`, `adm0`, `adm1`, `adm2`, or `non_administrative`.

`locations` is an array of complete administrative paths. Each path contains `adm0`, `adm1`, and `adm2`; levels below the study's documented scope are `null`. A study covering several districts has one location object per district. Keeping the full hierarchy together avoids ambiguous parallel arrays.

Administrative units use UNICEF GeoRepo `ucode` values so the GCHD application can join a case study to its existing ADM0-ADM2 boundary cache. `dcid` is optional in practice and is `null` when UN Data Commons does not expose a matching geography. Do not copy boundary polygons into case-study files.

Some sources identify a region only by name. Those units carry `name`, `source_name`, and where available `source_code`, with `ucode` left `null`, and sit at the closest GCHD level. `scripts/resolve_ucodes.py` matches them against the boundary cache later and moves a unit between `adm1` and `adm2` when GeoRepo puts it at a different level than the source implied. Treat a null `ucode` as unresolved, not as absent coverage, and use `point` to place the study in the meantime.

For named places that are not administrative regions, such as a refugee camp or watershed, use `location_scope: "non_administrative"`, put the name in `place_name`, and include only the containing administrative units that can be verified.

Global studies have `location_scope: "global"` and an empty `locations` array.

## Hazards

`hazards` is an array of controlled GCHD hazard concepts. It is intentionally separate from `indicators_measured` and `indicators_targeted`:

- Hazard IDs select or filter GCHD physical hazard layers.
- Indicator DCIDs identify statistical measures and outcomes available through UN Data Commons.

The allowed hazard IDs are defined by the schema. An empty array is valid for legacy case studies that are useful historical twins but do not analyze a GCHD hazard.

GCHD's more specific raster codes—such as `river_flood_100yr`, `heatwave_frequency`, and `drought_spi_tc`—belong in a shared application-level hazard taxonomy rather than being repeated in every case-study record. That taxonomy is [`hazard-taxonomy.json`](hazard-taxonomy.json): it maps each hazard ID to its dashboard topic and its GCHD layer codes, and marks which layers the public web app actually serves.

A source collection usually has its own hazard vocabulary that does not line up with the GCHD one. Record it in `source_hazard_tags`, one entry per source tag, with `mapped_to` listing the GCHD hazard IDs it became. An empty `mapped_to` means the tag has no GCHD equivalent and the tag is kept only so the information is not lost. Filter and correlate on `hazards`; read `source_hazard_tags` when you need to know what the source actually said.

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
