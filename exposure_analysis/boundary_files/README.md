# Boundary Files

## Administrative Boundaries

GCHD uses UNICEF's harmonised administrative boundary layers hosted as Google Earth Engine assets.

| Level | Description | Default GEE Asset | Chunked Asset (batch processing) |
|---|---|---|---|
| ADM0 | Country boundaries (229 countries and territories) | `projects/unicef-ccri/assets/global_boundary/adm0` | `projects/unicef-ccri/assets/global_boundary/adm0_chunked` |
| ADM1 | First sub-national level | `projects/unicef-ccri/assets/global_boundary/adm1` | `projects/unicef-ccri/assets/global_boundary/adm1_chunked` |
| ADM2 | Second sub-national level | `projects/unicef-ccri/assets/global_boundary/adm2` | `projects/unicef-ccri/assets/global_boundary/adm2_chunked` |

The default asset is used for standard processing. The chunked variant splits boundaries into smaller tiles for enhanced batch processing performance in Google Earth Engine.

## Coverage

229 countries and territories, including 195 UN member states and 34 territories.

## Source

Boundaries are derived from UNICEF's internal harmonised boundary dataset, aligned with UN cartographic standards.

## Notes

- Palestine (PSE) and Nicaragua (NIC) are retained in the output with analytical values set to null.
- All sovereign states and territories are included even where hazard or population data is unavailable.
