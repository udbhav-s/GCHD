"""End-to-end exposure for one district, against recorded figures.

Marked slow: it needs network and Earth Engine credentials. Run it with
`pytest -m slow`. The unit tests cover the arithmetic; this one catches the
wiring around it — wrong band names, a broken mask, a boundary that stopped
resolving.

Figures recorded 2026-09-21 from Bang Rak, Bangkok (THA_0056_0005_V1) against
WorldPop 2020 and the 2024 hazard layers. They change when a layer, threshold
or population year changes, and that is the point: re-record deliberately.
"""

import pytest

pytestmark = pytest.mark.slow

UCODE = "THA_0056_0005_V1"
ADMIN_LEVEL = "adm2 (Districts/Counties)"

EXPECTED = {
    "total_population": 191663.83,
    "total_population_male": 96398.48,
    "total_population_female": 95265.35,
    "Extreme Heat": 155497.06,
    "Drought": 191663.83,
    "Fire": 15048.59,
}

RELATIVE_TOLERANCE = 1e-3


@pytest.fixture(scope="module")
def stats():
    import gee_core

    try:
        gee_core.initialize_gee()
    except Exception as exc:
        pytest.skip(f"Earth Engine unavailable: {exc}")
    result = gee_core.compute_exposure(UCODE, ADMIN_LEVEL, mhc_value="1")
    if result is None:
        pytest.skip("boundary cache does not hold the test district")
    return result


@pytest.mark.parametrize("key, expected", sorted(EXPECTED.items()))
def test_figures_match_what_was_recorded(stats, key, expected):
    assert stats[key] == pytest.approx(expected, rel=RELATIVE_TOLERANCE)


def test_the_sexes_add_up_to_the_total(stats):
    total = stats["total_population_male"] + stats["total_population_female"]
    assert total == pytest.approx(stats["total_population"], rel=RELATIVE_TOLERANCE)


def test_no_topic_exposes_more_children_than_live_there(stats):
    from config import HAZARD_TOPICS

    for topic in HAZARD_TOPICS:
        assert stats[topic] <= stats["total_population"] * (1 + RELATIVE_TOLERANCE)


def test_the_count_filter_never_exceeds_the_population(stats):
    assert stats["active_count_filter"] <= stats["total_population"] * (1 + RELATIVE_TOLERANCE)


def test_asking_for_a_longer_spell_never_raises_exposure():
    """Requiring more days cannot add children. If it does, the duration is
    being applied in the wrong direction."""
    import gee_core
    from gee_core import durations_key

    try:
        gee_core.initialize_gee()
    except Exception as exc:
        pytest.skip(f"Earth Engine unavailable: {exc}")

    heat = "maximum_temperature_era5_land_2024"
    previous = None
    for minimum in (1, 7, 30):
        result = gee_core.compute_exposure(
            UCODE, ADMIN_LEVEL, durations=durations_key({heat: minimum})
        )
        if result is None:
            pytest.skip("boundary cache does not hold the test district")
        current = result["Extreme Heat"]
        if previous is not None:
            assert current <= previous * (1 + RELATIVE_TOLERANCE), (
                f"exposure rose when the minimum went to {minimum} days"
            )
        previous = current


def test_the_duration_control_actually_changes_something():
    """Bang Rak sees 29 to 41 days above 35 C, so a 30-day minimum has to cut
    the figure. A control that never moves a number is worse than none."""
    import gee_core
    from gee_core import durations_key

    try:
        gee_core.initialize_gee()
    except Exception as exc:
        pytest.skip(f"Earth Engine unavailable: {exc}")

    heat = "maximum_temperature_era5_land_2024"
    loose = gee_core.compute_exposure(UCODE, ADMIN_LEVEL, durations=durations_key({heat: 1}))
    tight = gee_core.compute_exposure(UCODE, ADMIN_LEVEL, durations=durations_key({heat: 30}))
    if loose is None or tight is None:
        pytest.skip("boundary cache does not hold the test district")
    assert tight["Extreme Heat"] < loose["Extreme Heat"]


def test_a_typical_year_is_not_more_exposed_than_a_bad_one():
    """2024 was the warmest year on record. Requiring the same conditions in
    several years out of ten cannot find more children than 2024 alone did."""
    import gee_core
    from gee_core import durations_key

    try:
        gee_core.initialize_gee()
    except Exception as exc:
        pytest.skip(f"Earth Engine unavailable: {exc}")

    heat = "maximum_temperature_era5_land_2024"
    key = durations_key({heat: 30})
    observed = gee_core.compute_exposure(UCODE, ADMIN_LEVEL, durations=key, period="observed")
    typical = gee_core.compute_exposure(
        UCODE, ADMIN_LEVEL, durations=key, period="typical", frequency=3
    )
    if observed is None or typical is None:
        pytest.skip("boundary cache does not hold the test district")
    assert typical["Extreme Heat"] <= observed["Extreme Heat"] * (1 + RELATIVE_TOLERANCE)


def test_demanding_a_hazard_more_often_never_finds_more_children():
    import gee_core
    from gee_core import durations_key

    try:
        gee_core.initialize_gee()
    except Exception as exc:
        pytest.skip(f"Earth Engine unavailable: {exc}")

    heat = "maximum_temperature_era5_land_2024"
    key = durations_key({heat: 30})
    previous = None
    for frequency in (1, 3, 5):
        result = gee_core.compute_exposure(
            UCODE, ADMIN_LEVEL, durations=key, period="typical", frequency=frequency
        )
        if result is None:
            pytest.skip("boundary cache does not hold the test district")
        current = result["Extreme Heat"]
        if previous is not None:
            assert current <= previous * (1 + RELATIVE_TOLERANCE), (
                f"exposure rose when the requirement went to {frequency} years in 10"
            )
        previous = current


def test_under_fives_are_counted_and_never_exceed_the_children(stats):
    """The share is a subset, so it cannot be larger than the whole."""
    assert stats["total_under_five"] > 0
    assert stats["total_under_five"] <= stats["total_population"] * (1 + RELATIVE_TOLERANCE)


def test_each_topic_reports_its_own_under_fives(stats):
    from config import HAZARD_TOPICS

    for topic in HAZARD_TOPICS:
        exposed_children = stats[topic]
        exposed_under_five = stats["u5_" + topic]
        assert exposed_under_five <= exposed_children * (1 + RELATIVE_TOLERANCE), (
            f"{topic} reports more under-fives than children"
        )
        assert exposed_under_five <= stats["total_under_five"] * (1 + RELATIVE_TOLERANCE)
