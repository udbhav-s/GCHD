"""Colour has to rise with the count.

The layers draw how long a hazard lasted. A ramp that lightens as the count
rises would put the worst places in the same colour as the safest ones.
"""

import pytest

import config


def _luminance(hex_colour):
    r = int(hex_colour[1:3], 16)
    g = int(hex_colour[3:5], 16)
    b = int(hex_colour[5:7], 16)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


DURATION_LAYERS = [h["name"] for h in config.DURATION_HAZARDS]


@pytest.mark.parametrize("name", DURATION_LAYERS)
def test_the_ramp_darkens_as_the_count_rises(name):
    palette = config.HAZARD_VIS_PALETTES[name]
    assert _luminance(palette[0]) > _luminance(palette[-1]), (
        f"{name} draws high counts lighter than low ones, so more hazard reads as less"
    )


@pytest.mark.parametrize("name", DURATION_LAYERS)
def test_the_ramp_does_not_turn_back_on_itself(name):
    """A diverging ramp against a count sends the extremes to similar colours."""
    values = [_luminance(c) for c in config.HAZARD_VIS_PALETTES[name]]
    assert values == sorted(values, reverse=True), (
        f"{name} brightens somewhere along its ramp, which reads as a reversal"
    )


@pytest.mark.parametrize("name", DURATION_LAYERS)
def test_the_scale_starts_at_no_occurrences(name):
    """Zero steps is drawn transparent, so the ramp has to begin there or the
    first visible colour already means something other than what it shows."""
    assert config.HAZARD_MAP[name]["vis_min"] == 0


@pytest.mark.parametrize("name", DURATION_LAYERS)
def test_the_top_of_the_scale_is_reachable(name):
    """A ceiling above what the source can report leaves the ramp's dark end
    unused, which is how the old intensity layer hid its own range."""
    hazard = config.HAZARD_MAP[name]
    steps_per_year = {"days": 366, "months": 12}[hazard["duration_unit"]]
    assert 0 < hazard["vis_max"] <= steps_per_year
