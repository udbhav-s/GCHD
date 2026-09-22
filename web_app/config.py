# =============================================================================
# config.py — Static configuration: hazards, topics, colors, admin levels
# No GEE imports here so this loads instantly.
# =============================================================================
#
# Only the layers this fork runs appear here. Colours, palettes and info text
# for the wider GCHD hazard catalogue used to sit alongside them with no code
# behind them, which made the app look like it covered hazards it does not.
# Git history has them if a layer arrives.

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
        "reducer": "max",
        "threshold": 308.15,
        "direction": "gt",
        "vis_min": 273.15,
        "vis_max": 323.15,
    },
    {
        "id": "IDAHO_EPSCOR/TERRACLIMATE",
        "name": "drought_pdsi_terraclimate_2024",
        "kind": "collection",
        "band": "pdsi",
        "start": "2024-01-01",
        "end": "2025-01-01",
        "reducer": "min",
        "scale_factor": 0.01,
        "threshold": -2,
        "direction": "lt",
        "vis_min": -6,
        "vis_max": 6,
    },
    {
        "id": "FIRMS",
        "name": "active_fire_frequency_firms_2024",
        "kind": "collection",
        "band": "T21",
        "start": "2024-01-01",
        "end": "2025-01-01",
        "reducer": "count_mask",
        "threshold": 1,
        "direction": "gte",
        "vis_min": 1,
        "vis_max": 10,
    },
]

HAZARD_MAP = {h["name"]: h for h in HAZARDS}

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

# Vis palettes per individual hazard (for map display)
HAZARD_VIS_PALETTES = {
    "population_worldpop_2020": ["#24126c", "#1fff4f", "#d4ff50"],
    "maximum_temperature_era5_land_2024": ["#313695", "#74add1", "#fdae61", "#d73027", "#7f0000"],
    "drought_pdsi_terraclimate_2024": ["#8c510a", "#d8b365", "#f6e8c3", "#c7eae5", "#01665e"],
    "active_fire_frequency_firms_2024": ["#ffffb2", "#fecc5c", "#fd8d3c", "#f03b20", "#bd0026"],
}

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
        "description": "Highest daily 2 m air temperature reached during 2024 in the ERA5-Land reanalysis.",
        "units": "Kelvin",
        "availability": "2024",
        "rule": "Flagged where the highest daily maximum in 2024 went above 35 °C (308.15 K).",
        "native_resolution": "About 11 km",
        "temporal_basis": "Single year, 2024. This is not a return period, and it says nothing about how likely the temperature is in any other year.",
        "coverage": "Global land.",
        "known_gaps": "The flag records that it happened, not how often. Across the land it flags, days above 35 °C run from 2 at the 10th percentile to 343 at the maximum, and all of them count the same. 2024 was the warmest year on record, so this reads hot against a longer baseline.",
        "source": "ECMWF ERA5-Land",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR",
    },
    "drought_pdsi_terraclimate_2024": {
        "description": "Lowest monthly Palmer Drought Severity Index value during 2024. Values below -2 indicate drought conditions.",
        "units": "PDSI",
        "availability": "2024",
        "rule": "Flagged where the lowest monthly PDSI in 2024 fell below -2.",
        "native_resolution": "About 4 km",
        "temporal_basis": "Single year, 2024, in monthly steps. This is not a return period.",
        "coverage": "Global land.",
        "known_gaps": "One dry month reads the same as a dry year, so the flag misses how long a drought lasted. PDSI is also calibrated locally, which limits comparison between climates.",
        "source": "TerraClimate",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/IDAHO_EPSCOR_TERRACLIMATE",
    },
    "active_fire_frequency_firms_2024": {
        "description": "Count of 2024 daily FIRMS active-fire detections per raster cell.",
        "units": "Detection days",
        "availability": "2024",
        "rule": "Flagged where at least one daily detection landed in the cell during 2024.",
        "native_resolution": "About 1 km",
        "temporal_basis": "Single year, 2024. This is not a return period.",
        "coverage": "Global.",
        "known_gaps": "FIRMS detects agricultural and land-clearing burns alongside wildfire and cannot tell them apart. Cloud cover and satellite overpass timing hide some fires. One detection day counts the same as a hundred.",
        "source": "NASA FIRMS",
        "source_url": "https://developers.google.com/earth-engine/datasets/catalog/FIRMS",
    },
    "Multi Hazard Count": {
        "description": f"How many of the {len(HAZARD_TOPICS)} hazard topics flag a pixel. The topics are counted, not weighted or scored, so two topics does not mean twice the severity of one.",
        "units": f"Topics (0-{len(HAZARD_TOPICS)})",
        "rule": "A topic flags a pixel when any of its layers crosses that layer's threshold.",
        "native_resolution": "Set by the coarsest layer involved, about 11 km",
        "temporal_basis": "Single year, 2024, inherited from the layers it counts.",
        "coverage": "Where all counted layers have data. A pixel one layer does not reach cannot reach the full count.",
        "known_gaps": "Each layer carries its own limits into this count, and the count hides them. Three topics is a narrow basis for a multi-hazard measure.",
        "source": "Derived here from the layers above",
    },
}
