# C40 case-study import

This import indexes the public [C40 Case Studies](https://www.c40.org/case-studies/) collection for the GCHD case-study viewer.

## Scope

The C40 WordPress API reported 635 unique case-study records when retrieved on 2026-09-21. Records were fetched in stable ID order to avoid duplicates across changing archive pages:

```text
https://www.c40.org/wp-json/wp/v2/case-study?per_page=100&page={page}&orderby=id&order=asc&_embed=wp:term
```

A study was included when at least one of these conditions was met:

1. Its source text explicitly concerned a hazard in the case-study schema.
2. It explicitly connected an intervention, service, or outcome to children or youth livelihoods.
3. Its tagged or clearly named city was classified as part of the Global South under the broad policy-research definition used for this import.

The conditions are combined with OR. The resulting import contains 479 studies: 281 hazard matches, 62 children/youth matches, and 320 Global South matches. These counts overlap.

## Files

- `manifest.json` lists every included C40 ID, source URL, inclusion criteria, city tags, controlled hazard tags, and a short audit reason.
- `city-mapping.json` maps C40 city labels to the UNICEF GeoRepo ADM0-ADM2 cache used by the app. Every city has a verified ADM0; more specific units are included only where they were confidently resolved.
- The schema records themselves are stored as `case_studies/c40-<slug>.json`.

## Conversion notes

- C40 is recorded as the collection and publisher in `provenance`.
- City initiatives use `location_scope: "non_administrative"` with their containing GeoRepo path. This keeps the named city while still enabling map joins and zooming.
- Hazard values use only the controlled schema vocabulary.
- SDGs are conservatively inferred from explicit subject vocabulary.
- UN Data Commons indicator arrays remain empty unless an indicator can be verified; the import does not invent DCIDs.
- Data sources are added only for explicit analytical inputs such as census, survey, monitoring, inventory, satellite, climate-model, population, or traffic data.
- Summaries combine a short index description with no more than 22 words from the source excerpt.

The import and its three conversion batches were validated against the case-study schema before being copied into the application dataset.
