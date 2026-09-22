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
