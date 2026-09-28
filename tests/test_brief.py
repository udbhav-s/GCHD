"""The region brief.

Its whole job is to carry figures somewhere else — into a document, a meeting,
a decision. So the rules it has to keep are about what travels with a number,
not about how it looks.
"""

import pytest

import brief
from config import ACCESS_OFF, HAZARD_TOPICS


def _result(**overrides):
    """An exposure result shaped like the one Earth Engine returns."""
    base = {
        "total_population": 100_000.0,
        "total_under_five": 22_000.0,
        "total_population_male": 51_000.0,
        "total_population_female": 49_000.0,
        "_view": {
            "durations": {},
            "period": "observed",
            "frequency": 1,
            "access": ACCESS_OFF,
        },
    }
    for topic in HAZARD_TOPICS:
        key = brief._safe_key(topic)
        base[topic] = 40_000.0
        base["cov_" + key] = 1.0
        base["u5_" + topic] = 9_000.0
    base.update(overrides)
    return base


def test_no_result_gives_no_brief():
    assert brief.build(None, "Somewhere", "adm2") is None


def test_the_region_and_level_are_stated():
    out = brief.build(_result(), "Bang Rak", "adm2 (Districts/Counties)")
    assert out["region"] == "Bang Rak"
    assert "adm2" in out["admin_level"]


def test_an_unnamed_region_is_still_labelled():
    out = brief.build(_result(), None, "adm2")
    assert out["region"]


def test_hazards_are_ranked_worst_first():
    topics = list(HAZARD_TOPICS)
    result = _result(**{topics[0]: 10_000.0, topics[1]: 90_000.0})
    out = brief.build(result, "R", "adm1")
    counts = [row["children"] for row in out["hazards"]]
    assert counts == sorted(counts, reverse=True)


def test_a_hazard_without_coverage_is_not_ranked_as_zero():
    """Ranking it as zero would put a region the data misses beside one the
    hazard genuinely spares."""
    topic = list(HAZARD_TOPICS)[0]
    result = _result(**{"cov_" + brief._safe_key(topic): 0.0, topic: 0.0})
    out = brief.build(result, "R", "adm1")
    assert topic in out["no_data_hazards"]
    assert topic not in [row["topic"] for row in out["hazards"]]


def test_absent_figures_read_as_absent():
    assert brief.format_number(None) == brief.NOT_AVAILABLE
    assert brief.format_share(None) == brief.NOT_AVAILABLE
    assert brief.format_number(0) == "0"


def test_access_is_absent_rather_than_zero_when_it_was_not_counted():
    out = brief.build(_result(), "R", "adm2")
    assert out["beyond_care"] is None


def test_access_is_reported_when_it_was_counted():
    result = _result(beyond_care=1_234.0)
    result["_view"]["access"] = 60
    out = brief.build(result, "R", "adm2")
    assert out["beyond_care"] == 1234


def test_a_region_with_no_children_has_no_share_rather_than_zero():
    out = brief.build(_result(total_population=0.0, total_under_five=0.0), "R", "adm2")
    assert out["under_five_share"] is None
    assert all(row["share"] is None for row in out["hazards"])


def test_every_brief_states_the_conditions_behind_its_figures():
    out = brief.build(_result(), "R", "adm2")
    assert out["conditions"]
    joined = " ".join(out["conditions"]).lower()
    for topic in HAZARD_TOPICS:
        assert topic.lower() in joined


def test_the_observed_period_is_named_as_a_single_year():
    out = brief.build(_result(), "R", "adm2")
    assert any("2024" in line for line in out["conditions"])


def test_the_typical_period_states_its_baselines():
    result = _result()
    result["_view"]["period"] = "typical"
    result["_view"]["frequency"] = 3
    out = brief.build(result, "R", "adm2")
    joined = " ".join(out["conditions"])
    assert "typical year" in joined.lower()
    assert "1991" in joined and "2020" in joined


def test_every_brief_says_what_it_cannot_tell_you():
    out = brief.build(_result(), "R", "adm2")
    joined = " ".join(out["missing"]).lower()
    assert "poverty" in joined
    assert "beds" in joined or "staff" in joined


def test_a_single_year_brief_says_so_in_its_limits():
    out = brief.build(_result(), "R", "adm2")
    assert any("single-year" in line.lower() for line in out["missing"])


def test_not_counting_access_is_listed_as_a_gap():
    out = brief.build(_result(), "R", "adm2")
    assert any("access" in line.lower() for line in out["missing"])


def test_every_source_carries_a_date_and_a_resolution():
    out = brief.build(_result(), "R", "adm2")
    assert out["sources"]
    for source in out["sources"]:
        assert source["as_of"]
        assert source["resolution"]
        assert source["source"]


def test_sources_list_travel_time_only_when_it_was_used():
    from config import ACCESS_LAYER

    without = brief.build(_result(), "R", "adm2")
    assert ACCESS_LAYER not in [s["layer"] for s in without["sources"]]

    result = _result(beyond_care=1.0)
    result["_view"]["access"] = 60
    with_access = brief.build(result, "R", "adm2")
    assert ACCESS_LAYER in [s["layer"] for s in with_access["sources"]]


def test_under_fives_are_carried_per_hazard():
    out = brief.build(_result(), "R", "adm2")
    assert all("under_five" in row for row in out["hazards"])


def test_case_studies_are_capped_so_the_brief_stays_short():
    out = brief.build(_result(), "R", "adm2", case_studies=[{"id": n} for n in range(20)])
    assert len(out["case_studies"]) <= 5


def test_the_page_names_itself_a_screening_aid_not_a_risk_assessment():
    html = brief.to_html(brief.build(_result(), "Bang Rak", "adm2"))
    assert "screening aid" in html
    assert "not a risk assessment" in html


def test_the_page_carries_conditions_limits_and_sources():
    html = brief.to_html(brief.build(_result(), "R", "adm2"))
    for heading in ("How these figures were counted", "What this cannot tell you", "Sources"):
        assert heading in html


def test_regions_a_hazard_misses_are_not_printed_as_zero():
    topic = list(HAZARD_TOPICS)[0]
    result = _result(**{"cov_" + brief._safe_key(topic): 0.0, topic: 0.0})
    html = brief.to_html(brief.build(result, "R", "adm2"))
    assert "These are not zero" in html


def test_region_names_cannot_inject_markup():
    html = brief.to_html(brief.build(_result(), "<script>alert(1)</script>", "adm2"))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_an_empty_brief_does_not_render_a_page():
    assert "No region selected" in brief.to_html(None)
