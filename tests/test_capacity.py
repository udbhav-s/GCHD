"""Travel time to care: the third construct, kept apart from the other two.

It measures whether a facility can be reached, not whether it can treat a
child. No global data says the second thing, so nothing here may imply it.
"""

import pytest

import config
from config import ACCESS_OFF, ACCESS_OPTIONS, access_choice, access_label, clean_access


def test_counting_access_is_off_by_default():
    """Each extra band is another full-resolution pass, and a whole country at
    100 m is already near what Earth Engine will do in one request."""
    assert access_choice(None) == ACCESS_OFF
    assert access_choice("nonsense") == ACCESS_OFF


def test_a_real_choice_is_kept():
    for minutes in ACCESS_OPTIONS:
        assert access_choice(minutes) == minutes


def test_the_off_state_is_not_a_number_of_minutes():
    """Otherwise 'off' would quietly become a threshold."""
    assert ACCESS_OFF not in ACCESS_OPTIONS
    assert not isinstance(ACCESS_OFF, int)


def test_a_stale_threshold_falls_back_rather_than_being_honoured():
    assert clean_access(9999) == config.ACCESS_DEFAULT


def test_options_are_ascending_and_plausible_travel_times():
    assert ACCESS_OPTIONS == sorted(set(ACCESS_OPTIONS))
    assert all(0 < minutes <= 24 * 60 for minutes in ACCESS_OPTIONS)


@pytest.mark.parametrize("minutes", ACCESS_OPTIONS)
def test_labels_say_the_direction_of_the_threshold(minutes):
    """'60 minutes' alone does not say whether it means nearer or further."""
    assert "over" in access_label(minutes).lower()


def test_hours_read_as_hours():
    assert access_label(60) == "Over 1 hour away"
    assert access_label(120) == "Over 2 hours away"


def test_the_layer_carries_its_limits():
    info = config.HAZARD_INFO[config.ACCESS_LAYER]
    for field in ("rule", "temporal_basis", "coverage", "known_gaps"):
        assert info.get(field)


def test_the_description_refuses_to_claim_capacity():
    """Reachable is not the same as able to treat anyone. If this admission
    goes, the layer starts reading as health-system capacity."""
    gaps = config.HAZARD_INFO[config.ACCESS_LAYER]["known_gaps"].lower()
    assert "beds" in gaps or "staff" in gaps


def test_capacity_has_its_own_colours():
    assert config.CAPACITY_PALETTE not in (
        config.VULNERABILITY_PALETTE,
        *config.HAZARD_VIS_PALETTES.values(),
    )


def test_capacity_is_not_counted_as_a_hazard():
    every_hazard = {n for names in config.HAZARD_TOPICS.values() for n in names}
    assert config.ACCESS_LAYER not in every_hazard
    assert config.ACCESS_LAYER not in config.HAZARD_MAP


def test_the_three_constructs_stay_separate():
    """Hazard, vulnerability and capacity each have their own layer name. A
    single combined score would need a weighting this app cannot defend."""
    assert len({config.ACCESS_LAYER, config.UNDER_FIVE_LAYER}) == 2
    assert config.ACCESS_LAYER not in config.HAZARD_TOPICS
