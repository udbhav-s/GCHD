# =============================================================================
# gee_core.py — GEE logic with no Streamlit dependency
# Caches with functools.lru_cache (module-level, server lifetime).
# =============================================================================

import re
import json
import os
from functools import lru_cache
import ee

from config import (
    HAZARDS, HAZARD_MAP, HAZARD_TOPICS, ALLOW_NEGATIVE,
    HAZARD_VIS_PALETTES, SELF_MASK_HAZARDS,
    ADMIN_DATA, VULNERABILITY_PALETTE, default_durations, clean_durations,
    clean_period, clean_frequency, baseline_window, baseline_years,
)
from exposure_math import child_band_weights, under_five_band_weights
from georepo_core import (
    get_country_names as get_local_country_names,
    get_country_ucode as get_local_country_ucode,
    get_country_bounds as get_local_country_bounds,
    get_feature_at_point as get_local_feature_at_point,
    get_feature_by_ucode as get_local_feature_by_ucode,
    get_feature_geojson,
)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def initialize_gee():
    key_path = os.path.join(os.path.dirname(__file__), "credentials", "service_account.json")
    with open(key_path) as f:
        info = json.load(f)
    credentials = ee.ServiceAccountCredentials(email=info["client_email"], key_file=key_path)
    project = os.environ.get("EARTH_ENGINE_PROJECT", info["project_id"])
    ee.Initialize(credentials=credentials, project=project)


def _step_exceeds(image, threshold, direction):
    """Whether one time step met the hazard's condition."""
    if direction == "lt":
        return image.lt(threshold)
    if direction == "lte":
        return image.lte(threshold)
    if direction == "gte":
        return image.gte(threshold)
    return image.gt(threshold)


def _hazard_image(hazard):
    """How many time steps met the condition, per pixel.

    The old version reduced the year to a single value and asked whether it
    crossed the threshold once. That made a place with two hot days identical
    to a place hot for most of the year. Counting the steps keeps the
    difference, and costs no more to compute: the comparison reduces each step
    to a boolean before the sum.
    """
    if hazard.get("kind") == "population":
        return (
            ee.ImageCollection(hazard["id"])
            .filter(ee.Filter.eq("year", hazard.get("year", 2020)))
            .mosaic()
            .select("population")
            .rename(hazard["name"])
        )

    collection = (
        ee.ImageCollection(hazard["id"])
        .filterDate(hazard["start"], hazard["end"])
        .select(hazard["band"])
    )
    return collection.map(_step_test(hazard)).sum().rename(hazard["name"])


def _step_test(hazard):
    scale_factor = hazard.get("scale_factor", 1)
    threshold = hazard["threshold"]
    direction = hazard.get("direction", "gt")

    def step(image):
        value = image.multiply(scale_factor) if scale_factor != 1 else image
        return _step_exceeds(value, threshold, direction)

    return step


def _qualifying_years_image(hazard, minimum_steps):
    """How many years in the baseline lasted at least `minimum_steps`.

    Each year is counted separately and the results added, so the answer is a
    number of years rather than a total of days. Earth Engine runs the years in
    parallel, which is why thirty of them cost about the same as one.
    """
    start_year, end_year = baseline_window(hazard)
    collection = ee.ImageCollection(hazard["id"]).select(hazard["band"])
    step = _step_test(hazard)

    def year(value):
        value = ee.Number(value)
        opens = ee.Date.fromYMD(value, 1, 1)
        window = collection.filterDate(opens, opens.advance(1, "year"))
        return window.map(step).sum().gte(minimum_steps)

    years = ee.List.sequence(start_year, end_year)
    return (
        ee.ImageCollection(years.map(year))
        .sum()
        .rename(hazard["name"])
    )


def _years_per_ten_image(hazard, minimum_steps):
    """The same count expressed per ten years, so windows of different lengths
    can sit beside each other."""
    scale = 10.0 / baseline_years(hazard)
    return _qualifying_years_image(hazard, minimum_steps).multiply(scale)


# ---------------------------------------------------------------------------
# Core GEE objects — built once at startup
# ---------------------------------------------------------------------------

def _weighted_bands(population, prefix, weights):
    total = None
    for band, weight in weights.items():
        term = population.select(f"{prefix}_{band}")
        if weight != 1.0:
            term = term.multiply(weight)
        total = term if total is None else total.add(term)
    return total


def _child_population_by_sex(population, prefix):
    """Add up the WorldPop age bands that fall under 18, for one sex.

    The weights come from exposure_math so the same arithmetic can be tested
    without Earth Engine.
    """
    return _weighted_bands(population, prefix, child_band_weights())


@lru_cache(maxsize=64)
def build_core_images(durations=None, period="observed", frequency=1):
    """Build the images the app draws and measures.

    `durations` maps a hazard name to the minimum number of time steps that
    must meet its condition before a pixel counts as exposed. It is a tuple of
    pairs rather than a dict so the result can be cached per choice.

    `period` picks what the figures describe. "observed" is 2024. "typical"
    asks how often a year like that occurred across the hazard's baseline, and
    `frequency` is how many such years per ten are needed to count.
    """
    durations = dict(durations) if durations else default_durations()
    period = clean_period(period)
    frequency = clean_frequency(frequency)

    population_collection = (
        ee.ImageCollection("WorldPop/GP/100m/pop_age_sex_cons_unadj")
        .filter(ee.Filter.eq("year", 2020))
    )
    population = population_collection.mosaic()
    childpop_m = _child_population_by_sex(population, "M").rename("population_m")
    childpop_f = _child_population_by_sex(population, "F").rename("population_f")
    childpop = childpop_m.add(childpop_f).rename("population")

    # Vulnerability, kept as its own quantity rather than folded into exposure.
    under_five = (
        _weighted_bands(population, "M", under_five_band_weights())
        .add(_weighted_bands(population, "F", under_five_band_weights()))
        .rename("under_five")
    )
    # Masked where no children live: a cell with none has no age structure, and
    # drawing it as 0% would place it beside genuinely older populations.
    under_five_share = (
        under_five.divide(childpop.selfMask()).multiply(100).rename("under_five_share")
    )

    pop_target_res = population_collection.first().select("population").projection().nominalScale()

    def exposed_area(hazard):
        """Where this hazard counts, under the current duration and period."""
        minimum = durations.get(hazard["name"], hazard.get("duration_default", 1))
        if period == "typical":
            # Exposed where a qualifying year turned up often enough, rather
            # than because it happened once in 2024.
            return _years_per_ten_image(hazard, minimum).gte(frequency)
        return _hazard_image(hazard).gte(minimum)

    hazard_masks = {
        h["name"]: exposed_area(h)
        for h in HAZARDS if h.get("threshold") is not None
    }
    exposure_by_hazard = {
        name: childpop.updateMask(mask).rename(name)
        for name, mask in hazard_masks.items()
    }
    under_five_by_hazard = {
        name: under_five.updateMask(mask).rename("u5_" + name)
        for name, mask in hazard_masks.items()
    }

    def build_topic_mask(topic_name):
        masks = [exposure_by_hazard[n].mask() for n in HAZARD_TOPICS[topic_name]]
        union = masks[0]
        for m in masks[1:]:
            union = union.Or(m)
        return ee.Image.constant(1).updateMask(union)

    topic_masks = {t: build_topic_mask(t) for t in HAZARD_TOPICS}
    stacked = ee.ImageCollection([topic_masks[t] for t in HAZARD_TOPICS]).toBands()
    topic_count_image = stacked.reduce(ee.Reducer.count()).rename("topic_count")

    def get_raw_mask(hazard):
        return _hazard_image(hazard).mask()

    def build_coverage_image(topic_name):
        coverages = [get_raw_mask(HAZARD_MAP[n]) for n in HAZARD_TOPICS[topic_name] if n in HAZARD_MAP]
        union = coverages[0]
        for c in coverages[1:]:
            union = union.Or(c)
        safe_key = re.sub(r"[^a-zA-Z0-9]", "_", topic_name)
        return ee.Image.constant(1).updateMask(union).rename(f"cov_{safe_key}")

    topic_coverage = {t: build_coverage_image(t) for t in HAZARD_TOPICS}

    return {
        "childpop":                  childpop,
        "childpop_m":                childpop_m,
        "childpop_f":                childpop_f,
        "pop_target_res":            pop_target_res,
        "exposure_by_hazard":        exposure_by_hazard,
        "topic_masks":               topic_masks,
        "topic_coverage":            topic_coverage,
        "topic_count_image":         topic_count_image,
        "under_five":                under_five,
        "under_five_share":          under_five_share,
        "under_five_by_hazard":      under_five_by_hazard,
    }


# ---------------------------------------------------------------------------
# Country helpers
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_country_names():
    return get_local_country_names()


@lru_cache(maxsize=512)
def get_country_ucode(country_name):
    return get_local_country_ucode(country_name)


@lru_cache(maxsize=512)
def get_country_bounds(country_ucode):
    return get_local_country_bounds(country_ucode)


# ---------------------------------------------------------------------------
# Tile URL helpers (cached 1 h — GEE tokens expire)
# ---------------------------------------------------------------------------

def durations_key(selected=None):
    """A hashable, validated form of a duration selection, for caching."""
    return tuple(sorted(clean_durations(selected).items()))


def view_key(durations=None, period="observed", frequency=1):
    """Everything that changes what the figures mean, in one cacheable value."""
    return durations_key(durations), clean_period(period), clean_frequency(frequency)


@lru_cache(maxsize=64)
def get_topic_tile_url(topic_name, color, durations=None, period="observed", frequency=1):
    core = build_core_images(durations, period, frequency)
    vis  = {"palette": [color], "min": 0, "max": 1}
    mid  = core["topic_masks"][topic_name].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=32)
def get_topic_count_tile_url(durations=None, period="observed", frequency=1):
    core = build_core_images(durations, period, frequency)
    n    = len(HAZARD_TOPICS)
    vis  = {"min": 0, "max": n, "palette": ["#ffffd4", "#fed98e", "#fe9929", "#d95f0e", "#993404"]}
    mid  = core["topic_count_image"].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=8)
def get_under_five_tile_url():
    """Share of children who are under five, as its own layer.

    Vulnerability is shown beside hazard and exposure, not multiplied into
    them. Any combined score would need a formula this app cannot yet defend.
    """
    core = build_core_images()
    vis = {"min": 0, "max": 25, "palette": VULNERABILITY_PALETTE}
    mid = core["under_five_share"].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=64)
def get_hazard_tile_url(hazard_name, durations=None, period="observed"):
    """Tile for one hazard layer, showing how long its condition held.

    The map shows the same quantity the exposure figures are built from. Drawing
    the year's peak temperature while counting children by days above a
    threshold would put two different measures on the same screen.
    """
    hazard = HAZARD_MAP.get(hazard_name)
    if not hazard:
        return None, None

    palette = HAZARD_VIS_PALETTES.get(hazard_name, ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"])
    if clean_period(period) == "typical" and hazard.get("duration_options"):
        minimum = dict(durations_key(dict(durations) if durations else None))[hazard_name]
        image = _years_per_ten_image(hazard, minimum)
        vis = {"min": 0, "max": 10, "palette": palette}
    else:
        image = _hazard_image(hazard)
        vis = {
            "min": hazard.get("vis_min", 0),
            "max": hazard.get("vis_max", 1),
            "palette": palette,
        }
    # Zero steps means the hazard never occurred, which should read as empty
    # rather than as the bottom of the colour ramp.
    if hazard.get("duration_options") or hazard.get("kind") == "population":
        image = image.selfMask()

    mid = image.getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


# ---------------------------------------------------------------------------
# Feature lookup by click
# ---------------------------------------------------------------------------

def get_feature_at_point(lon, lat, admin_level, country_ucode):
    level = ADMIN_DATA[admin_level]["level"]
    return get_local_feature_at_point(lon, lat, level, country_ucode)


@lru_cache(maxsize=512)
def get_feature_by_ucode(feature_ucode, admin_level, country_ucode=None):
    level = ADMIN_DATA[admin_level]["level"]
    return get_local_feature_by_ucode(feature_ucode, level, country_ucode)


# ---------------------------------------------------------------------------
# Exposure computation
# ---------------------------------------------------------------------------

def compute_exposure(feature_ucode, admin_level, mhc_value=None, durations=None,
                     period="observed", frequency=1):
    core        = build_core_images(durations, period, frequency)
    childpop    = core["childpop"]
    childpop_m  = core["childpop_m"]
    childpop_f  = core["childpop_f"]
    pop_res     = core["pop_target_res"]
    topic_masks = core["topic_masks"]
    topic_cov   = core["topic_coverage"]
    exposure_by = core["exposure_by_hazard"]
    topic_count = core["topic_count_image"]

    bands = []
    for topic_name in HAZARD_TOPICS:
        bands.append(childpop.updateMask(topic_masks[topic_name]).rename(topic_name))
        bands.append(topic_cov[topic_name])
        # Under-fives within the same area, so the age split can be reported
        # beside the total rather than inferred from it.
        bands.append(
            core["under_five"].updateMask(topic_masks[topic_name]).rename("u5_" + topic_name)
        )

    for topic_name, hazard_names in HAZARD_TOPICS.items():
        if len(hazard_names) > 1:
            for h_name in hazard_names:
                bands.append(exposure_by[h_name].rename(h_name))

    combined = (
        ee.Image.cat(bands)
        .addBands(childpop.rename("total_population"))
        .addBands(childpop_m.rename("total_population_male"))
        .addBands(childpop_f.rename("total_population_female"))
        .addBands(core["under_five"].rename("total_under_five"))
    )

    if mhc_value:
        count_mask = topic_count.gte(ee.Number.parse(str(mhc_value)))
        combined = combined.addBands(childpop.updateMask(count_mask).rename("active_count_filter"))

    feature = get_feature_geojson(feature_ucode)
    if not feature:
        return None
    stats = combined.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=ee.Geometry(feature["geometry"]),
        scale=pop_res,
        maxPixels=1e13,
        tileScale=4,
    )
    return stats.getInfo()


def compute_topic_overlap(feature_ucode, admin_level, topic_names, durations=None,
                          period="observed", frequency=1):
    """Children exposed to ALL of the listed hazard topics simultaneously (intersection)."""
    core        = build_core_images(durations, period, frequency)
    childpop    = core["childpop"]
    pop_res     = core["pop_target_res"]
    topic_masks = core["topic_masks"]

    combined_mask = topic_masks[topic_names[0]]
    for t in topic_names[1:]:
        combined_mask = combined_mask.And(topic_masks[t])

    combined = (
        childpop.updateMask(combined_mask).rename("overlap")
        .addBands(childpop.rename("total_population"))
    )
    feature = get_feature_geojson(feature_ucode)
    if not feature:
        return None
    stats = combined.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=ee.Geometry(feature["geometry"]),
        scale=pop_res,
        maxPixels=1e13,
        tileScale=4,
    )
    return stats.getInfo()


@lru_cache(maxsize=32)
def get_asset_info(asset_id):
    """Return (feature_count, [property_names]) for a GEE FeatureCollection asset."""
    fc    = ee.FeatureCollection(asset_id)
    n     = fc.size().getInfo()
    props = fc.first().propertyNames().getInfo()
    return n, props


@lru_cache(maxsize=32)
def get_asset_bounds(asset_id):
    """Return [[minlat, minlon], [maxlat, maxlon]] for a GEE FeatureCollection asset."""
    fc     = ee.FeatureCollection(asset_id)
    coords = fc.geometry().bounds(1).coordinates().getInfo()[0]
    lons   = [c[0] for c in coords]
    lats   = [c[1] for c in coords]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]


@lru_cache(maxsize=32)
def get_custom_asset_tile_url(asset_id):
    """Return tile URL for a styled GEE FeatureCollection asset."""
    fc     = ee.FeatureCollection(asset_id)
    styled = fc.style(color="e67e22", width=2, fillColor="e67e2208")
    mid    = styled.getMapId({})
    return mid["tile_fetcher"].url_format


def compute_exposure_asset(asset_id, durations=None):
    """Run per-hazard exposure for a GEE FeatureCollection asset.
    Returns list of property dicts (geometries stripped).
    """
    core        = build_core_images(durations)
    childpop    = core["childpop"]
    childpop_m  = core["childpop_m"]
    childpop_f  = core["childpop_f"]
    pop_res     = core["pop_target_res"]
    exposure_by = core["exposure_by_hazard"]

    hazard_names = [h["name"] for h in HAZARDS if h.get("threshold") is not None]
    bands = [exposure_by[n].rename(n) for n in hazard_names if n in exposure_by]
    combined = (
        ee.Image.cat(bands)
        .addBands(childpop.rename("total_population"))
        .addBands(childpop_m.rename("total_population_male"))
        .addBands(childpop_f.rename("total_population_female"))
    )
    fc      = ee.FeatureCollection(asset_id)
    results = combined.reduceRegions(
        collection=fc, reducer=ee.Reducer.sum(),
        scale=pop_res, tileScale=8,
    )
    props_only = results.map(lambda f: ee.Feature(None, f.toDictionary()))
    return props_only.getInfo()["features"]


def compute_exposure_custom(geojson_dict, durations=None):
    """Run per-hazard exposure for every feature in a GeoJSON FeatureCollection.
    Returns list of property dicts (geometries stripped to reduce payload size).
    """
    core        = build_core_images(durations)
    childpop    = core["childpop"]
    childpop_m  = core["childpop_m"]
    childpop_f  = core["childpop_f"]
    pop_res     = core["pop_target_res"]
    exposure_by = core["exposure_by_hazard"]

    hazard_names = [h["name"] for h in HAZARDS if h.get("threshold") is not None]

    bands = [exposure_by[n].rename(n) for n in hazard_names if n in exposure_by]
    combined = (
        ee.Image.cat(bands)
        .addBands(childpop.rename("total_population"))
        .addBands(childpop_m.rename("total_population_male"))
        .addBands(childpop_f.rename("total_population_female"))
    )

    fc      = ee.FeatureCollection(geojson_dict)
    results = combined.reduceRegions(
        collection=fc, reducer=ee.Reducer.sum(),
        scale=pop_res, tileScale=8,
    )
    # Strip geometries before getInfo() to keep payload small for large feature sets
    props_only = results.map(lambda f: ee.Feature(None, f.toDictionary()))
    return props_only.getInfo()["features"]
