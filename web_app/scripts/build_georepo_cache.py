#!/usr/bin/env python3
"""Build a compact SQLite boundary cache from GeoRepo line-delimited GeoJSON."""

import argparse
import json
import sqlite3
import zlib
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.validation import make_valid


TOLERANCE_BY_LEVEL = {0: 0.02, 1: 0.01, 2: 0.005}


def iter_features(path):
    with path.open("r", encoding="utf-8") as src:
        for line in src:
            value = line.strip().rstrip(",")
            if not value.startswith('{"type": "Feature"'):
                continue
            yield json.loads(value)


def prepare_database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        DROP TABLE IF EXISTS boundaries;
        CREATE TABLE boundaries (
            ucode TEXT PRIMARY KEY,
            level INTEGER NOT NULL,
            name TEXT NOT NULL,
            adm0_ucode TEXT NOT NULL,
            adm1_ucode TEXT,
            minx REAL NOT NULL,
            miny REAL NOT NULL,
            maxx REAL NOT NULL,
            maxy REAL NOT NULL,
            area REAL NOT NULL,
            geometry BLOB NOT NULL
        );
        CREATE INDEX boundaries_country_level
            ON boundaries(adm0_ucode, level);
        CREATE INDEX boundaries_bbox
            ON boundaries(level, adm0_ucode, minx, maxx, miny, maxy);
        """
    )
    return connection


def insert_level(connection, level, source):
    tolerance = TOLERANCE_BY_LEVEL[level]
    inserted = 0
    skipped = 0
    for feature in iter_features(source):
        properties = feature.get("properties") or {}
        if properties.get("is_latest") is not True:
            skipped += 1
            continue

        geometry = shape(feature["geometry"])
        if not geometry.is_valid:
            geometry = make_valid(geometry)
        geometry = geometry.simplify(tolerance, preserve_topology=True)
        if geometry.is_empty:
            skipped += 1
            continue

        ucode = properties["ucode"]
        adm0_ucode = properties.get("adm0_ucode") or ucode
        minx, miny, maxx, maxy = geometry.bounds
        geometry_bytes = zlib.compress(
            json.dumps(mapping(geometry), separators=(",", ":")).encode("utf-8"),
            level=6,
        )
        connection.execute(
            """
            INSERT OR REPLACE INTO boundaries
                (ucode, level, name, adm0_ucode, adm1_ucode,
                 minx, miny, maxx, maxy, area, geometry)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ucode,
                level,
                properties.get("name") or properties.get("name_en") or ucode,
                adm0_ucode,
                properties.get("adm1_ucode"),
                minx,
                miny,
                maxx,
                maxy,
                geometry.area,
                geometry_bytes,
            ),
        )
        inserted += 1
        if inserted % 1000 == 0:
            connection.commit()
            print(f"adm{level}: {inserted:,} current features", flush=True)
    connection.commit()
    print(
        f"adm{level}: complete ({inserted:,} current, {skipped:,} historical/invalid skipped)",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--adm0", type=Path, required=True)
    parser.add_argument("--adm1", type=Path, required=True)
    parser.add_argument("--adm2", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    connection = prepare_database(args.output)
    try:
        for level in range(3):
            insert_level(connection, level, getattr(args, f"adm{level}"))
        connection.execute("VACUUM")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
