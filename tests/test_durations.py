"""How long a hazard must last before a place counts as exposed.

The layers used to answer "did this ever happen", which made one hot day and a
hot year identical. These guard the duration model that replaced it.
"""

import pytest

import config
from config import (
    DURATION_HAZARDS,
    clean_durations,
    default_durations,
    duration_label,
)


def test_every_hazard_layer_offers_a_duration():
    """A layer without one silently falls back to counting any occurrence."""
    layers = [h for h in config.HAZARDS if h.get("threshold") is not None]
    assert {h["name"] for h in layers} == {h["name"] for h in DURATION_HAZARDS}


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_the_default_is_an_offered_option(hazard):
    assert hazard["duration_default"] in hazard["duration_options"]


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_options_are_ascending_and_start_at_any(hazard):
    options = hazard["duration_options"]
    assert options == sorted(set(options))
    assert options[0] == 1, "the loosest option has to be reachable"


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_a_duration_cannot_exceed_the_steps_the_source_reports(hazard):
    """Asking for 30 months of a layer with 12 readings a year would select
    nothing and look like an absence of hazard."""
    steps_per_year = {"days": 365, "months": 12}[hazard["duration_unit"]]
    assert max(hazard["duration_options"]) <= steps_per_year


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_the_unit_is_one_the_interface_can_label(hazard):
    assert hazard["duration_unit"] in ("days", "months")


def test_monthly_and_daily_layers_are_not_given_the_same_options():
    """Units are deliberately not normalised. If drought ever carries the same
    options as the daily layers, someone has flattened that difference."""
    by_unit = {}
    for hazard in DURATION_HAZARDS:
        by_unit.setdefault(hazard["duration_unit"], set()).add(
            tuple(hazard["duration_options"])
        )
    if len(by_unit) > 1:
        assert len(set.union(*by_unit.values())) > 1


def test_defaults_reproduce_counting_any_occurrence():
    """The default has to match the old behaviour, or every published figure
    moved the day this shipped."""
    assert all(value == 1 for value in default_durations().values())


def test_an_unoffered_choice_falls_back_rather_than_being_honoured():
    cleaned = clean_durations({"maximum_temperature_era5_land_2024": 999})
    assert cleaned["maximum_temperature_era5_land_2024"] == 1


def test_an_unknown_hazard_is_dropped():
    cleaned = clean_durations({"a_layer_that_does_not_exist": 7})
    assert "a_layer_that_does_not_exist" not in cleaned


def test_missing_choices_are_filled_in():
    assert clean_durations({}) == default_durations()
    assert clean_durations(None) == default_durations()


def test_every_hazard_is_answered_even_when_one_is_given():
    cleaned = clean_durations({"maximum_temperature_era5_land_2024": 30})
    assert set(cleaned) == {h["name"] for h in DURATION_HAZARDS}
    assert cleaned["maximum_temperature_era5_land_2024"] == 30


@pytest.mark.parametrize("hazard", DURATION_HAZARDS, ids=lambda h: h["name"])
def test_labels_name_the_unit(hazard):
    for value in hazard["duration_options"]:
        label = duration_label(hazard, value)
        assert hazard["duration_unit"][:-1] in label, f"{label} hides its unit"


def test_the_loosest_label_does_not_read_as_a_number_of_steps():
    hazard = DURATION_HAZARDS[0]
    assert "any" in duration_label(hazard, 1).lower()


def test_descriptions_say_the_layer_counts_rather_than_flags():
    for hazard in DURATION_HAZARDS:
        info = config.HAZARD_INFO[hazard["name"]]
        assert "count" in info["rule"].lower(), (
            f"{hazard['name']} still describes itself as flagging a single event"
        )
        assert info["units"].lower() in ("days", "months")
