# =============================================================================
# exposure_math.py — the arithmetic behind child population counts.
# No Earth Engine import, so this can be tested without credentials.
# =============================================================================

from config import CHILD_AGE_BANDS, CHILD_PARTIAL_BAND, CHILD_PARTIAL_FRACTION


def child_band_weights(
    age_bands=CHILD_AGE_BANDS,
    partial_band=CHILD_PARTIAL_BAND,
    partial_fraction=CHILD_PARTIAL_FRACTION,
):
    """Return the weight each WorldPop age band contributes to the under-18 count.

    Bands that sit entirely below 18 count whole. The 15-19 band straddles the
    cutoff, so it counts at a fraction.
    """
    if partial_band in age_bands:
        raise ValueError(
            f"band {partial_band!r} is listed as both a whole band and the partial band"
        )
    weights = {band: 1.0 for band in age_bands}
    weights[partial_band] = float(partial_fraction)
    return weights


def child_population_from_bands(band_values, weights=None):
    """Add up one sex's age bands into a child total.

    band_values maps a band name to the people in it. This is the same sum the
    Earth Engine path runs per pixel, written so it can be checked directly.
    """
    weights = child_band_weights() if weights is None else weights
    missing = [band for band in weights if band not in band_values]
    if missing:
        raise KeyError(f"missing age bands: {', '.join(sorted(missing))}")
    return sum(band_values[band] * weight for band, weight in weights.items())
