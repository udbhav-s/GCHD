#!/usr/bin/env python3
"""Bring the hand-authored case studies up to schema 2.2.

These records were written by hand rather than scraped, so
migrate_c40_schema_22.py cannot touch them: it reads every 2.2 field from the
C40 API and keys on a slug they do not have. This fills in what can be derived
from each record itself and leaves the rest empty instead of inventing it.

  population_focus  Scanned from the record's own title and summary, with the
                    same term list the Climate-ADAPT scraper uses.
  point             Null. There is no source coordinate to take one from.
  source_tags       Empty. These records come from no tagged collection.
  intervention      Null. The source text it needs was never captured.

The indicator fields these records already carry are left untouched. They are
the only records in the collection that have them.

    python scripts/migrate_legacy_schema_22.py            # report, write nothing
    python scripts/migrate_legacy_schema_22.py --apply
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from climate_adapt_mapping import detect_population_groups  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = REPO_ROOT / "case_studies"
TARGET_VERSION = "2.2"
MIGRATION_VERSION = "migrate_legacy_schema_22.py@1.0"


def population_focus(record: dict) -> dict:
    """Read the groups a study names out of its own text."""
    text = " ".join(part for part in (record.get("title"), record.get("summary")) if part)
    groups, evidence, mentions = detect_population_groups(text)
    return {
        "groups": groups,
        "determined_by": "keyword_scan",
        "evidence_terms": evidence,
        "group_mentions": mentions,
    }


def upgraded_record(record: dict) -> dict:
    """Return the record at 2.2, with the new fields after hazards."""
    provenance = dict(record.get("provenance", {}))
    provenance["extracted_by"] = MIGRATION_VERSION

    additions = {
        "source_hazard_tags": [],
        "source_tags": [],
        "population_focus": population_focus(record),
        "intervention": None,
        "point": None,
    }

    upgraded = {}
    for key, value in record.items():
        if key == "schema_version":
            upgraded[key] = TARGET_VERSION
        elif key == "provenance":
            upgraded[key] = provenance
        else:
            upgraded[key] = value
        if key == "hazards":
            upgraded.update(additions)
    return upgraded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-studies", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--apply", action="store_true", help="write the changes")
    args = parser.parse_args()

    upgrades = []
    for path in sorted(args.case_studies.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            record = json.load(handle)
        if str(record.get("schema_version")) == TARGET_VERSION:
            continue
        upgrades.append((path, upgraded_record(record)))

    for path, record in upgrades:
        focus = record["population_focus"]
        groups = ", ".join(focus["groups"]) if focus["groups"] else "none"
        print(f"{path.name}\n    groups: {groups}")

    if not args.apply:
        print(f"\n{len(upgrades)} records would be upgraded. Re-run with --apply to write.")
        return

    for path, record in upgrades:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(f"\n{len(upgrades)} records upgraded to schema {TARGET_VERSION}.")


if __name__ == "__main__":
    main()
