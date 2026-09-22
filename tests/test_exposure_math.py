"""The child population sum, checked without Earth Engine.

Every exposure figure in the app is this arithmetic run per pixel, so an error
here would be invisible and would scale to every number on screen.
"""

import pytest

from config import (
    CHILD_AGE_BANDS,
    CHILD_PARTIAL_BAND,
    CHILD_PARTIAL_FRACTION,
)
from exposure_math import child_band_weights, child_population_from_bands


def test_whole_bands_count_once():
    weights = child_band_weights()
    for band in CHILD_AGE_BANDS:
        assert weights[band] == 1.0


def test_the_straddling_band_counts_at_a_fraction():
    weights = child_band_weights()
    assert weights[CHILD_PARTIAL_BAND] == CHILD_PARTIAL_FRACTION
    assert 0 < CHILD_PARTIAL_FRACTION < 1


def test_no_band_outside_the_configured_set_is_counted():
    # The WorldPop mosaic also carries a "population" band holding every age.
    # Counting it would report the whole population as children.
    weights = child_band_weights()
    assert set(weights) == set(CHILD_AGE_BANDS) | {CHILD_PARTIAL_BAND}
    assert "population" not in weights


def test_a_band_cannot_be_both_whole_and_partial():
    with pytest.raises(ValueError):
        child_band_weights(age_bands=["0", "15"], partial_band="15")


def test_sum_matches_a_hand_worked_example():
    bands = {"0": 10.0, "1": 20.0, "5": 30.0, "10": 40.0, "15": 50.0}
    expected = 10 + 20 + 30 + 40 + 50 * CHILD_PARTIAL_FRACTION
    assert child_population_from_bands(bands) == pytest.approx(expected)


def test_children_never_exceed_the_bands_they_come_from():
    bands = {band: 100.0 for band in CHILD_AGE_BANDS + [CHILD_PARTIAL_BAND]}
    total_in_bands = sum(bands.values())
    assert child_population_from_bands(bands) < total_in_bands


def test_empty_bands_give_no_children():
    bands = {band: 0.0 for band in CHILD_AGE_BANDS + [CHILD_PARTIAL_BAND]}
    assert child_population_from_bands(bands) == 0


def test_a_missing_band_is_an_error_not_a_silent_zero():
    with pytest.raises(KeyError):
        child_population_from_bands({"0": 1.0})
