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
    HAZARD_VIS_PALETTES, SELF_MASK_HAZARDS, GLOBAL_GEOMETRY,
    ADMIN_DATA, CHILD_AGE_BANDS, CHILD_PARTIAL_BAND, CHILD_PARTIAL_FRACTION,
)
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


def _hazard_image(hazard):
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
    reducer = hazard.get("reducer", "max")
    if reducer == "min":
        image = collection.min()
    elif reducer == "mean":
        image = collection.mean()
    elif reducer == "sum":
        image = collection.sum()
    elif reducer == "count_mask":
        image = collection.map(lambda item: item.gt(0)).sum()
    else:
        image = collection.max()
    return image.multiply(hazard.get("scale_factor", 1)).rename(hazard["name"])


# ---------------------------------------------------------------------------
# Core GEE objects — built once at startup
# ---------------------------------------------------------------------------

def _child_population_by_sex(population, prefix):
    """Add up the WorldPop age bands that fall under 18, for one sex.

    The 15-19 band straddles the cutoff, so it is counted at CHILD_PARTIAL_FRACTION
    and the younger bands are counted whole.
    """
    whole = population.select(
        [f"{prefix}_{band}" for band in CHILD_AGE_BANDS]
    ).reduce(ee.Reducer.sum())
    partial = population.select(f"{prefix}_{CHILD_PARTIAL_BAND}").multiply(
        CHILD_PARTIAL_FRACTION
    )
    return whole.add(partial)


@lru_cache(maxsize=1)
def build_core_images():
    population_collection = (
        ee.ImageCollection("WorldPop/GP/100m/pop_age_sex_cons_unadj")
        .filter(ee.Filter.eq("year", 2020))
    )
    population = population_collection.mosaic()
    childpop_m = _child_population_by_sex(population, "M").rename("population_m")
    childpop_f = _child_population_by_sex(population, "F").rename("population_f")
    childpop = childpop_m.add(childpop_f).rename("population")

    pop_target_res = population_collection.first().select("population").projection().nominalScale()
    target_crs = population_collection.first().select("population").projection()
    target_scale = pop_target_res

    country_boundaries = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level0")
    country_boundaries_reproj = country_boundaries.map(lambda f: f.transform(target_crs))
    global_geom = ee.Geometry.Polygon([GLOBAL_GEOMETRY], None, False)

    def summarize_population(hazard):
        layer = _hazard_image(hazard)
        threshold = hazard["threshold"]
        direction = hazard.get("direction", "gt")
        if direction == "lt":
            mask = layer.lt(threshold)
        elif direction == "lte":
            mask = layer.lte(threshold)
        elif direction == "gte":
            mask = layer.gte(threshold)
        else:
            mask = layer.gt(threshold)
        return childpop.updateMask(mask).rename(hazard["name"])

    exposure_by_hazard = {
        h["name"]: summarize_population(h)
        for h in HAZARDS if h.get("threshold") is not None
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
    hazard_score = topic_count_image.toFloat()

    return {
        "childpop":                  childpop,
        "childpop_m":                childpop_m,
        "childpop_f":                childpop_f,
        "pop_target_res":            pop_target_res,
        "target_crs":                target_crs,
        "target_scale":              target_scale,
        "country_boundaries_reproj": country_boundaries_reproj,
        "global_geom":               global_geom,
        "exposure_by_hazard":        exposure_by_hazard,
        "topic_masks":               topic_masks,
        "topic_coverage":            topic_coverage,
        "topic_count_image":         topic_count_image,
        "hazard_score":              hazard_score,
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

@lru_cache(maxsize=64)
def get_topic_tile_url(topic_name, color):
    core = build_core_images()
    vis  = {"palette": [color], "min": 0, "max": 1}
    mid  = core["topic_masks"][topic_name].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=1)
def get_topic_count_tile_url():
    core = build_core_images()
    n    = len(HAZARD_TOPICS)
    vis  = {"min": 0, "max": n, "palette": ["#ffffd4", "#fed98e", "#fe9929", "#d95f0e", "#993404"]}
    mid  = core["topic_count_image"].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=1)
def get_pixel_score_tile_url():
    core = build_core_images()
    vis = {"min": 1, "max": len(HAZARD_TOPICS), "palette": ["#ffffd4", "#fe9929", "#993404"]}
    mid = core["topic_count_image"].getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=8)
def get_pixel_score_percentile_tile_url(percentile):
    core         = build_core_images()
    hazard_score = core["hazard_score"]
    land_mask_base = core["country_boundaries_reproj"]
    target_crs   = core["target_crs"]
    target_scale = core["target_scale"]
    global_geom  = core["global_geom"]

    land_mask = (
        ee.Image(1).clip(land_mask_base).unmask(0)
        .reproject(crs=target_crs, scale=target_scale)
    )
    threshold = (
        hazard_score.updateMask(land_mask)
        .reduceRegion(
            reducer=ee.Reducer.percentile([int(percentile)]),
            geometry=global_geom,
            scale=hazard_score.projection().nominalScale(),
            bestEffort=True,
        ).values().get(0)
    )
    masked = hazard_score.updateMask(hazard_score.gt(ee.Number(threshold)))
    vis = {"min": 0, "max": 10, "palette": ["#000004", "#3b0f70", "#8c2981", "#de4968", "#fe9f6d"]}
    mid = masked.getMapId(vis)
    return mid["tile_fetcher"].url_format, vis


@lru_cache(maxsize=64)
def get_hazard_tile_url(hazard_name):
    hazard = HAZARD_MAP.get(hazard_name)
    if not hazard:
        return None, None

    image = _hazard_image(hazard)
    palette = HAZARD_VIS_PALETTES.get(hazard_name, ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"])
    vis = {
        "min": hazard.get("vis_min", 0),
        "max": hazard.get("vis_max", 1),
        "palette": palette,
    }
    if hazard.get("reducer") == "count_mask" or hazard.get("kind") == "population":
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

def compute_exposure(feature_ucode, admin_level, mhc_value=None, mhi_percentile=None):
    core        = build_core_images()
    childpop    = core["childpop"]
    childpop_m  = core["childpop_m"]
    childpop_f  = core["childpop_f"]
    pop_res     = core["pop_target_res"]
    topic_masks = core["topic_masks"]
    topic_cov   = core["topic_coverage"]
    exposure_by = core["exposure_by_hazard"]
    topic_count = core["topic_count_image"]
    hazard_score= core["hazard_score"]
    global_geom = core["global_geom"]
    land_mask_base = core["country_boundaries_reproj"]
    target_crs  = core["target_crs"]
    target_scale= core["target_scale"]

    bands = []
    for topic_name in HAZARD_TOPICS:
        bands.append(childpop.updateMask(topic_masks[topic_name]).rename(topic_name))
        bands.append(topic_cov[topic_name])

    for topic_name, hazard_names in HAZARD_TOPICS.items():
        if len(hazard_names) > 1:
            for h_name in hazard_names:
                bands.append(exposure_by[h_name].rename(h_name))

    combined = (
        ee.Image.cat(bands)
        .addBands(childpop.rename("total_population"))
        .addBands(childpop_m.rename("total_population_male"))
        .addBands(childpop_f.rename("total_population_female"))
    )

    if mhc_value:
        count_mask = topic_count.gte(ee.Number.parse(str(mhc_value)))
        combined = combined.addBands(childpop.updateMask(count_mask).rename("active_count_filter"))

    if mhi_percentile:
        land_mask = (
            ee.Image(1).clip(land_mask_base).unmask(0)
            .reproject(crs=target_crs, scale=target_scale)
        )
        mhi_threshold = (
            hazard_score.updateMask(land_mask)
            .reduceRegion(
                reducer=ee.Reducer.percentile([int(mhi_percentile)]),
                geometry=global_geom,
                scale=hazard_score.projection().nominalScale(),
                bestEffort=True,
            ).values().get(0)
        )
        intensity_mask = hazard_score.gt(ee.Number(mhi_threshold))
        combined = combined.addBands(childpop.updateMask(intensity_mask).rename("active_intensity_filter"))

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


def compute_topic_overlap(feature_ucode, admin_level, topic_names):
    """Children exposed to ALL of the listed hazard topics simultaneously (intersection)."""
    core        = build_core_images()
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


def compute_exposure_asset(asset_id):
    """Run per-hazard exposure for a GEE FeatureCollection asset.
    Returns list of property dicts (geometries stripped).
    """
    core        = build_core_images()
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


def compute_exposure_custom(geojson_dict):
    """Run per-hazard exposure for every feature in a GeoJSON FeatureCollection.
    Returns list of property dicts (geometries stripped to reduce payload size).
    """
    core        = build_core_images()
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
