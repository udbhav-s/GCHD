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


def _strip_accents(text):
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalise(name):
    """Reduce a region name to a comparable form: no accents, no punctuation, no admin prefix."""
    text = _strip_accents(name)
    text = NOISE.sub("", text.strip())
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


_PAREN = re.compile(r"^(.*?)\s*\(([^)]+)\)\s*$")

# Administrative words some sources append: Stockholms Laen, Aarhus Amt.
SUFFIX_NOISE = re.compile(
    r"\s+(laen|lan|amt|amtskommune|county|counties|region|regionen|megye|"
    r"voivodeship|oblast|zhupa)$",
    re.IGNORECASE,
)


def name_variants(name):
    """Every comparable form of a region name.

    Sources and GeoRepo write the same region differently. Spain's Madrid is
    "Comunidad de Madrid" in one and "Madrid, Comunidad De" in the other, and
    Greek regions arrive as "Aττική (Attiki)" against a plain "Attiki". Matching
    on any shared form catches these without loosening the comparison itself.
    """
    variants = set()

    def add(value):
        key = normalise(value)
        if key:
            variants.add(key)
            trimmed = SUFFIX_NOISE.sub("", key).strip()
            if trimmed:
                variants.add(trimmed)

    add(name)

    # Bilingual names joined by a slash, as Brussels is written in French and Dutch.
    if "/" in name:
        for part in name.split("/"):
            add(part)

    # "Attiki" out of "Aττική (Attiki)": keep a parenthetical when the name
    # outside it does not survive being reduced to Latin letters.
    match = _PAREN.match(name)
    if match:
        outside, inside = match.group(1), match.group(2)
        add(inside)
        if re.search(r"[a-zA-Z]", _strip_accents(outside)):
            add(outside)

    # "Madrid, Comunidad De" and "Comunidad de Madrid" meet in the middle.
    if "," in name:
        parts = [part.strip() for part in name.split(",") if part.strip()]
        if len(parts) == 2:
            add(" ".join(reversed(parts)))
            add(parts[0])

    return variants


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
        entry = {"ucode": row["ucode"], "level": row["level"], "name": row["name"]}
        for variant in name_variants(row["name"]):
            index.setdefault((row["adm0_ucode"], variant), []).append(entry)
    return index


def find_match(index, adm0_ucode, name, cutoff):
    """Return (match, note). match is None when nothing is safe to write."""
    for key in sorted(name_variants(name)):
        exact = index.get((adm0_ucode, key))
        if not exact:
            continue
        unique = {candidate["ucode"]: candidate for candidate in exact}
        if len(unique) == 1:
            return next(iter(unique.values())), "exact"
        levels = {candidate["level"] for candidate in unique.values()}
        if len(levels) > 1:
            return None, f"ambiguous across levels: {sorted(unique)}"
        return None, f"ambiguous: {sorted(unique)}"

    key = normalise(name)
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
