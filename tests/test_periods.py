"""The two periods, and how often a hazard has to recur.

2024 says what happened. The typical year says how often a year like it turned
up. Mixing the two, or letting a baseline go unstated, is how a single bad year
gets read as a normal one.
"""

import pytest

import config
from config import (
    DURATION_HAZARDS,
    FREQUENCY_DEFAULT,
    FREQUENCY_OPTIONS,
    PERIOD_DEFAULT,
    PERIOD_LABELS,
    PERIOD_OPTIONS,
    baseline_label,
    baseline_window,
    baseline_years,
    clean_frequency,
    clean_period,
    frequency_label,
)

# FIRMS begins in November 2000 and ERA5-Land in 1950, so the layers cannot
# share a baseline. Pinned because silently widening fire's window would be
# comparing a satellite era against one that has no satellites in it.
EXPECTED_WINDOWS = {
    "maximum_temperature_era5_land_2024": (1991, 2020),
    "drought_pdsi_terraclimate_2024": (1991, 2020),
    "active_fire_frequency_firms_2024": (2001, 2024),
}


def test_the_default_period_is_the_observed_year():
    """Opening on a modelled baseline would present a derived figure as the
    plain fact of what happened."""
    assert PERIOD_DEFAULT == "observed"


def test_both_periods_have_a_label():
    assert set(PERIOD_LABELS) == set(PERIOD_OPTIONS)
    assert all(PERIOD_LABELS[p].strip() for p in PERIOD_OPTIONS)


def test_an_unknown_period_falls_back():
    assert clean_period("2050") == PERIOD_DEFAULT
    assert clean_period(None) == PERIOD_DEFAULT


def test_an_unknown_frequency_falls_back():
    assert clean_frequency(99) == FREQUENCY_DEFAULT
    assert clean_frequency(None) == FREQUENCY_DEFAULT


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_baselines_match_what_the_sources_can_support(hazard):
    assert baseline_window(hazard) == EXPECTED_WINDOWS[hazard["name"]]


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_a_baseline_is_long_enough_to_say_anything_about_frequency(hazard):
    """Fewer than ten years cannot support a claim stated per ten years."""
    assert baseline_years(hazard) >= 10


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_a_baseline_does_not_run_past_its_source(hazard):
    start, end = baseline_window(hazard)
    assert start < end
    assert end <= 2024, "TerraClimate stops at December 2024; nothing may claim later"


def test_the_layers_do_not_share_one_baseline():
    """If they ever do, the interface copy explaining why they differ is stale."""
    assert config.baseline_windows_differ()


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_the_window_is_stated_in_full(hazard):
    label = baseline_label(hazard)
    start, end = baseline_window(hazard)
    assert str(start) in label and str(end) in label


def test_frequency_is_expressed_per_ten_years():
    """Windows are 30 and 24 years long. A raw count of qualifying years would
    not be comparable between them."""
    for value in FREQUENCY_OPTIONS:
        assert "10" in frequency_label(value)


def test_frequency_options_are_reachable_within_ten():
    assert all(1 <= value <= 10 for value in FREQUENCY_OPTIONS)
    assert FREQUENCY_OPTIONS == sorted(set(FREQUENCY_OPTIONS))


def test_the_default_frequency_is_the_loosest():
    assert FREQUENCY_DEFAULT == min(FREQUENCY_OPTIONS)


def test_nothing_claims_a_return_period():
    """Thirty years of record cannot support a one-in-a-hundred statement."""
    banned = ("return period", "1-in-", "100-year", "100 year")
    text = " ".join(
        str(value).lower()
        for info in config.HAZARD_INFO.values()
        for key, value in info.items()
        if key != "temporal_basis"  # that field exists to deny return periods
    )
    for phrase in banned:
        assert phrase not in text, f"a layer claims {phrase!r}"
