#!/usr/bin/env python3
"""Fill in missing GeoRepo ucodes on case-study records by matching region names.

Scrapers that read a source which names its regions instead of coding them leave
adm1 and adm2 units with a null ucode. This matches those names against the
GeoRepo boundary cache and writes the ucode back.

The cache is the one web_app/scripts/build_georepo_cache.py produces, so build it
first. Matching is by name within the record's country, and a unit is only
rewritten on an unambiguous match. Everything else is reported for a human.

    python scripts/resolve_ucodes.py --db web_app/data/georepo/boundaries.sqlite
    python scripts/resolve_ucodes.py --db ... --apply
"""

import argparse
import difflib
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "web_app" / "data" / "georepo" / "boundaries.sqlite"
DEFAULT_DIR = REPO_ROOT / "case_studies"

# Administrative prefixes and suffixes that a source may carry but GeoRepo does not.
NOISE = re.compile(
    r"^(prov\.?|provincia|province|provincie|region|regione|región|região|"
    r"comunidad|comunitat|kanton|canton|county|okres|zupanija|"
    r"regierungsbezirk|departement|département)\s+(of\s+|de\s+|di\s+)?",
    re.IGNORECASE,
)


def normalise(name):
    """Reduce a region name to a comparable form: no accents, no punctuation, no admin prefix."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = NOISE.sub("", text.strip())
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def load_candidates(db_path):
    """Index every adm1 and adm2 boundary by country and normalised name."""
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        "SELECT ucode, level, name, adm0_ucode FROM boundaries WHERE level IN (1, 2)"
    ).fetchall()
    connection.close()

    index = {}
    for row in rows:
        key = (row["adm0_ucode"], normalise(row["name"]))
        index.setdefault(key, []).append(
            {"ucode": row["ucode"], "level": row["level"], "name": row["name"]}
        )
    return index


def find_match(index, adm0_ucode, name, cutoff):
    """Return (match, note). match is None when nothing is safe to write."""
    key = normalise(name)
    exact = index.get((adm0_ucode, key))
    if exact and len(exact) == 1:
        return exact[0], "exact"
    if exact:
        levels = {c["level"] for c in exact}
        if len(levels) > 1:
            return None, f"ambiguous across levels: {[c['ucode'] for c in exact]}"
        return None, f"ambiguous: {[c['ucode'] for c in exact]}"

    names = [k[1] for k in index if k[0] == adm0_ucode]
    close = difflib.get_close_matches(key, names, n=2, cutoff=cutoff)
    if len(close) == 1:
        candidates = index[(adm0_ucode, close[0])]
        if len(candidates) == 1:
            return candidates[0], f"fuzzy ~ {close[0]}"
    if not close:
        return None, "no candidate"
    return None, f"fuzzy ambiguous: {close}"


def resolve_record(record, index, cutoff):
    """Fill ucodes in one record. Returns (changed, report rows)."""
    changed = False
    report = []
    for location in record.get("locations", []):
        for level_key in ("adm1", "adm2"):
            unit = location.get(level_key)
            if not unit or unit.get("ucode"):
                continue
            adm0 = location.get("adm0") or {}
            adm0_ucode = adm0.get("ucode")
            if not adm0_ucode:
                report.append((record["id"], level_key, unit["name"], "no country ucode"))
                continue

            match, note = find_match(index, adm0_ucode, unit["name"], cutoff)
            if not match:
                report.append((record["id"], level_key, unit["name"], note))
                continue

            unit["ucode"] = match["ucode"]
            matched_key = f"adm{match['level']}"
            # The source's level is a guess; GeoRepo decides where the unit really sits.
            if matched_key != level_key:
                location[matched_key] = unit
                location[level_key] = None
                if location.get("level") == level_key:
                    location["level"] = matched_key
            changed = True
            report.append((record["id"], matched_key, unit["name"], f"{note} -> {match['ucode']}"))
    return changed, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--apply", action="store_true", help="Write the matches back to disk")
    parser.add_argument("--cutoff", type=float, default=0.92, help="Fuzzy match threshold")
    args = parser.parse_args()

    if not args.db.exists():
        sys.exit(
            f"No boundary cache at {args.db}.\n"
            "Build it first with web_app/scripts/build_georepo_cache.py."
        )

    index = load_candidates(args.db)
    print(f"boundary cache: {len(index):,} distinct country/name keys")

    resolved = unresolved = 0
    for path in sorted(args.dir.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        changed, report = resolve_record(record, index, args.cutoff)
        for study_id, level, name, note in report:
            arrow = "->" in note
            resolved += arrow
            unresolved += not arrow
            print(f"  {'OK ' if arrow else '?? '} {study_id} {level} {name!r}: {note}")
        if changed and args.apply:
            path.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

    print(f"\nresolved {resolved}, unresolved {unresolved}")
    if not args.apply:
        print("Dry run. Re-run with --apply to write these ucodes back.")


if __name__ == "__main__":
    main()
