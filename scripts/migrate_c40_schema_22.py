#!/usr/bin/env python3
"""Upgrade the indexed C40 records to case-study schema 2.2.

The original C40 import retained a compact summary but not the source's
structured challenge/solution text.  This migration reads the public C40 API,
maps those sections into the 2.2 intervention object, and records the API
identity in provenance so the operation is reproducible.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


API_URL = "https://www.c40.org/wp-json/wp/v2/case-study"
COLLECTION_URL = "https://www.c40.org/case-studies/"
MIGRATION_VERSION = "migrate_c40_schema_22.py@1.0"
PAGE_SIZE = 100

HEADING_RE = re.compile(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]\s*>", re.I | re.S)
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(value: str | None) -> str:
    """Turn a C40 HTML fragment into compact, readable plain text."""
    if not value:
        return ""
    value = re.sub(r"<\s*(br|/p|/li|/div)\b[^>]*>", "\n", value, flags=re.I)
    value = TAG_RE.sub(" ", value)
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n\s*\n+", "\n", value)
    return value.strip()


def source_sections(content: str) -> list[tuple[str, str]]:
    """Return non-empty (heading, body) pairs from C40's HTML content."""
    matches = list(HEADING_RE.finditer(content or ""))
    sections = []
    for index, match in enumerate(matches):
        heading = clean_text(match.group(1))
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        body = clean_text(content[match.end() : end])
        if heading and body:
            sections.append((heading, body))
    return sections


def plain_content(content: str) -> str:
    """Return source content for records that do not use heading markup."""
    return clean_text(content)


def matching_sections(sections: list[tuple[str, str]], terms: tuple[str, ...]) -> str | None:
    values = [body for heading, body in sections if any(term in heading.lower() for term in terms)]
    if not values:
        return None
    return "\n\n".join(dict.fromkeys(values))


def intervention(record: dict) -> dict[str, str | None]:
    content = record.get("content", {}).get("rendered", "")
    sections = source_sections(content)
    source_text = plain_content(content)
    summary = clean_text(record.get("excerpt", {}).get("rendered", ""))

    objectives = matching_sections(sections, ("challenge", "problem", "context")) or summary
    measures = matching_sections(
        sections,
        (
            "solution",
            "what is it",
            "how does it work",
            "project description",
            "application",
            "implementation",
            "what is the policy",
        ),
    )
    if not measures:
        # Short C40 records often contain a single unheaded paragraph.
        measures = source_text or summary

    outcomes = matching_sections(
        sections,
        ("result", "impact", "success", "outcome", "next step", "co2 reduction"),
    )
    cost_benefit = matching_sections(
        sections,
        ("cost", "benefit", "economic", "saving", "funding", "finance"),
    )
    stakeholders = matching_sections(
        sections,
        ("stakeholder", "partner", "community", "volunteer", "governance", "engagement"),
    )
    legal_context = matching_sections(
        sections,
        ("legislation", "ordinance", "regulation", "legal", "policy"),
    )

    return {
        "objectives": objectives or None,
        "measures": measures or None,
        "outcomes": outcomes,
        "cost_benefit": cost_benefit,
        "timeline": None,
        "lifetime": None,
        "stakeholders": stakeholders,
        "legal_context": legal_context,
    }


def fetch_records() -> dict[str, dict]:
    records = {}
    for page in range(1, 100):
        query = urllib.parse.urlencode(
            {
                "per_page": PAGE_SIZE,
                "page": page,
                "orderby": "id",
                "order": "asc",
                "_embed": "wp:term",
            }
        )
        request = urllib.request.Request(
            f"{API_URL}?{query}", headers={"User-Agent": "Mirror-Worlds C40 schema migration"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.load(response)
        if not payload:
            break
        records.update({record["slug"]: record for record in payload})
        if len(payload) < PAGE_SIZE:
            break
    return records


def source_tags(record: dict) -> list[dict[str, str]]:
    tags = []
    for group in record.get("_embedded", {}).get("wp:term", []):
        for term in group:
            taxonomy = term.get("taxonomy")
            code = term.get("slug")
            label = clean_text(term.get("name"))
            if taxonomy and code and label:
                tags.append({"vocabulary": f"c40_{taxonomy}", "code": code, "label": label})
    return list({(tag["vocabulary"], tag["code"]): tag for tag in tags}.values())


def population_focus(record: dict, manifest_entry: dict | None) -> dict:
    criteria = set((manifest_entry or {}).get("criteria", []))
    groups = ["children_youth"] if "children_livelihood" in criteria else []
    return {
        "groups": groups,
        "determined_by": "llm_assisted" if groups else "manual",
        "evidence_terms": ["children", "youth"] if groups else [],
        "group_mentions": {},
    }


def upgraded_record(disk_record: dict, source_record: dict, manifest_entry: dict | None) -> dict:
    provenance = dict(disk_record.get("provenance", {}))
    provenance.update(
        {
            "source_record_id": str(source_record["id"]),
            "source_api_url": f"{API_URL}?slug={urllib.parse.quote(source_record['slug'])}&_embed=wp:term",
            "source_content_type": source_record.get("type") or "case-study",
            "source_modified": source_record.get("modified"),
            "extracted_by": MIGRATION_VERSION,
        }
    )

    additions = {
        "source_hazard_tags": [],
        "source_tags": source_tags(source_record),
        "population_focus": population_focus(source_record, manifest_entry),
        "intervention": intervention(source_record),
        "point": None,
    }
    upgraded = {}
    for key, value in disk_record.items():
        if key == "schema_version":
            upgraded[key] = "2.2"
        elif key == "provenance":
            upgraded[key] = provenance
        else:
            upgraded[key] = value
        if key == "hazards":
            upgraded.update(additions)
    return upgraded


def load_manifest(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as handle:
        return {str(item["id"]): item for item in json.load(handle)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-studies", type=Path, default=Path(__file__).parents[1] / "case_studies")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).parents[1] / "case_study_imports" / "c40" / "manifest.json",
    )
    args = parser.parse_args()

    paths = sorted(args.case_studies.glob("c40-*.json"))
    api_records = fetch_records()
    manifest = load_manifest(args.manifest)
    upgrades = []
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            disk_record = json.load(handle)
        slug = disk_record["url"].rstrip("/").split("/")[-1]
        source = api_records.get(slug)
        if source is None:
            raise RuntimeError(f"C40 API did not return indexed slug: {slug}")
        entry = manifest.get(str(source["id"]))
        upgrades.append((path, upgraded_record(disk_record, source, entry)))

    for path, record in upgrades:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(f"updated {len(upgrades)} C40 records from {len(api_records)} API records")


if __name__ == "__main__":
    main()
