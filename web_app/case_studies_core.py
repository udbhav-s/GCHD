"""Load case-study records and join their locations to GeoRepo boundaries."""

import json
from functools import lru_cache
from pathlib import Path

from shapely.geometry import Point, shape
from shapely.ops import unary_union
from shapely.prepared import prep

from georepo_core import get_feature_by_ucode


CASE_STUDIES_DIR = Path(__file__).resolve().parents[1] / "case_studies"


def _units_deepest_first(location):
    """Yield the location's administrative units, most specific first."""
    for level in ("adm2", "adm1", "adm0"):
        unit = location.get(level)
        if unit and unit.get("ucode"):
            yield level, unit


def _deepest_unit(location):
    return next(_units_deepest_first(location), (None, None))


def _combined_bounds(features):
    if not features:
        return None
    min_lat = min(feature["bounds"][0][0] for feature in features)
    min_lon = min(feature["bounds"][0][1] for feature in features)
    max_lat = max(feature["bounds"][1][0] for feature in features)
    max_lon = max(feature["bounds"][1][1] for feature in features)
    return [[min_lat, min_lon], [max_lat, max_lon]]


def _map_geometry(locations, feature_lookup):
    features = []
    seen_ucodes = set()
    for location in locations:
        # Fall back to a wider unit when the boundary cache has no feature for the
        # narrow one. A study with an unresolved district still maps to its country.
        for _level, unit in _units_deepest_first(location):
            if unit["ucode"] in seen_ucodes:
                break
            feature = feature_lookup(unit["ucode"])
            if feature:
                seen_ucodes.add(unit["ucode"])
                features.append(feature)
                break

    if not features:
        return None, None

    geometries = [shape(feature["feature"]["geometry"]) for feature in features]
    geometry = unary_union(geometries)
    point = geometry.representative_point() if len(geometries) == 1 else geometry.centroid
    return [point.y, point.x], _combined_bounds(features)


def enrich_case_study(record, feature_lookup=get_feature_by_ucode):
    """Add display/filter metadata and a map position without mutating the record."""
    locations = record.get("locations", [])
    countries = {}
    admin_regions = {}
    location_labels = []

    for location in locations:
        adm0 = location.get("adm0")
        if adm0:
            countries[adm0["ucode"]] = {"name": adm0["name"], "ucode": adm0["ucode"]}

        deepest_level, deepest = _deepest_unit(location)
        if deepest and deepest_level != "adm0":
            admin_regions[deepest["ucode"]] = {
                "name": deepest["name"],
                "ucode": deepest["ucode"],
                "level": deepest_level,
            }

        place_name = location.get("place_name")
        label = place_name or (deepest or {}).get("name")
        if label and label not in location_labels:
            location_labels.append(label)

    if not location_labels and record.get("location_scope") == "global":
        location_labels.append("Global")

    point, bounds = _map_geometry(locations, feature_lookup)

    # A coordinate from the source beats a centroid worked out from a boundary.
    # Falling back to a country centroid would put a city study hundreds of
    # kilometres away, outside every region it actually belongs to.
    record_point = record.get("point")
    if record_point:
        point = [record_point["lat"], record_point["lon"]]

    return {
        **record,
        "countries": sorted(countries.values(), key=lambda item: item["name"]),
        "admin_regions": sorted(admin_regions.values(), key=lambda item: item["name"]),
        "location_labels": location_labels,
        "map_point": point,
        "map_bounds": bounds,
    }


@lru_cache(maxsize=64)
def _prepared_region(region_ucode):
    """Fetch a boundary once and keep it ready for repeated point tests."""
    feature = get_feature_by_ucode(region_ucode)
    if not feature:
        return None
    geometry = shape(feature["feature"]["geometry"])
    return prep(geometry)


def studies_in_region(studies, region_ucode):
    """Keep the studies that sit inside the given boundary.

    A study matches if it names the region in its own location path, or if its
    mapped point falls inside the boundary. The point test is what lets a study
    whose narrower unit never resolved still show up for the right region.
    """
    if not region_ucode:
        return list(studies)

    region = _prepared_region(region_ucode)
    matches = []
    for study in studies:
        named = any(
            unit and unit.get("ucode") == region_ucode
            for location in study.get("locations", [])
            for unit in (location.get("adm0"), location.get("adm1"), location.get("adm2"))
        )
        if named:
            matches.append(study)
            continue
        point = study.get("map_point")
        if region and point and region.contains(Point(point[1], point[0])):
            matches.append(study)
    return matches


def load_case_studies(directory=CASE_STUDIES_DIR, feature_lookup=get_feature_by_ucode):
    records = []
    for path in sorted(Path(directory).glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            records.append(enrich_case_study(json.load(handle), feature_lookup))
    return records
