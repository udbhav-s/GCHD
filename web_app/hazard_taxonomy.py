"""Link case-study hazard IDs to the dashboard's hazard topics and layers.

Case studies record hazards in the schema's vocabulary, such as extreme_heat.
The dashboard works in topics and raster layer codes, such as Extreme Heat and
maximum_temperature_era5_land_2024. schema/hazard-taxonomy.json holds the
correspondence; this module reads it so both halves of the app can filter on the
same thing.
"""

import json
from pathlib import Path

TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "schema" / "hazard-taxonomy.json"

_taxonomy = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))

HAZARDS = _taxonomy["hazards"]
PUBLIC_LAYERS = set(_taxonomy.get("public_layers", []))

# Dashboard topic to the case-study hazard IDs that belong to it. Several hazard
# IDs can share a topic: Drought covers both the agricultural and the
# meteorological kind.
TOPIC_TO_HAZARDS = {}
for hazard_id, entry in HAZARDS.items():
    topic = entry.get("dashboard_topic")
    if topic:
        TOPIC_TO_HAZARDS.setdefault(topic, set()).add(hazard_id)

HAZARD_TO_TOPIC = {
    hazard_id: entry.get("dashboard_topic") for hazard_id, entry in HAZARDS.items()
}

LAYER_TO_HAZARDS = {}
for hazard_id, entry in HAZARDS.items():
    for layer in entry.get("layers", []):
        LAYER_TO_HAZARDS.setdefault(layer, set()).add(hazard_id)

# Hazard IDs with no dashboard topic. They still need to be filterable.
UNTOPICED_HAZARDS = {
    hazard_id for hazard_id, topic in HAZARD_TO_TOPIC.items() if not topic
}

TOPIC_PREFIX = "topic:"
HAZARD_PREFIX = "hazard:"


def hazard_label(hazard_id):
    entry = HAZARDS.get(hazard_id)
    return entry["name"] if entry else hazard_id.replace("_", " ").title()


def hazards_for_layers(layer_names):
    """Case-study hazard IDs that correspond to the given dashboard layers."""
    matched = set()
    for layer in layer_names or []:
        matched |= LAYER_TO_HAZARDS.get(layer, set())
    return matched


def expand_filter_values(values):
    """Turn filter values into the set of hazard IDs they select.

    A value is either a dashboard topic or a single hazard ID, distinguished by
    prefix. Anything unprefixed is treated as a bare hazard ID so older saved
    filters keep working.
    """
    hazards = set()
    for value in values or []:
        if value.startswith(TOPIC_PREFIX):
            hazards |= TOPIC_TO_HAZARDS.get(value[len(TOPIC_PREFIX):], set())
        elif value.startswith(HAZARD_PREFIX):
            hazards.add(value[len(HAZARD_PREFIX):])
        else:
            hazards.add(value)
    return hazards


def filter_options(present_hazards):
    """Build hazard filter options for the hazards that actually occur in the data.

    Topics come first, so picking Drought catches both drought hazards at once.
    Hazards with no dashboard topic are listed on their own.
    """
    present = set(present_hazards)
    options = []
    for topic in sorted(TOPIC_TO_HAZARDS):
        covered = TOPIC_TO_HAZARDS[topic] & present
        if not covered:
            continue
        options.append(
            {
                "label": f"{topic} ({len(covered)} hazard types)"
                if len(covered) > 1
                else topic,
                "value": f"{TOPIC_PREFIX}{topic}",
            }
        )
    for hazard_id in sorted(UNTOPICED_HAZARDS & present):
        options.append(
            {"label": hazard_label(hazard_id), "value": f"{HAZARD_PREFIX}{hazard_id}"}
        )
    return options
