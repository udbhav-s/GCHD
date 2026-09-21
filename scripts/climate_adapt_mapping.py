"""Vocabulary and geography mappings for the Climate-ADAPT case study source.

Kept apart from the scraper so the mapping decisions can be reviewed on their own.
"""

import csv
import re
from pathlib import Path


COLLECTION_NAME = "Climate-ADAPT Case Study Explorer"
COLLECTION_URL = (
    "https://climate-adapt.eea.europa.eu/en/knowledge/tools/case-study-explorer"
)
PUBLISHER = "European Environment Agency"
SOURCE_CONTENT_TYPE = "eea.climateadapt.casestudy"
IMPACT_VOCABULARY = "climate_adapt_climate_impacts"

COUNTRIES_INFO_CSV = (
    Path(__file__).resolve().parents[1]
    / "exposure_analysis"
    / "subnational_level"
    / "config"
    / "countries_info.csv"
)

# Climate-ADAPT climate-impact tokens to GCHD hazard IDs.
#
# Four tokens have no GCHD equivalent and map to nothing. They stay on the record
# in source_hazard_tags so the source vocabulary is not lost:
#   STORM        European windstorm, which is not the tropical_storm hazard
#   WATERSCARCE  a water-supply condition rather than a physical hazard layer
#   ICEANDSNOW   no GCHD layer
#   EXTREMECOLD  no GCHD layer
#   NONSPECIFIC  the source's own catch-all
CLIMATE_IMPACT_MAP = {
    "FLOODING": ["river_flood"],
    "SEALEVELRISE": ["coastal_flood"],
    "DROUGHT": ["meteorological_drought"],
    "EXTREMEHEAT": ["extreme_heat"],
    "WILDFIRES": ["wildfire"],
    "STORM": [],
    "WATERSCARCE": [],
    "ICEANDSNOW": [],
    "EXTREMECOLD": [],
    "NONSPECIFIC": [],
}

# Other Climate-ADAPT vocabularies worth keeping. The record field name maps to
# the vocabulary name written into source_tags.
SOURCE_TAG_FIELDS = {
    "sectors": "climate_adapt_sectors",
    "governance_level": "climate_adapt_governance_level",
    "elements": "climate_adapt_adaptation_elements",
}

# Climate-ADAPT rich-text fields that describe what was done and what came of it.
INTERVENTION_FIELDS = {
    "objectives": "objectives",
    "measures": "solutions",
    "outcomes": "success_limitations",
    "cost_benefit": "cost_benefit",
    "timeline": "implementation_time",
    "lifetime": "lifetime",
    "stakeholders": "stakeholder_participation",
    "legal_context": "legal_aspects",
}

# Terms that suggest a study is aimed at a particular group. These are hints read
# out of free text, so population_focus records that a scan produced them.
POPULATION_TERMS = {
    "children_youth": [
        "child", "children", "kids", "youth", "young people", "adolescent",
        "adolescents", "infant", "infants", "toddler", "pupil", "pupils",
        "paediatric", "pediatric", "minors",
    ],
    "schools": [
        "school", "schools", "schoolyard", "schoolyards", "kindergarten",
        "kindergartens", "nursery", "nurseries", "playground", "playgrounds",
        "classroom", "classrooms", "student", "students",
    ],
    "women": ["women", "girls", "maternal", "mothers"],
    "older_people": ["elderly", "older people", "older adults", "seniors", "pensioners"],
    "low_income": [
        "low-income", "low income", "poverty", "deprived", "disadvantaged",
        "informal settlement", "informal settlements",
    ],
    "displaced": ["refugee", "refugees", "migrant", "migrants", "displaced"],
    "health_patients": ["patient", "patients", "hospital", "hospitals"],
}

ISO2_TO_ISO3 = {
    "AT": "AUT", "BA": "BIH", "BE": "BEL", "BG": "BGR", "CH": "CHE",
    "CY": "CYP", "CZ": "CZE", "DE": "DEU", "DK": "DNK", "ES": "ESP",
    "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC", "HR": "HRV",
    "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "MD": "MDA",
    "MK": "MKD", "NL": "NLD", "NO": "NOR", "PL": "POL", "PT": "PRT",
    "RO": "ROU", "RS": "SRB", "SE": "SWE", "SI": "SVN", "SK": "SVK",
    "UA": "UKR",
}

# UN Data Commons country DCIDs follow the ISO3 code directly.
def dcid_for_iso3(iso3):
    return f"country/{iso3}"


def load_country_ucodes(path=COUNTRIES_INFO_CSV):
    """Map ISO3 to the GeoRepo ucode of the main country entity.

    One ISO3 can carry several ucodes, because GeoRepo splits some outlying
    island groups into their own entities (ESP1 Canary Islands, PRT1 Azores).
    The mainland entity is the one whose ucode starts with the bare ISO3.
    """
    ucodes = {}
    names = {}
    with open(path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            iso3 = row["ISO3"]
            ucode = row["ucode"]
            if ucode.startswith(f"{iso3}_"):
                ucodes[iso3] = ucode
                names[iso3] = row["name"]
    return ucodes, names


POPULATION_PATTERNS = {
    group: re.compile(
        r"\b(" + "|".join(re.escape(term) for term in sorted(terms, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )
    for group, terms in POPULATION_TERMS.items()
}


def detect_population_groups(text):
    """Find population groups named in a study's text.

    Returns the groups, the terms that triggered them, and how often each group
    was mentioned, so a reader can judge the match instead of trusting it. One
    passing mention is usually incidental.
    """
    groups = []
    evidence = []
    mentions = {}
    for group, pattern in POPULATION_PATTERNS.items():
        matches = pattern.findall(text)
        if not matches:
            continue
        groups.append(group)
        mentions[group] = len(matches)
        evidence.extend(sorted({match.lower() for match in matches}))
    return groups, sorted(set(evidence)), mentions


_SUFFIX = re.compile(r"\s*\(([A-Z]{2})\)\s*$")


def split_region_label(label):
    """Split a Climate-ADAPT region label into its name and country ISO2 code.

    Labels arrive as "Puglia (IT)" or "Prov. Antwerpen (BE)".
    """
    match = _SUFFIX.search(label)
    if not match:
        return label.strip(), None
    return label[: match.start()].strip(), match.group(1)


def slugify(value):
    """Reduce a string to the lowercase hyphenated form the schema's id pattern allows."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug)
