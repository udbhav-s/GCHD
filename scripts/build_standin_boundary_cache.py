#!/usr/bin/env python3
"""Build a stand-in boundary cache so the web app can run without GeoRepo.

UNICEF GeoRepo has been retired and now answers 410 on every endpoint, so
web_app/scripts/build_georepo_cache.py has no source to read and the app cannot
start. This builds a cache with the same table shape from Natural Earth, which
is public domain, purely so the app is runnable for local review.

What is real and what is not:

  ADM0  Real GeoRepo ucodes, taken from the repository's own countries_info.csv
        and keyed by ISO3. Case studies that reference a country join correctly.
  ADM1  Real Natural Earth geometry, but the ucodes are invented and marked with
        a _V0 suffix. They are self-consistent inside this cache, so the admin
        level selector works, but they will NOT match the GeoRepo ADM1 ucodes
        recorded on case studies.
  ADM2  Not included. Natural Earth has no ADM2 layer.

Do not use this for analysis, and do not treat an ADM1 match here as a verified
GeoRepo identifier. Replace it with a real export if GeoRepo data resurfaces.

    python scripts/build_standin_boundary_cache.py
"""

import argparse
import json
import sys
import urllib.request
import zlib
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.validation import make_valid

sys.path.insert(0, str(Path(__file__).resolve().parent))
from climate_adapt_mapping import load_country_ucodes  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "web_app" / "data" / "georepo" / "boundaries.sqlite"
DEFAULT_CACHE = REPO_ROOT / ".cache" / "natural_earth"

NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
ADM0_FILE = "ne_50m_admin_0_countries.geojson"
ADM1_FILE = "ne_10m_admin_1_states_provinces.geojson"

TOLERANCE = {0: 0.02, 1: 0.01}

# Natural Earth codes a few territories differently from ISO 3166-1.
NE_TO_ISO3 = {"SDS": "SSD", "SAH": "ESH", "PSX": "PSE", "ALD": "ALA"}


def download(name, cache_dir):
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / name
    if target.exists():
        return target
    url = f"{NE_BASE}/{name}"
    print(f"downloading {name} ...", flush=True)
    with urllib.request.urlopen(url, timeout=300) as response:
        target.write_bytes(response.read())
    return target


def clean_geometry(raw, level):
    geometry = shape(raw)
    if not geometry.is_valid:
        geometry = make_valid(geometry)
    geometry = geometry.simplify(TOLERANCE[level], preserve_topology=True)
    return None if geometry.is_empty else geometry


def row_for(cursor, ucode, level, name, adm0_ucode, adm1_ucode, geometry):
    minx, miny, maxx, maxy = geometry.bounds
    blob = zlib.compress(
        json.dumps(mapping(geometry), separators=(",", ":")).encode("utf-8"), level=6
    )
    cursor.execute(
        """
        INSERT OR REPLACE INTO boundaries
            (ucode, level, name, adm0_ucode, adm1_ucode,
             minx, miny, maxx, maxy, area, geometry)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ucode, level, name, adm0_ucode, adm1_ucode,
         minx, miny, maxx, maxy, geometry.area, blob),
    )


def main():
    import sqlite3

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_DB)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    args = parser.parse_args()

    ucodes, names = load_country_ucodes()
    adm0_path = download(ADM0_FILE, args.cache_dir)
    adm1_path = download(ADM1_FILE, args.cache_dir)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(args.output)
    connection.executescript(
        """
        PRAGMA journal_mode=WAL;
        DROP TABLE IF EXISTS boundaries;
        CREATE TABLE boundaries (
            ucode TEXT PRIMARY KEY,
            level INTEGER NOT NULL,
            name TEXT NOT NULL,
            adm0_ucode TEXT NOT NULL,
            adm1_ucode TEXT,
            minx REAL NOT NULL, miny REAL NOT NULL,
            maxx REAL NOT NULL, maxy REAL NOT NULL,
            area REAL NOT NULL, geometry BLOB NOT NULL
        );
        CREATE INDEX boundaries_country_level ON boundaries(adm0_ucode, level);
        CREATE INDEX boundaries_bbox
            ON boundaries(level, adm0_ucode, minx, maxx, miny, maxy);
        """
    )
    cursor = connection.cursor()

    # ADM0 keyed by ISO3 so the ucodes match the ones case studies already carry.
    iso3_to_ucode = {}
    written = skipped = 0
    for feature in json.loads(adm0_path.read_text(encoding="utf-8"))["features"]:
        properties = feature["properties"]
        iso3 = properties.get("ADM0_A3") or properties.get("ISO_A3")
        iso3 = NE_TO_ISO3.get(iso3, iso3)
        ucode = ucodes.get(iso3)
        if not ucode:
            skipped += 1
            continue
        geometry = clean_geometry(feature["geometry"], 0)
        if geometry is None:
            skipped += 1
            continue
        iso3_to_ucode[iso3] = ucode
        row_for(cursor, ucode, 0, names.get(iso3, properties.get("NAME")), ucode, None, geometry)
        written += 1
    connection.commit()
    print(f"adm0: {written} countries written, {skipped} skipped (no ucode in countries_info.csv)")

    # ADM1 ucodes are invented. _V0 marks them as not from GeoRepo.
    counters = {}
    written = skipped = 0
    for feature in json.loads(adm1_path.read_text(encoding="utf-8"))["features"]:
        properties = feature["properties"]
        iso3 = properties.get("adm0_a3")
        iso3 = NE_TO_ISO3.get(iso3, iso3)
        adm0_ucode = iso3_to_ucode.get(iso3)
        if not adm0_ucode or not feature.get("geometry"):
            skipped += 1
            continue
        geometry = clean_geometry(feature["geometry"], 1)
        if geometry is None:
            skipped += 1
            continue
        counters[iso3] = counters.get(iso3, 0) + 1
        ucode = f"{iso3}_{counters[iso3]:04d}_V0"
        name = properties.get("name") or properties.get("name_en") or ucode
        row_for(cursor, ucode, 1, name, adm0_ucode, None, geometry)
        written += 1
    connection.commit()
    print(f"adm1: {written} regions written, {skipped} skipped")

    connection.execute("VACUUM")
    connection.close()
    size = args.output.stat().st_size / 1e6
    print(f"\nwrote {args.output} ({size:.1f} MB)")
    print("Stand-in cache. ADM0 ucodes are real; ADM1 ucodes are invented; ADM2 is absent.")


if __name__ == "__main__":
    main()
