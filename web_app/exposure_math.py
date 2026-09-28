# =============================================================================
# exposure_math.py — the arithmetic behind child population counts.
# No Earth Engine import, so this can be tested without credentials.
# =============================================================================

from config import (
    CHILD_AGE_BANDS,
    CHILD_PARTIAL_BAND,
    CHILD_PARTIAL_FRACTION,
    UNDER_FIVE_BANDS,
)


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


def under_five_band_weights(bands=UNDER_FIVE_BANDS):
    """Weights for the under-five count.

    Both bands sit entirely below five, so neither is split. This is a subset of
    the under-18 weights, which is what makes the share meaningful.
    """
    return {band: 1.0 for band in bands}


def under_five_share(band_values):
    """Under-fives as a fraction of all children in the same cell.

    Returns None where no children live, rather than zero. A place with no
    children has no age structure, and reporting 0% would put it at the safe
    end of the scale alongside places that genuinely skew older.
    """
    children = child_population_from_bands(band_values)
    if children <= 0:
        return None
    return child_population_from_bands(band_values, under_five_band_weights()) / children


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
