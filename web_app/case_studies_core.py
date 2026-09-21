"""Load case-study records and join their locations to GeoRepo boundaries."""

import json
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import unary_union

from georepo_core import get_feature_by_ucode


CASE_STUDIES_DIR = Path(__file__).resolve().parents[1] / "case_studies"


def _deepest_unit(location):
    for level in ("adm2", "adm1", "adm0"):
        unit = location.get(level)
        if unit and unit.get("ucode"):
            return level, unit
    return None, None


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
        _level, unit = _deepest_unit(location)
        if not unit or unit["ucode"] in seen_ucodes:
            continue
        seen_ucodes.add(unit["ucode"])
        feature = feature_lookup(unit["ucode"])
        if feature:
            features.append(feature)

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
    return {
        **record,
        "countries": sorted(countries.values(), key=lambda item: item["name"]),
        "admin_regions": sorted(admin_regions.values(), key=lambda item: item["name"]),
        "location_labels": location_labels,
        "map_point": point,
        "map_bounds": bounds,
    }


def load_case_studies(directory=CASE_STUDIES_DIR, feature_lookup=get_feature_by_ucode):
    records = []
    for path in sorted(Path(directory).glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            records.append(enrich_case_study(json.load(handle), feature_lookup))
    return records
