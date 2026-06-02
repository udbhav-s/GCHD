# =============================================================================
# config.py — Static configuration: hazards, topics, colors, admin levels
# No GEE imports here so this loads instantly.
# =============================================================================

HAZARDS = [
    {"id": "projects/unicef-ccri/assets/hazards/river_flood_r100",               "threshold": 0.01,       "name": "river_flood_100yr_jrc_2024"},
    {"id": "projects/unicef-ccri/assets/hazards/coastal_flood_r100",             "threshold": 0,          "name": "coastal_flood_100yr_jrc_2024"},
    {"id": "projects/unicef-ccri/assets/hazards/storm_giri_rp100",               "threshold": 17.5,       "name": "tropical_storm_100yr_giri_2024"},
    {"id": "projects/unicef-ccri/assets/hazards/ASI_return_level_100yr",         "threshold": 30,         "name": "agricultural_drought_fao_1984-2023"},
    {"id": "projects/unicef-ccri/assets/droughts/spei12_TerraClimate_1958-2025", "band": "b2", "threshold": 0.0650162152126539, "name": "drought_spei_terraclimate_1958-2025"},
    {"id": "projects/unicef-ccri/assets/droughts/spi12_TerraClimate_1958-2025",  "band": "b2", "threshold": 0.0912838950900999, "name": "drought_spi_terraclimate_1958-2025"},
    {"id": "projects/unicef-ccri/assets/hazards/heatwave_frequency_return_level_100yr", "threshold": 16.02, "name": "heatwave_frequency_ecmwf_2014-2024"},
    {"id": "projects/unicef-ccri/assets/hazards/heatwave_duration_return_level_100yr",  "threshold": 94.01, "name": "heatwave_duration_ecmwf_2014-2024"},
    {"id": "projects/unicef-ccri/assets/hazards/heatwave_severity_return_level_100yr",  "threshold": 3.66,  "name": "heatwave_severity_ecmwf_2014-2024"},
    {"id": "projects/unicef-ccri/assets/hazards/high_temp_degree_days_return_level_100yr", "threshold": 35, "name": "extreme_heat_ecmwf_2014-2024"},
    {"id": "projects/unicef-ccri/assets/hazards/FIRMS_FRP_90th_percentile",      "threshold": 37.89,      "name": "fire_FRP_nasa_2001-2024"},
    {"id": "projects/unicef-ccri/assets/hazards/FIRMS_count_90th_percentile",    "threshold": 4.91,       "name": "fire_frequency_nasa_2001-2023"},
    {"id": "projects/unicef-ccri/assets/hazards/sand_dust_storm_annual",         "threshold": 0,          "name": "sand_dust_storm_unccd_2024",          "isImage": True},
    {"id": "projects/unicef-ccri/assets/hazards/pm25_p90_1998_2023",             "threshold": 5,          "name": "air_pollution_pm25_1998-2023"},
    {"id": "projects/unicef-ccri/assets/hazards/Pv_average_2013_2022",           "threshold": 0.001,      "name": "vectorborne_malariapv_2012-2022"},
    {"id": "projects/unicef-ccri/assets/hazards/Pf_average_2013_2022",           "threshold": 0.001,      "name": "vectorborne_malariapf_2012-2022"},
    {"id": "projects/unicef-ccri/assets/hazards/MHI_climate",                    "threshold": 6.516479,   "name": "Pixel Based Hazard Score"},
]

HAZARD_MAP = {h["name"]: h for h in HAZARDS}

HAZARD_TOPICS = {
    "River Flood":        ["river_flood_100yr_jrc_2024"],
    "Coastal Flood":      ["coastal_flood_100yr_jrc_2024"],
    "Tropical Storm":     ["tropical_storm_100yr_giri_2024"],
    "Drought":            ["agricultural_drought_fao_1984-2023", "drought_spei_terraclimate_1958-2025", "drought_spi_terraclimate_1958-2025"],
    "Heatwave":           ["heatwave_frequency_ecmwf_2014-2024", "heatwave_duration_ecmwf_2014-2024", "heatwave_severity_ecmwf_2014-2024"],
    "Extreme Heat":       ["extreme_heat_ecmwf_2014-2024"],
    "Fire":               ["fire_FRP_nasa_2001-2024", "fire_frequency_nasa_2001-2023"],
    "Sand and Dust Storm":["sand_dust_storm_unccd_2024"],
    "Air Pollution":      ["air_pollution_pm25_1998-2023"],
    "Malaria":            ["vectorborne_malariapv_2012-2022", "vectorborne_malariapf_2012-2022"],
}

# Topics that show sub-hazard breakdown in the results panel
SUB_TOPIC_DETAIL = ["Malaria", "Heatwave", "Fire", "Drought"]

ALLOW_NEGATIVE = []  # TerraClimate droughts now use positive probability thresholds

TOPIC_COLORS = {
    "River Flood":         "#1f78b4",
    "Coastal Flood":       "#a6cee3",
    "Tropical Storm":      "#33a02c",
    "Drought":             "#ff7f00",
    "Heatwave":            "#e31a1c",
    "Extreme Heat":        "#6a3d9a",
    "Fire":                "#fb9a99",
    "Sand and Dust Storm": "#b15928",
    "Air Pollution":       "#cab2d6",
    "Malaria":             "#b2df8a",
    "Multi Hazard Count":  "#800026",
    "Multi Hazard Intensity": "#c63a26",
}

# Vis palettes per individual hazard (for map display)
HAZARD_VIS_PALETTES = {
    "river_flood_100yr_jrc_2024":       ["#cfe8ff", "#8fcbff", "#1d7bff", "#0654be", "#00357d"],
    "coastal_flood_100yr_jrc_2024":     ["#ffffff", "#084081"],
    "tropical_storm_100yr_giri_2024":   ["#e4eff2", "#c3dce7", "#9ebdd2", "#7e8ab0", "#6d6c91"],
    "agricultural_drought_fao_1984-2023": ["#fdf4cb", "#fbd992", "#f3b431", "#c66216", "#843d09"],
    "drought_spei_terraclimate_1958-2025": ["#fdf4cb", "#fbd992", "#f3b431", "#c66216", "#843d09"],
    "drought_spi_terraclimate_1958-2025":  ["#fdf4cb", "#fbd992", "#f3b431", "#c66216", "#843d09"],
    "heatwave_frequency_ecmwf_2014-2024": ["#f8e593", "#f8cc14", "#F89800", "#F86800", "#F83000"],
    "heatwave_duration_ecmwf_2014-2024":  ["#f8e593", "#f8cc14", "#F89800", "#F86800", "#F83000"],
    "heatwave_severity_ecmwf_2014-2024":  ["#f8e593", "#f8cc14", "#F89800", "#F86800", "#F83000"],
    "extreme_heat_ecmwf_2014-2024":     ["#f8e593", "#f8cc14", "#F89800", "#F86800", "#F83000"],
    "fire_FRP_nasa_2001-2024":          ["#F0F0DC", "#FFD282", "#FF8C3C", "#DC3C1E", "#5A0000"],
    "fire_frequency_nasa_2001-2023":    ["#F0F0DC", "#FFD282", "#FF8C3C", "#DC3C1E", "#5A0000"],
    "sand_dust_storm_unccd_2024":       ["#faf0dc", "#e6d2b4", "#c8aa82", "#a0785a", "#261f28"],
    "air_pollution_pm25_1998-2023":     ["#d0dde5", "#99a1b4", "#7c6e87", "#5a4b5e", "#261f27"],
    "vectorborne_malariapv_2012-2022":  ["#e8f0e3", "#bcd4b4", "#8ba889", "#607c66", "#35503d"],
    "vectorborne_malariapf_2012-2022":  ["#e8f0e3", "#bcd4b4", "#8ba889", "#607c66", "#35503d"],
}

# Hazards that need selfMask (0 = transparent)
SELF_MASK_HAZARDS = [
    "tropical_storm_100yr_giri_2024",
    "coastal_flood_100yr_jrc_2024",
    "heatwave_frequency_ecmwf_2014-2024",
    "heatwave_duration_ecmwf_2014-2024",
    "heatwave_severity_ecmwf_2014-2024",
]

ADMIN_DATA = {
    "adm0 (Country)": {
        "asset":       "projects/unicef-ccri/assets/global_boundary/admin0_regions_merged",
        "name_prop":   "name",
        "chunk_asset": "projects/unicef-ccri/assets/global_boundary/adm0_chunked_500km_shp",
    },
    "adm1 (Provinces/States)": {
        "asset":       "projects/unicef-ccri/assets/global_boundary/adm1",
        "name_prop":   "name",
        "chunk_asset": "projects/unicef-ccri/assets/global_boundary/adm1_chunked_500km_shp",
    },
    "adm2 (Districts/Counties)": {
        "asset":       "projects/unicef-ccri/assets/global_boundary/adm2",
        "name_prop":   "name",
        "chunk_asset": "projects/unicef-ccri/assets/global_boundary/adm2_chunked_500km_shp",
    },
}

GLOBAL_GEOMETRY = [[-180, 90], [-180, -90], [180, -90], [180, 90]]

MHC_OPTIONS = [str(i) for i in range(1, len(HAZARD_TOPICS) + 1)]
MHI_OPTIONS  = ["75", "80", "85", "90", "95"]

# Informational text shown in the hazard info popup
# Each entry: description, units, source (from CCRR Internal Data Catalog - Indicators tab)
HAZARD_INFO = {
    "river_flood_100yr_jrc_2024": {
        "description": "A fluvial or riverine flood is a rise, usually brief, in the water level of a stream or water body to a peak from which the water level recedes at a slower rate.",
        "units": "Depth in m",
        "source": "JRC",
        "source_url": "https://global-flood-maps.jrc.ec.europa.eu/",
    },
    "coastal_flood_100yr_jrc_2024": {
        "description": "Coastal flooding is most frequently the result of storm surges and high winds coinciding with high tides.",
        "units": "Binary",
        "source": "JRC",
        "source_url": "https://global-flood-maps.jrc.ec.europa.eu/",
    },
    "tropical_storm_100yr_giri_2024": {
        "description": "A tropical storm is a type of storm system characterized by a low-pressure center, a closed low-level atmospheric circulation, strong winds, and a spiral arrangement of thunderstorms that produce heavy rain.",
        "units": "Wind speed in m/s",
        "source": "GIRI",
        "source_url": "https://www.undrr.org/",
    },
    "agricultural_drought_fao_1984-2023": {
        "description": "Agricultural drought occurs when there is insufficient soil moisture to meet the needs of a particular crop at a particular time.",
        "units": "Agricultural Stress Index (%)",
        "availability": "1984–2023",
        "source": "FAO",
        "source_url": "https://www.fao.org/giews/earthobservation/",
    },
    "drought_spi_terraclimate_1958-2025": {
        "description": "SPI measures the deviation of precipitation from the climatological average over a given accumulation period and is widely used to detect and characterize meteorological droughts. Probability values are computed from the full 1958–2025 record (804 monthly time steps).",
        "units": "Index",
        "availability": "1958–present",
        "source": "TerraClimate",
        "source_url": "https://www.climatologylab.org/terraclimate.html",
    },
    "drought_spei_terraclimate_1958-2025": {
        "description": "SPEI adds the effect of evapotranspiration and is better suited to assess droughts under climate change scenarios where temperature changes are important. Probability values are computed from the full 1958–2025 record (804 monthly time steps).",
        "units": "Index",
        "availability": "1958–present",
        "source": "TerraClimate",
        "source_url": "https://www.climatologylab.org/terraclimate.html",
    },
    "heatwave_frequency_ecmwf_2014-2024": {
        "description": "A heatwave can be defined as a period where local excess heat accumulates over a sequence of unusually hot days and nights. Heatwave frequency refers to the number of heatwaves per year.",
        "units": "Times per year",
        "availability": "2014–2024",
        "source": "ECMWF",
        "source_url": "https://www.ecmwf.int/",
    },
    "heatwave_duration_ecmwf_2014-2024": {
        "description": "A heatwave can be defined as a period where local excess heat accumulates over a sequence of unusually hot days and nights. Heatwave duration refers to the total number of days an event lasts.",
        "units": "Number of days",
        "availability": "2014–2024",
        "source": "ECMWF",
        "source_url": "https://www.ecmwf.int/",
    },
    "heatwave_severity_ecmwf_2014-2024": {
        "description": "A heatwave can be defined as a period where local excess heat accumulates over a sequence of unusually hot days and nights. Heatwave severity refers to the temperature above the local 15-day average during the heatwave, expressed in degrees Celsius.",
        "units": "Temperature in °C",
        "availability": "2014–2024",
        "source": "ECMWF",
        "source_url": "https://www.ecmwf.int/",
    },
    "extreme_heat_ecmwf_2014-2024": {
        "description": "Extremely high temperatures (extremely hot days) are estimated when a day exceeds 35 degrees Celsius.",
        "units": "Number of days over 35°C",
        "availability": "2014–2024",
        "source": "ECMWF",
        "source_url": "https://www.ecmwf.int/",
    },
    "fire_FRP_nasa_2001-2024": {
        "description": "Wildfires are uncontrolled burns of vegetation, including forests, shrublands, grasslands, savannas, and croplands. Fire Radiative Power (FRP) is a measure of the energy released by a fire in the form of radiation.",
        "units": "MW",
        "availability": "2001–2023",
        "source": "NASA FIRMS",
        "source_url": "https://firms.modaps.eosdis.nasa.gov/",
    },
    "fire_frequency_nasa_2001-2023": {
        "description": "Wildfires are uncontrolled burns of vegetation, including forests, shrublands, grasslands, savannas, and croplands. Fire frequency is obtained from NASA's Fire Information for Resource Management System (FIRMS) and is used as a proxy for fire hazard.",
        "units": "km⁻² · yr⁻¹",
        "availability": "2001–2023",
        "source": "NASA FIRMS",
        "source_url": "https://firms.modaps.eosdis.nasa.gov/",
    },
    "sand_dust_storm_unccd_2024": {
        "description": "Sand and dust storms (SDS) are caused by intense winds over areas of arid soil that pick up large amounts of ground material into the atmosphere.",
        "units": "Index",
        "source": "UNCCD",
        "source_url": "https://www.unccd.int/",
    },
    "air_pollution_pm25_1998-2023": {
        "description": "Air pollution refers to the presence of substances in the atmosphere that are harmful to human health and the environment. Fine particle air pollution (PM2.5) refers to airborne particles measuring less than 2.5 micrometers in diameter emitted from vehicles, fuel use, power plants, agriculture, waste burning, wildfires, and other sources.",
        "units": "PM2.5 in μg/m³",
        "availability": "2012–2022",
        "source": "ACAG",
        "source_url": "https://sites.wustl.edu/acag/",
    },
    "vectorborne_malariapv_2012-2022": {
        "description": "P. vivax is the dominant malaria parasite in most countries outside of sub-Saharan Africa. Malaria is a life-threatening disease caused by parasites transmitted to humans through the bites of infected female Anopheles mosquitoes.",
        "units": "Persons",
        "availability": "2012–2022",
        "source": "MAP",
        "source_url": "https://malariaatlas.org/",
    },
    "vectorborne_malariapf_2012-2022": {
        "description": "Malaria is a life-threatening disease caused by parasites transmitted to humans through the bites of infected female Anopheles mosquitoes. P. falciparum is the deadliest malaria parasite and the most prevalent on the African continent.",
        "units": "Persons",
        "availability": "2012–2022",
        "source": "MAP",
        "source_url": "https://malariaatlas.org/",
    },
    "Multi Hazard Count": {
        "description": "Combined count of hazard types exceeding their respective thresholds at each pixel.",
        "units": "Count",
        "source": "UNICEF Children's Climate Risk Report 2026",
        "source_url": "https://www.unicef.org/reports/climate-crisis-child-rights-crisis",
    },
    "Multi Hazard Intensity": {
        "description": "Combined hazard count and intensity score across all hazard types.",
        "units": "Score",
        "source": "UNICEF Children's Climate Risk Report 2026",
        "source_url": "https://www.unicef.org/reports/climate-crisis-child-rights-crisis",
    },
}
