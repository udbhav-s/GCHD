# =============================================================================
# config.py — Static configuration: hazards, topics, colors, admin levels
# No GEE imports here so this loads instantly.
# =============================================================================
#
# Only the layers this fork runs appear here. Colours, palettes and info text
# for the wider GCHD hazard catalogue used to sit alongside them with no code
# behind them, which made the app look like it covered hazards it does not.
# Git history has them if a layer arrives.

# Each hazard layer counts how many time steps met its condition, rather than
# recording only whether one ever did. `threshold` and `direction` are the test
# applied to a single step; `duration_options` are the minimum counts a user can
# ask for. The unit differs by source and is not normalised: ERA5-Land and FIRMS
# report daily, TerraClimate monthly. Calling twelve monthly readings "days"
# would hide that difference.
HAZARDS = [
    {
        "id": "WorldPop/GP/100m/pop_age_sex_cons_unadj",
        "name": "population_worldpop_2020",
        "kind": "population",
        "year": 2020,
        "vis_min": 0,
        "vis_max": 100,
    },
    {
        "id": "ECMWF/ERA5_LAND/DAILY_AGGR",
        "name": "maximum_temperature_era5_land_2024",
        "kind": "collection",
        "band": "temperature_2m_max",
        "start": "2024-01-01",
        "end": "2025-01-01",
        "threshold": 308.15,
        "direction": "gt",
        "duration_unit": "days",
        "duration_options": [1, 7, 30],
        "duration_default": 1,
        "baseline_start": 1991,
        "baseline_end": 2020,
        "vis_min": 0,
        "vis_max": 120,
    },
    {
        "id": "IDAHO_EPSCOR/TERRACLIMATE",
        "name": "drought_pdsi_terraclimate_2024",
        "kind": "collection",
        "band": "pdsi",
        "start": "2024-01-01",
        "end": "2025-01-01",
        "scale_factor": 0.01,
        "threshold": -2,
        "direction": "lt",
        "duration_unit": "months",
        "duration_options": [1, 2, 3],
        "duration_default": 1,
        "baseline_start": 1991,
        "baseline_end": 2020,
        "vis_min": 0,
        "vis_max": 12,
    },
    {
        "id": "FIRMS",
        "name": "active_fire_frequency_firms_2024",
        "kind": "collection",
        "band": "T21",
        "start": "2024-01-01",
        "end": "2025-01-01",
        "threshold": 0,
        "direction": "gt",
        "duration_unit": "days",
        "duration_options": [1, 7, 30],
        "duration_default": 1,
        # FIRMS begins in November 2000, so fire cannot share the 1991-2020
        # baseline. It also spans a MODIS to VIIRS change, which alters how
        # sensitive detection is across the window.
        "baseline_start": 2001,
        "baseline_end": 2024,
        "vis_min": 0,
        "vis_max": 30,
    },
]

HAZARD_MAP = {h["name"]: h for h in HAZARDS}

DURATION_HAZARDS = [h for h in HAZARDS if h.get("duration_options")]


def duration_label(hazard, minimum):
    """How a duration choice reads in the interface."""
    unit = hazard["duration_unit"]
    if minimum <= 1:
        return f"Any ({unit[:-1]} or more)"
    return f"{minimum}+ {unit}"


def default_durations():
    return {h["name"]: h["duration_default"] for h in DURATION_HAZARDS}


def clean_durations(selected):
    """Keep only choices this config offers, and fill in the rest.

    A stale value from a saved session must not silently become a different
    threshold than the label claims.
    """
    selected = selected or {}
    cleaned = {}
    for hazard in DURATION_HAZARDS:
        value = selected.get(hazard["name"], hazard["duration_default"])
        if value not in hazard["duration_options"]:
            value = hazard["duration_default"]
        cleaned[hazard["name"]] = value
    return cleaned


# Two periods, never mixed on one map. "observed" is what happened in 2024.
# "typical" counts how often a year like that turned up across a longer record,
# which is the closest this data comes to saying how likely something is.
PERIOD_OPTIONS = ["observed", "typical"]
PERIOD_DEFAULT = "observed"

PERIOD_LABELS = {
    "observed": "2024",
    "typical":  "Typical year",
}

# How often the hazard has to qualify before a place counts, stated per ten
# years so the windows stay comparable: heat and drought run 30 years, fire 24.
FREQUENCY_OPTIONS = [1, 3, 5]
FREQUENCY_DEFAULT = 1


def clean_period(value):
    return value if value in PERIOD_OPTIONS else PERIOD_DEFAULT


def clean_frequency(value):
    return value if value in FREQUENCY_OPTIONS else FREQUENCY_DEFAULT


def frequency_label(per_ten):
    return f"{per_ten}+ years in 10"


def baseline_window(hazard):
    return hazard["baseline_start"], hazard["baseline_end"]


def baseline_years(hazard):
    start, end = baseline_window(hazard)
    return end - start + 1


def baseline_label(hazard):
    start, end = baseline_window(hazard)
    return f"{start}–{end}"


def baseline_windows_differ():
    """True when the layers do not share one baseline, which has to be said out
    loud rather than left for a reader to discover."""
    return len({baseline_window(h) for h in DURATION_HAZARDS}) > 1

# WorldPop splits population into age bands labelled by the first year each one
# covers: 0 is under 1, 1 is 1-4, 5 is 5-9, 10 is 10-14, 15 is 15-19. UNICEF
# counts a child as anyone under 18, which cuts the 15-19 band in the middle, so
# that band is counted at three fifths and the rest are counted whole.
#
# The band named "population" is every age together. Using it would report the
# whole population rather than children.
CHILD_AGE_BANDS = ["0", "1", "5", "10"]
CHILD_PARTIAL_BAND = "15"
CHILD_PARTIAL_FRACTION = 0.6
CHILD_AGE_LABEL = "under 18"

# The youngest children, band 0 being under one and band 1 covering one to four.
# They are counted separately because age is the one thing about vulnerability
# this data can already answer: under-fives carry far more of the health burden
# from heat, smoke and undernutrition than older children do.
UNDER_FIVE_BANDS = ["0", "1"]
UNDER_FIVE_LABEL = "under 5"

HAZARD_TOPICS = {
    "Extreme Heat": ["maximum_temperature_era5_land_2024"],
    "Drought":      ["drought_pdsi_terraclimate_2024"],
    "Fire":         ["active_fire_frequency_firms_2024"],
}

REFERENCE_LAYERS = ["population_worldpop_2020"]

# Topics that show sub-hazard breakdown in the results panel
SUB_TOPIC_DETAIL = []

ALLOW_NEGATIVE = []  # Public layers use explicit visualization ranges.

TOPIC_COLORS = {
    "Drought":             "#ff7f00",
    "Extreme Heat":        "#6a3d9a",
    "Fire":                "#fb9a99",
    "Multi Hazard Count":  "#800026",
}

# Vis palettes per individual hazard (for map display).
#
# These ramps run light to dark as the count rises. They have to: the layers now
# draw how many days or months met a condition, so more colour must mean more
# hazard. The drought ramp used to run the other way, because it was built for
# PDSI values where a negative number means dry. Against a count of dry months
# that put the driest places in the same green as the wettest.
HAZARD_VIS_PALETTES = {
    "population_worldpop_2020": ["#24126c", "#1fff4f", "#d4ff50"],
    "maximum_temperature_era5_land_2024": ["#ffffcc", "#fdae61", "#f46d43", "#d73027", "#7f0000"],
    "drought_pdsi_terraclimate_2024": ["#f6e8c3", "#dfc27d", "#bf812d", "#8c510a", "#543005"],
    "active_fire_frequency_firms_2024": ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
}

# Vulnerability is drawn in its own colour family so it cannot be mistaken for
# a hazard layer on the map.
VULNERABILITY_PALETTE = ["#f7f4f9", "#d4b9da", "#c994c7", "#df65b0", "#ce1256"]

UNDER_FIVE_LAYER = "under_five_share"

# Coping capacity, as far as global data can carry it. This is travel time to
# the nearest health facility: whether care is reachable, not whether it has
# beds or staff. No global facility-level capacity data exists, so the app says
# "access" and never claims more.
ACCESS_LAYER = "travel_time_to_healthcare"
ACCESS_ASSET = "projects/malariaatlasproject/assets/accessibility/accessibility_to_healthcare/2019"
ACCESS_BAND = "accessibility"

# Minutes beyond which care counts as out of reach. Kept as discrete choices
# rather than a slider, like every other threshold here.
ACCESS_OPTIONS = [30, 60, 120]
ACCESS_DEFAULT = 60
ACCESS_VIS_MAX = 300

# Its own colour family again, so capacity cannot be read as hazard or as
# vulnerability on the same map.
CAPACITY_PALETTE = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"]


ACCESS_OFF = "off"


def clean_access(value):
    return value if value in ACCESS_OPTIONS else ACCESS_DEFAULT


def access_choice(value):
    """The access setting, where "off" means do not count it at all.

    Off is the default. Every extra band is another full-resolution pass over
    the region, and a large country at 100 m is already near what Earth Engine
    will do in one request.
    """
    return value if value in ACCESS_OPTIONS else ACCESS_OFF


def access_label(minutes):
    if minutes >= 60 and minutes % 60 == 0:
        hours = minutes // 60
        return f"Over {hours} hour{'s' if hours > 1 else ''} away"
    return f"Over {minutes} min away"


# Hazards that need selfMask (0 = transparent)
SELF_MASK_HAZARDS = [
]

ADMIN_DATA = {
    "adm0 (Country)": {
        "name_prop":   "name",
        "level": 0,
    },
    "adm1 (Provinces/States)": {
        "name_prop":   "name",
        "level": 1,
    },
    "adm2 (Districts/Counties)": {
        "name_prop":   "name",
        "level": 2,
    },
}

MHC_OPTIONS = [str(i) for i in range(1, len(HAZARD_TOPICS) + 1)]

# Informational text shown in the hazard info popup.
#
# Every layer states how it was built and where it falls short, because the
# counts drawn from these layers get read as risk figures. Keep `rule`,
# `temporal_basis` and `known_gaps` filled in for anything new: a layer with no
# stated limits reads as if it has none.
HAZARD_INFO = {
    "population_worldpop_2020": {
        "description": "Estimated residential population per 100 m grid cell, with totals constrained to UN population estimates. Children are the under-18 age bands, with 15-19 counted at three fifths.",
        "units": "People per grid cell",
        "availability": "2020",
        "native_resolution": "100 m at the equator",
        "temporal_basis": "Single year, 2020.",
        "coverage": "Global land.",
        "known_gaps": "Later WorldPop years exist upstream but are not used here. Age bands are modelled, so the under-18 split carries more uncertainty than the total.",
        "source": "WorldPop",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop_age_sex_cons_unadj",
    },
    "maximum_temperature_era5_land_2024": {
        "description": "Days during 2024 when the daily maximum 2 m air temperature went above 35 °C, from the ERA5-Land reanalysis.",
        "units": "Days",
        "availability": "2024",
        "rule": "Counts the days above 35 °C (308.15 K). A place counts as exposed once it reaches the number of days you select.",
        "native_resolution": "About 11 km",
        "temporal_basis": "Single year, 2024. This is not a return period, and it says nothing about how likely the temperature is in any other year.",
        "coverage": "Global land.",
        "known_gaps": "Counting days says how long, not how bad: a day at 35.1 °C counts the same as one at 45 °C. The threshold is also fixed worldwide, so it ignores that people adapt to their own climate. 2024 was the warmest year on record, so this reads hot against a longer baseline.",
        "source": "ECMWF ERA5-Land",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR",
    },
    "drought_pdsi_terraclimate_2024": {
        "description": "Months during 2024 when the Palmer Drought Severity Index sat below -2, the conventional mark for drought.",
        "units": "Months",
        "availability": "2024",
        "rule": "Counts the months below -2. A place counts as exposed once it reaches the number of months you select.",
        "native_resolution": "About 4 km",
        "temporal_basis": "Single year, 2024, in monthly steps. This is not a return period.",
        "coverage": "Global land.",
        "known_gaps": "Twelve readings a year is the finest this can resolve, so short droughts are invisible and the count cannot be compared directly against the daily layers. The months need not be consecutive, so three scattered dry months read the same as three in a row. PDSI is calibrated locally, which limits comparison between climates.",
        "source": "TerraClimate",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_TERRACLIMATE",
    },
    "active_fire_frequency_firms_2024": {
        "description": "Days during 2024 with at least one FIRMS active-fire detection in the cell.",
        "units": "Days",
        "availability": "2024",
        "rule": "Counts the days carrying a detection. A place counts as exposed once it reaches the number of days you select.",
        "native_resolution": "About 1 km",
        "temporal_basis": "Single year, 2024. This is not a return period.",
        "coverage": "Global.",
        "known_gaps": "FIRMS detects agricultural and land-clearing burns alongside wildfire and cannot tell them apart. Cloud cover and satellite overpass timing hide some fires, so the count is a floor rather than a total.",
        "source": "NASA FIRMS",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/FIRMS",
    },
    "under_five_share": {
        "description": "Share of the children in a cell who are under five. Shown on its own, never multiplied into the hazard figures.",
        "units": "Percent of children",
        "availability": "2020",
        "rule": "Under-fives divided by all under-18s in the same cell. Cells with no children are left blank rather than drawn as zero.",
        "native_resolution": "100 m at the equator",
        "temporal_basis": "Single year, 2020.",
        "coverage": "Global land, wherever children live.",
        "known_gaps": "This is the only part of vulnerability the app holds. Poverty, health, housing, disability and displacement are all absent, and age alone does not rank places by how badly a hazard will hurt them. WorldPop models its age bands, so the split is less certain than the population total.",
        "source": "WorldPop, age and sex bands",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop_age_sex_cons_unadj",
    },
    "travel_time_to_healthcare": {
        "description": "Motorised travel time to the nearest health facility, in minutes. Shown on its own, never multiplied into the hazard figures.",
        "units": "Minutes",
        "availability": "2019",
        "rule": "Children count as beyond care where travel time exceeds the number of minutes you select.",
        "native_resolution": "About 1 km",
        "temporal_basis": "Single year, 2019. Roads, facilities and conflict have moved since.",
        "coverage": "Global land.",
        "known_gaps": "This is whether care can be reached, not whether it can treat anyone. No global data exists on beds, staff or paediatric capability, so a reachable clinic and a functioning hospital look identical here. It assumes motorised travel, which overstates access for anyone without a vehicle, and it inherits gaps in the facility database that are largest in the places with the worst access.",
        "source": "Malaria Atlas Project (Weiss et al. 2020)",
        "source_url": "https://www.nature.com/articles/s41591-020-1059-1",
    },
    "Multi Hazard Count": {
        "description": f"How many of the {len(HAZARD_TOPICS)} hazard topics flag a pixel. The topics are counted, not weighted or scored, so two topics does not mean twice the severity of one.",
        "units": f"Topics (0-{len(HAZARD_TOPICS)})",
        "rule": "A topic counts a pixel when any of its layers lasted at least as long as you asked. Change a duration and this count changes with it.",
        "native_resolution": "Set by the coarsest layer involved, about 11 km",
        "temporal_basis": "Single year, 2024, inherited from the layers it counts.",
        "coverage": "Where all counted layers have data. A pixel one layer does not reach cannot reach the full count.",
        "known_gaps": "Each layer carries its own limits into this count, and the count hides them. Counts taken at different durations are not comparable. Three topics is a narrow basis for a multi-hazard measure.",
        "source": "Derived here from the layers above",
    },
}
