"""Local access to the preprocessed UNICEF GeoRepo boundary cache."""

import json
import os
import sqlite3
import zlib
from functools import lru_cache

from shapely.geometry import Point, shape


DB_PATH = os.environ.get(
    "GCHD_GEOREPO_DB",
    os.path.join(os.path.dirname(__file__), "data", "georepo", "boundaries.sqlite"),
)
ATTRIBUTION = "Administrative boundaries: UNICEF GeoRepo (CC BY 4.0)"


def _connect():
    if not os.path.exists(DB_PATH):
        raise RuntimeError(
            "GeoRepo boundary cache is missing. Run scripts/build_georepo_cache.py first."
        )
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _geometry(blob):
    return json.loads(zlib.decompress(blob).decode("utf-8"))


def _feature(row):
    return {
        "type": "Feature",
        "geometry": _geometry(row["geometry"]),
        "properties": {
            "ucode": row["ucode"],
            "name": row["name"],
            "adm0_ucode": row["adm0_ucode"],
            "adm1_ucode": row["adm1_ucode"],
        },
    }


@lru_cache(maxsize=1)
def get_country_names():
    with _connect() as connection:
        rows = connection.execute(
            "SELECT name FROM boundaries WHERE level = 0 ORDER BY name"
        ).fetchall()
    return [row["name"] for row in rows]


@lru_cache(maxsize=512)
def get_country_ucode(country_name):
    with _connect() as connection:
        row = connection.execute(
            "SELECT ucode FROM boundaries WHERE level = 0 AND name = ?",
            (country_name,),
        ).fetchone()
    if not row:
        raise KeyError(f"Country not found: {country_name}")
    return row["ucode"]


@lru_cache(maxsize=512)
def get_country_bounds(country_ucode):
    with _connect() as connection:
        row = connection.execute(
            "SELECT minx, miny, maxx, maxy FROM boundaries WHERE level = 0 AND ucode = ?",
            (country_ucode,),
        ).fetchone()
    if not row:
        raise KeyError(f"Country code not found: {country_ucode}")
    return [[row["miny"], row["minx"]], [row["maxy"], row["maxx"]]]


@lru_cache(maxsize=256)
def get_boundary_collection(level, country_ucode):
    with _connect() as connection:
        if level == 0:
            rows = connection.execute(
                "SELECT * FROM boundaries WHERE level = 0 AND ucode = ?",
                (country_ucode,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM boundaries WHERE level = ? AND adm0_ucode = ? ORDER BY name",
                (level, country_ucode),
            ).fetchall()
    return {"type": "FeatureCollection", "features": [_feature(row) for row in rows]}


@lru_cache(maxsize=1024)
def get_feature_by_ucode(feature_ucode, level=None, country_ucode=None):
    clauses = ["ucode = ?"]
    values = [feature_ucode]
    if level is not None:
        clauses.append("level = ?")
        values.append(level)
    if country_ucode:
        clauses.append("adm0_ucode = ?")
        values.append(country_ucode)
    query = "SELECT * FROM boundaries WHERE " + " AND ".join(clauses)
    with _connect() as connection:
        row = connection.execute(query, values).fetchone()
    if not row:
        return None
    feature = _feature(row)
    return {
        "ucode": row["ucode"],
        "name": row["name"],
        "bounds": [[row["miny"], row["minx"]], [row["maxy"], row["maxx"]]],
        "feature": feature,
    }


def get_feature_at_point(lon, lat, level, country_ucode):
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM boundaries
            WHERE level = ? AND adm0_ucode = ?
              AND minx <= ? AND maxx >= ? AND miny <= ? AND maxy >= ?
            ORDER BY area ASC
            """,
            (level, country_ucode, lon, lon, lat, lat),
        ).fetchall()
    point = Point(lon, lat)
    for row in rows:
        if shape(_geometry(row["geometry"])).covers(point):
            return row["ucode"], row["name"]
    return None, None


def get_feature_geojson(feature_ucode):
    result = get_feature_by_ucode(feature_ucode)
    return result["feature"] if result else None
