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
