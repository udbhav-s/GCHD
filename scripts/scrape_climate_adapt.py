#!/usr/bin/env python3
"""Turn Climate-ADAPT case studies into GCHD case-study records.

The European Environment Agency publishes its case studies through a Plone REST
API, so this reads structured fields rather than parsing pages. Responses are
cached on disk; a re-run without --refresh reuses the cache and writes the same
output.

    python scripts/scrape_climate_adapt.py --out case_studies/
"""

import argparse
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from climate_adapt_mapping import (  # noqa: E402
    CLIMATE_IMPACT_MAP,
    COLLECTION_NAME,
    COLLECTION_URL,
    IMPACT_VOCABULARY,
    INTERVENTION_FIELDS,
    ISO2_TO_ISO3,
    PUBLISHER,
    SOURCE_CONTENT_TYPE,
    SOURCE_TAG_FIELDS,
    dcid_for_iso3,
    detect_population_groups,
    load_country_ucodes,
    slugify,
    split_region_label,
)

SCRAPER_VERSION = "scrape_climate_adapt.py@1.1"
API_ROOT = "https://climate-adapt.eea.europa.eu/++api++/en"
SEARCH_URL = f"{API_ROOT}/@search"
ID_PREFIX = "climate-adapt"
PAGE_SIZE = 50
SUMMARY_LIMIT = 700

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "case_studies"
DEFAULT_CACHE = REPO_ROOT / ".cache" / "climate_adapt"


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def _get_json(url, timeout=90, attempts=3):
    last_error = None
    for _ in range(attempts):
        try:
            request = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": "GCHD-case-study-scraper/1.0"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except Exception as error:  # network and decode failures are both retryable
            last_error = error
    raise RuntimeError(f"Could not fetch {url}: {last_error}")


def fetch_index():
    """List every published case study. The API rejects large page sizes, so page through."""
    items = []
    start = 0
    while True:
        page = _get_json(
            f"{SEARCH_URL}?portal_type={SOURCE_CONTENT_TYPE}&b_size={PAGE_SIZE}&b_start={start}"
        )
        batch = page.get("items", [])
        items.extend(batch)
        total = page.get("items_total", 0)
        start += PAGE_SIZE
        if not batch or start >= total:
            return items, total


def api_url(page_url):
    return page_url.replace(
        "climate-adapt.eea.europa.eu/", "climate-adapt.eea.europa.eu/++api++/"
    )


def fetch_records(index, cache_dir, refresh=False, workers=6):
    cache_dir.mkdir(parents=True, exist_ok=True)

    def one(entry):
        slug = entry["@id"].rstrip("/").rsplit("/", 1)[-1]
        cached = cache_dir / f"{slug}.json"
        if cached.exists() and not refresh:
            return json.loads(cached.read_text(encoding="utf-8"))
        record = _get_json(api_url(entry["@id"]))
        cached.write_text(json.dumps(record), encoding="utf-8")
        return record

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, index))


# --------------------------------------------------------------------------
# Field helpers
# --------------------------------------------------------------------------

# Around half the collection stores a stringified Python None in text fields
# instead of leaving them empty. Treat those as blank.
PLACEHOLDER_TEXT = {"none", "null", "nan", "-", "n/a"}


def clean_text(value):
    if not value:
        return ""
    text = re.sub(r"\s+", " ", str(value)).strip()
    return "" if text.lower() in PLACEHOLDER_TEXT else text


def rich_text(field):
    """Flatten one of the API's HTML rich-text fields to plain text."""
    if not field:
        return ""
    data = field.get("data") if isinstance(field, dict) else field
    if not data:
        return ""
    text = re.sub(r"<[^>]+>", " ", data)
    return clean_text(html.unescape(text))


def build_summary(record):
    """Use the record's abstract, falling back to the body when it is blank.

    Around half the collection ships an empty description, so the fallback is
    the common path rather than an edge case.
    """
    description = clean_text(record.get("description"))
    if description:
        return description

    body = rich_text(record.get("long_description"))
    if len(body) <= SUMMARY_LIMIT:
        return body
    cut = body[:SUMMARY_LIMIT]
    stop = cut.rfind(". ")
    return (cut[: stop + 1] if stop > SUMMARY_LIMIT // 2 else cut.rstrip() + "…").strip()


def geo_elements(record):
    try:
        return json.loads(record.get("geochars") or "{}").get("geoElements", {}) or {}
    except json.JSONDecodeError:
        return {}


def build_hazards(record):
    """Map the source's climate-impact tokens, keeping every tag including unmapped ones."""
    hazards = []
    tags = []
    for impact in record.get("climate_impacts") or []:
        token = impact.get("token")
        if not token:
            continue
        mapped = CLIMATE_IMPACT_MAP.get(token)
        if mapped is None:
            print(f"  ! unknown climate impact token: {token}", file=sys.stderr)
            mapped = []
        for hazard in mapped:
            if hazard not in hazards:
                hazards.append(hazard)
        tags.append(
            {
                "vocabulary": IMPACT_VOCABULARY,
                "code": token,
                "label": impact.get("title") or token,
                "mapped_to": list(mapped),
            }
        )
    return hazards, tags


def build_source_tags(record):
    """Keep the source's other controlled vocabularies, such as sectors."""
    tags = []
    for field, vocabulary in SOURCE_TAG_FIELDS.items():
        for entry in record.get(field) or []:
            code = entry.get("token")
            if not code:
                continue
            tags.append(
                {"vocabulary": vocabulary, "code": code, "label": entry.get("title") or code}
            )
    for keyword in record.get("keywords") or []:
        keyword = clean_text(keyword)
        if keyword:
            tags.append(
                {"vocabulary": "climate_adapt_keywords", "code": keyword, "label": keyword}
            )
    return tags


def build_intervention(record):
    """Pull the source's account of what was done and what came of it."""
    intervention = {
        key: (rich_text(record.get(field)) or None)
        for key, field in INTERVENTION_FIELDS.items()
    }
    return intervention if any(intervention.values()) else None


def build_population_focus(record):
    """Scan the study's text for the groups it is aimed at."""
    parts = [clean_text(record.get("description"))]
    parts += [rich_text(record.get(field)) for field in INTERVENTION_FIELDS.values()]
    parts.append(rich_text(record.get("long_description")))
    parts.append(rich_text(record.get("challenges")))

    groups, evidence, mentions = detect_population_groups(
        " ".join(part for part in parts if part)
    )
    return {
        "groups": groups,
        "determined_by": "keyword_scan",
        "evidence_terms": evidence,
        "group_mentions": mentions,
    }


def admin_unit(name, ucode=None, iso3=None, dcid=None, source_code=None, source_name=None):
    unit = {"name": name, "ucode": ucode, "dcid": dcid}
    if iso3 is not None:
        unit["iso3"] = iso3
    if source_code is not None:
        unit["source_code"] = source_code
    if source_name is not None:
        unit["source_name"] = source_name
    return unit


def build_locations(record, country_ucodes, country_names):
    """Build one location path per country named by the record.

    Climate-ADAPT reports subnational coverage as NUTS-2 region names rather than
    codes, so those units carry a name and the source label but no ucode. They sit
    at adm1 because that is the closest GCHD level; resolve_ucodes.py decides the
    real level when a GeoRepo boundary cache is available.
    """
    elements = geo_elements(record)
    geographic = record.get("geographic") or {}
    iso2_codes = elements.get("countries") or []
    city = clean_text(elements.get("city"))

    regions = {}
    for label in geographic.get("sub_nationals") or []:
        region_name, iso2 = split_region_label(label)
        if len(iso2_codes) == 1 and iso2 is None:
            iso2 = iso2_codes[0]
        regions.setdefault(iso2, []).append((region_name, label))

    source_tokens = elements.get("subnational") or []

    if not iso2_codes:
        # A handful of studies cover Europe as a whole with no country named.
        transnational = geographic.get("transnational_region") or geographic.get(
            "geographic_characterisation"
        ) or ["Europe"]
        return [
            {
                "level": "non_administrative",
                "place_name": ", ".join(transnational),
                "adm0": None,
                "adm1": None,
                "adm2": None,
            }
        ], "non_administrative"

    locations = []
    for iso2 in iso2_codes:
        iso3 = ISO2_TO_ISO3.get(iso2)
        if not iso3:
            print(f"  ! no ISO3 mapping for country {iso2}", file=sys.stderr)
            continue

        adm0 = admin_unit(
            name=country_names.get(iso3, iso2),
            ucode=country_ucodes.get(iso3),
            iso3=iso3,
            dcid=dcid_for_iso3(iso3),
        )

        country_regions = regions.get(iso2) or []
        # One location per region so each unit resolves on its own.
        if not country_regions:
            country_regions = [(None, None)]

        for region_name, region_label in country_regions:
            adm1 = None
            if region_name:
                token = next(
                    (t for t in source_tokens if slugify(t).startswith("subn-" + slugify(region_name)[:12])),
                    None,
                )
                adm1 = admin_unit(
                    name=region_name,
                    ucode=None,
                    dcid=None,
                    source_code=token,
                    source_name=region_label,
                )

            place_name = city if (city and len(iso2_codes) == 1) else None
            if place_name:
                level = "non_administrative"
            elif adm1:
                level = "adm1"
            else:
                level = "adm0"

            locations.append(
                {
                    "level": level,
                    "place_name": place_name,
                    "adm0": adm0,
                    "adm1": adm1,
                    "adm2": None,
                }
            )

    order = ["adm0", "adm1", "adm2", "non_administrative"]
    scope = max((location["level"] for location in locations), key=order.index)
    return locations, scope


def build_data_sources(record):
    """Record the websites the study points at. The API does not expose its analytical inputs."""
    sources = []
    for url in record.get("websites") or []:
        url = (url or "").strip()
        if not url:
            continue
        host = re.sub(r"^www\.", "", urllib.parse.urlparse(url).netloc)
        sources.append({"name": host or url, "url": url, "role": "contextual_input"})
    return sources


def build_point(record):
    location = record.get("geolocation") or {}
    lat, lon = location.get("latitude"), location.get("longitude")
    if lat is None or lon is None:
        return None
    return {"lat": lat, "lon": lon, "source": "climate_adapt_geolocation"}


def publication_date(record):
    value = record.get("publication_date") or record.get("cca_published")
    return value[:10] if value else None


def convert(record, country_ucodes, country_names, retrieved_at):
    hazards, hazard_tags = build_hazards(record)
    locations, scope = build_locations(record, country_ucodes, country_names)
    page_url = record["@id"]

    return {
        "schema_version": "2.2",
        "id": f"{ID_PREFIX}-{slugify(record['id'])}",
        "url": page_url,
        "title": clean_text(record.get("title")),
        "summary": build_summary(record),
        "location_scope": scope,
        "locations": locations,
        "hazards": hazards,
        "source_hazard_tags": hazard_tags,
        "source_tags": build_source_tags(record),
        "population_focus": build_population_focus(record),
        "intervention": build_intervention(record),
        "point": build_point(record),
        "data_sources": build_data_sources(record),
        "provenance": {
            "collection_name": COLLECTION_NAME,
            "collection_url": COLLECTION_URL,
            "publisher": PUBLISHER,
            "document_url": page_url,
            "publication_date": publication_date(record),
            "retrieved_at": retrieved_at,
            "extraction_method": "api",
            "source_record_id": record.get("UID"),
            "source_api_url": api_url(page_url),
            "source_content_type": record.get("@type"),
            "source_modified": record.get("cca_last_modified") or record.get("modified"),
            "extracted_by": SCRAPER_VERSION,
        },
        "sdgs": [],
        "indicators_measured": [],
        "indicators_targeted": [],
    }


# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--refresh", action="store_true", help="Ignore cached responses")
    parser.add_argument("--limit", type=int, help="Convert only the first N records")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing files")
    args = parser.parse_args()

    country_ucodes, country_names = load_country_ucodes()
    retrieved_at = date.today().isoformat()

    index, total = fetch_index()
    print(f"index: {len(index)} of {total} case studies")
    if args.limit:
        index = index[: args.limit]

    records = fetch_records(index, args.cache_dir, refresh=args.refresh)
    print(f"fetched: {len(records)} records (cache {args.cache_dir})")

    args.out.mkdir(parents=True, exist_ok=True)
    written = 0
    for record in records:
        converted = convert(record, country_ucodes, country_names, retrieved_at)
        if args.dry_run:
            continue
        path = args.out / f"{converted['id']}.json"
        path.write_text(
            json.dumps(converted, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        written += 1

    print(f"written: {written} records to {args.out}")


if __name__ == "__main__":
    main()
