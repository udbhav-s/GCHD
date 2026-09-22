"""Guards on what the app tells people about its own data.

The app lost credibility once by describing a hazard count as a PCA-derived
intensity score. These tests hold the descriptions to the code.
"""

import config


PROVENANCE_FIELDS = ["native_resolution", "temporal_basis", "coverage", "known_gaps"]


def test_every_layer_the_app_shows_has_an_info_entry():
    layers = {h["name"] for h in config.HAZARDS}
    assert layers <= set(config.HAZARD_INFO)


def test_no_info_entry_describes_a_layer_that_does_not_exist():
    """An entry with no layer behind it reads as a hazard the app covers."""
    derived = {"Multi Hazard Count"}
    layers = {h["name"] for h in config.HAZARDS}
    orphans = set(config.HAZARD_INFO) - layers - derived
    assert orphans == set()


def test_every_info_entry_states_its_limits():
    missing = []
    for name, info in config.HAZARD_INFO.items():
        for field in PROVENANCE_FIELDS:
            if not info.get(field):
                missing.append(f"{name}.{field}")
    assert missing == []


def test_thresholded_layers_say_how_they_flag():
    for hazard in config.HAZARDS:
        if hazard.get("threshold") is None:
            continue
        info = config.HAZARD_INFO[hazard["name"]]
        assert info.get("rule"), f"{hazard['name']} has a threshold but does not state it"


def test_single_year_layers_do_not_claim_a_return_period():
    for hazard in config.HAZARDS:
        if hazard.get("kind") != "collection":
            continue
        basis = config.HAZARD_INFO[hazard["name"]]["temporal_basis"].lower()
        assert "not a return period" in basis


def test_palettes_and_colors_only_cover_what_runs():
    layers = {h["name"] for h in config.HAZARDS}
    assert set(config.HAZARD_VIS_PALETTES) <= layers
    assert set(config.SELF_MASK_HAZARDS) <= layers
    assert set(config.TOPIC_COLORS) - {"Multi Hazard Count"} == set(config.HAZARD_TOPICS)


def test_the_count_options_cannot_exceed_the_topics_available():
    assert config.MHC_OPTIONS == [str(i) for i in range(1, len(config.HAZARD_TOPICS) + 1)]


def test_no_percentile_control_survives_on_the_hazard_count():
    """The old intensity control thresholded percentiles of a three-valued count,
    so several of its options drew the same map. It must not come back."""
    assert not hasattr(config, "MHI_OPTIONS")


def test_every_topic_names_layers_that_exist():
    for topic, names in config.HAZARD_TOPICS.items():
        for name in names:
            assert name in config.HAZARD_MAP, f"{topic} names an unknown layer {name}"
