# Plan — from hazard screening to a child risk workbench

2026-09-21. Repo `~/Projects/GCHD`, branch `case-studies-viewer`, origin is the
udbhav-s fork. Nothing here is built yet. Edit freely.

## What the app actually is today

Verified in the code, not from the README:

- Three hazard topics only, all single-year 2024 statistics (`config.py:6-57`):
  ERA5-Land max temperature above 35 °C, TerraClimate PDSI below -2, and at
  least one FIRMS fire detection day.
- Under-18 population from WorldPop 2020 age/sex bands, with 15-19 counted at a
  fraction (`gee_core.py:73-85`, `:88-97`).
- 638 case studies as a discovery layer, joined to boundaries by ucode.
- No tests. No `test_*.py`, no conftest, no pytest config anywhere in the repo.

**The MHI is the hazard count.** `gee_core.py:149` sets
`hazard_score = topic_count_image.toFloat()`. With three topics that variable
only takes the values 0, 1, 2, 3. So:

- The percentile selector (P75/P80/P85/P90/P95, `config.py:150`) thresholds a
  three-valued integer. Several of those options resolve to the same threshold
  and draw identical maps.
- MHC uses `topic_count.gte(n)` (`gee_core.py:317`) and MHI uses
  `hazard_score.gt(p)` (`:334`) on the same image. Two controls, one variable.
- The palette is stretched over `{min: 0, max: 10}` (`:239`) against data that
  maxes at 3, so only the dark end of the ramp ever appears.
- The panel text at `app.py:395-399` describes a PCA across 13 layers. The web
  app does not build one. That score does exist in this repository, at
  `multi_hazard_indicators/mhi/mhi_construction.ipynb`, computed from rasters
  this public build cannot reach.

So the app was not showing an invented metric. It was showing a placeholder
under the name and the description of a real product it had no access to, which
is harder to catch: the description checked out against something, just not
against what was on screen.

A policymaker reading "Multi-Hazard Intensity, P90" gets a severity claim the
data cannot support.

## The framing

[UNDRR](https://www.undrr.org/terminology/disaster-risk) and
[INFORM](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Methodology):
risk is hazard × exposure × vulnerability, moderated by coping capacity. The app
has hazard and exposure. Vulnerability, coping capacity, likelihood, future
scenarios, and uncertainty are all absent.

Until Stage 1 lands, the honest label for this tool is **hazard and exposure
screening**, not risk assessment. That wording should appear in the UI, not only
in the docs.

UNICEF's own CCRR is the closest sibling and its Python pipeline is open. Take
its methodology rather than inventing one. INFORM subnational is worth borrowing
as a framework; do not expect to get its data.

**One thing the CCRR docs change about this plan.** CCRR is built from two
pillars — hazard exposure, and child vulnerability — and its hazard pillar is
sourced from GCHD. This repo is CCRR's upstream. So GCHD should not grow a
competing vulnerability score; it should expose vulnerability and capacity as
separate, documented inputs that a brief can read, and leave the composite to
CCRR. Worth noting too that CCRR folds coping capacity into its vulnerability
pillar (17 indicators across health, nutrition, WASH, education, protection,
poverty, survival, averaged arithmetically), while INFORM keeps the two apart.
That is a decision to make deliberately, not to inherit by accident. Its hazard
pillar combines groups by geometric mean, so strong exposure to any one hazard
lifts the score — the opposite of the flattening our current count does.

---

## Stage 0 — make it defensible

**Done 2026-09-21, uncommitted.** All six items below landed; 40 tests pass and
9 more run under `-m slow`. Two things turned up on the way and are recorded at
the end of this section.

No new layers until this is done.

**1. Relabel the MHI as what it is.** One control, not two: "number of hazard
topics present (1-3)".

| Change | Where |
|---|---|
| Drop `MHI_OPTIONS` | `config.py:150` |
| Delete the percentile tile helper | `gee_core.py:216-241` |
| Drop the `hazard_score` alias, use `topic_count_image` | `gee_core.py:149`, `:164` |
| Replace the `active_intensity_filter` band with a count threshold — approved 2026-09-21 | `gee_core.py:320-335` |
| Fix the vis range to 0-3 | `gee_core.py:239`, `app.py:343` |
| Rewrite the control and its explanation | `app.py:368-399` |
| Fix the export key and legend row | `app.py:1826`, `:1834` |

**2. Rewrite the README as one document.** Decided 2026-09-21: rewrite, do not
split. The de facto split is what caused the problem — the fork preamble
(`README.md:5-20`) and the inherited upstream text below it both describe
something called GCHD, so a reader takes the aspirational half as current.
Formalising that into two sections preserves the failure and adds a heading.
The fork is home and is not merging upstream, so there is no reason to keep
upstream prose intact.

New structure: what this fork runs, how to run it, then one short clearly marked
section on what the full UNICEF GCHD programme covers, linking to
`unicef/GCHD`.

Conflicts to clear: the 2025 under-18 baseline (`:108`) against WorldPop 2020;
the PCA-derived 0-10 MHI (`:118-126`); the resolution claim (`:102-105`). Delete
the eleven-row source table (`:140-152`) rather than correct it — it is accurate
about the programme and wrong about this code, which is the worst combination.

**3. Per-layer provenance.** `HAZARD_INFO` (`config.py:154`) already carries
description, units, availability, source, and source URL for the three live
layers — plus stale entries for eight hazards with no implementation behind
them. Add `native_resolution`, `temporal_basis`, `coverage`, `known_gaps`, and
the threshold stated in words. Surface all of it in the layer panel and in
exports. Delete the eight orphan entries or mark them plainly as not implemented.

**4. Say that the thresholds are single-year occurrence flags.** 35 °C maximum,
PDSI below -2, one or more detection days — each is a 2024 value, not a return
level, and each is binary. The UI implies otherwise by borrowing the CCRR
vocabulary.

Measured in Earth Engine on 2026-09-21: **33% of global land** satisfies "at
least one day above 35 °C in 2024". Among the pixels it flags, days above 35 °C
run p10 = 2, median = 57, p90 = 178, max = 343. A place with two hot days and a
place hot for most of the year are the same pixel, and contribute children to the
same exposure total. This is the MHI's flattening repeated one level down. P0
only labels it; P1 fixes it.

**5. Tests.** First suite, in rough order of value:

- Child-band arithmetic: the whole-band sum plus the partial 15-19 band
  (`gee_core.py:73-85`). Pull the arithmetic into a pure function so it can be
  tested without Earth Engine.
- Admin aggregation: ADM2 sums do not exceed their parent ADM1 for a sample
  country; the cache holds 289 / 3,578 / 41,092; ucode lookup round-trips.
- Taxonomy: every hazard id in the case studies exists in
  `hazard_taxonomy.json`; the fifteen deliberately empty `hazards` arrays stay
  empty, as a regression guard.
- Schema: wire the existing 2.2 validator into pytest so all 638 records are
  checked on every run. Note `jsonschema` lives in `scripts/requirements.txt`,
  not the web app's.
- One golden-value exposure test for a single district, tolerance-based, marked
  slow because it needs network and credentials.

### What Stage 0 turned up

**Two controls became one, not two-with-a-new-input.** The approved fix was to
give the intensity filter a count threshold. Once the percentile was gone, that
band was the count band the MHC control already produced, so keeping both would
have left two identical controls. The tab now carries one, and
`active_intensity_filter` is gone rather than rewritten.

**217 case studies carry no hazard, not 15.** The earlier handover counted only
the Climate-ADAPT records. Of 638, 217 have an empty `hazards` array and cannot
be reached by any hazard filter. 15 of those are the Climate-ADAPT ones, which
keep their `source_hazard_tags` so the decision stays visible. The other 202 are
mostly C40 records about waste, transport and energy efficiency that name no
hazard because they address none. Both counts are pinned in the tests. Whether
the discovery layer should surface the other third some other way is a product
question, not a bug.

**Four tests failed first and all four were my premises, not the code.** Worth
recording because two of them nearly became false bug reports: district bounding
boxes sit up to 0.022° outside their country's box because the ADM0 outline is
simplified more heavily than the ADM2 one, and the hazard taxonomy legitimately
lists layers this fork does not run. The tests now assert the weaker, true
invariants — a district cannot be degrees outside its country, and every live
layer must appear somewhere in the taxonomy.

---

## Stage 1 — vulnerability and coping capacity

Availability probed today against this repo's service account. Verified means I
loaded the asset and read its bands.

| Layer | Asset | Status |
|---|---|---|
| Travel time to healthcare, 2019, ~1 km | `projects/malariaatlasproject/assets/accessibility/accessibility_to_healthcare/2019` | Verified. Band `accessibility`, minutes. The old `Oxford/MAP/...` id still resolves, carries a walking-only band too, and is deprecated |
| Friction surface, 2019 | `projects/malariaatlasproject/assets/accessibility/friction_surface/2019_v5_1` | Verified via the deprecated alias. Needed only if we compute catchments ourselves |
| WorldPop age/sex, 100 m | already wired | In use |
| Settlement, built surface, population grids | `JRC/GHSL/P2023A/GHS_SMOD_V2-0`, `GHS_BUILT_S`, `GHS_POP` | Verified. Urban/rural split and a housing proxy |
| Nighttime lights, annual | `NOAA/VIIRS/DNB/ANNUAL_V22` | Verified. Electrification **proxy** only |
| Basic demographics | `CIESIN/GPWv411/GPW_Basic_Demographic_Characteristics` | Verified |
| GRDI v1, SEDAC, 1 km | — | **Not reachable in Earth Engine.** Seven plausible catalog paths all fail, and the `sat-io` folder is not listable by our service account. Needs a SEDAC download and an asset ingest, or local raster processing. Budget it as its own task |
| healthsites.io facilities | — | Not an Earth Engine dataset. API or country downloads, ingested as a FeatureCollection |
| Admin-1 tables: World Bank poverty atlas, GDL SHDI, OPHI MPI child breakdowns | — | Not Earth Engine. Join by admin code — but none of them use GeoRepo ucodes, so a crosswalk is required |

**Resolution floor, stated honestly: 1 km grid or ADM1.** Sub-national
vulnerability at ADM2 exists only as modelled DHS estimates in survey countries.
Do not draw ADM2 vulnerability as if it were measured.

**Before either of those, fix the hazard layers themselves.** Count days above
the threshold instead of flagging any occurrence. The machinery already exists —
`config.py`'s `count_mask` reducer does this for FIRMS, so heat and drought only
need the same treatment (`era.map(lambda i: i.gt(threshold)).sum()`). That alone
restores the severity range the measurement above shows we are throwing away.

Then extend it across years: how many years in ten exceed the threshold. That is
the empirical-probability statement the return-period vocabulary already promises
and does not deliver, and it is what makes the Observed half of the Stage 2
toggle worth showing. Precompute to an Earth Engine asset rather than computing
live — a 30-year daily global reduction is not an on-request operation.

**Then ship the smallest defensible pair:**

- Vulnerability — under-5 share of the child population, from the WorldPop bands
  already loaded. Real signal, no new dependency, 100 m.
- Coping capacity — travel time to healthcare, MAP 2019.

Keep them as separate constructs in the UI. No composite until its formula and
components are on screen.

**The heat-and-access screen.** Heat exposure × child population within X
minutes of a facility, with capacity proxied by admin-level beds per capita and
labelled a proxy. Not a facility-by-facility overburden forecast — no global
facility-level beds or staffing data exists. X as chips (30 / 60 / 120 min), per
the control rule below. The travel-time surface is already precomputed, so the
work here is the catchment aggregation and the honest labelling, not the routing.

---

## Stage 2 — time, as discrete states

**Ship one toggle first: Observed (ERA5-Land) against Mid-century (CMIP6
SSP2-4.5).** One control, two worlds, no multi-dimensional overwhelm. Both ends
are available now: the ERA5-Land daily collection already wired runs 1950 to
present, and `NASA/GDDP-CMIP6` carries `tasmax` at 25 km with historical, ssp245
and ssp585 across 34 models, ssp245 starting 2015.

Only after that lands, and only if it earns its keep:

- Mode chips — Baseline / Trend / 2050. The map never shows more than one thing.
- Return period as chips, not a slider.
- Trend as a delta view, not two absolute maps side by side.
- A sparkline per region in the side panel, so trend never touches the map.
- Season as a compact month strip under the layer name.

The map stays single-variable; controls swap what it shows.

Two caveats to honour rather than design around. Return-period chips are
dishonest until layers exist that actually carry return periods — the current
three do not. And for 2050, the inter-model range is the uncertainty story;
showing one model's number alone would repeat the MHI mistake in a new place.

---

## Stage 3 — the Region Risk Brief

Pick a district, get one to two pages, exportable as PDF plus CSV:

- Region, admin level, total and child population, and a "data as of" per input
- Ranked hazards, with exposed child counts and shares
- Vulnerability drivers as components, never rolled into one number
- Coping capacity, kept separate from vulnerability
- Uncertainty: what is missing, what is modelled, what is a proxy
- Trend or scenario, if Stage 2 landed
- Matched case studies from the 638-record library, by hazard and geography —
  the join already exists in `case_studies_core.py`

Then compare mode for two to five districts with an absolute-counts versus rates
toggle, and a prioritization matrix with visible, editable weights.

## Rules that apply throughout

- Any composite shows its formula and its components.
- "Not available" is never drawn as zero.
- Missing data is hatched, not blank.
- Every layer carries data-as-of, resolution, source, coverage, and known gaps.
- Proxies are labelled as proxies in the interface, not only in the docs.

## Decisions I need from you

1. README — split into fork and upstream sections, or one rewritten honest page?
2. GRDI — worth the SEDAC download and Earth Engine ingest, or start with the
   WorldPop under-5 share alone?
3. The ucode crosswalk for GDL and OPHI admin-1 tables — build it, or stay
   raster-only for now?
4. Still open from the last handover and untouched by this plan: the 37 NUTS-1
   regions with no ucode, and DCID enrichment for 630 scraped records.

## What I have not verified

- GRDI's licence and exact resolution. The SEDAC metadata page refused the
  connection when I tried to read it. All I established first-hand is that GRDI
  is not reachable in Earth Engine from this service account.
- `exposure_analysis/`. Separate pipeline, own boundary inputs, unread. It may
  duplicate or contradict anything above.
- The CCRR Python pipeline itself. I read its documentation site, not its code.
- The 2025 JAMA Network Open and Lancet Respiratory Medicine papers, and Weiss
  et al. 2020. Second-hand here.

## Sources

- INFORM risk methodology — https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Methodology
- UNDRR, disaster risk terminology — https://www.undrr.org/terminology/disaster-risk
- UNICEF CCRR methodology and pipeline — https://unicef.github.io/CCRR/
- GRDI v1, SEDAC — https://sedac.ciesin.columbia.edu/downloads/metadata/povmap-grdi-v1.html
- Weiss et al. 2020, global travel time to healthcare, *Nature Medicine* — https://www.nature.com/articles/s41591-020-1059-1
- JAMA Network Open 2025, heat and health-system load — https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2823543
