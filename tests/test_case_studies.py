"""Case-study records: schema, hazard vocabulary, and the config they filter against."""

import json

import pytest

# 217 of the 638 records carry no hazard, so no hazard filter can reach them.
# They split into two kinds:
#
# 15 came from Climate-ADAPT with impact tokens that map to no GCHD hazard —
# European windstorm is not tropical_storm, water scarcity is a supply
# condition, and ice, extreme cold and unspecified have no layer at all. They
# keep their source_hazard_tags, so the decision stays visible.
#
# The other 202 are mostly C40 records about waste, transport and energy
# efficiency. They name no hazard because they address none.
#
# Pinned so the split cannot drift quietly. If a mapping improves, change these.
EXPECTED_EMPTY_HAZARDS = 217
EXPECTED_UNMAPPED_WITH_TAGS = 15


def test_every_record_declares_the_current_schema(case_studies):
    wrong = [p.name for p, r in case_studies if r.get("schema_version") != "2.2"]
    assert wrong == []


def test_every_record_validates(case_studies, repo_root):
    jsonschema = pytest.importorskip(
        "jsonschema", reason="jsonschema lives in scripts/requirements.txt"
    )
    schema = json.loads(
        (repo_root / "schema" / "case-study.schema.json").read_text(encoding="utf-8")
    )
    validator = jsonschema.Draft202012Validator(schema)
    failures = []
    for path, record in case_studies:
        for error in validator.iter_errors(record):
            failures.append(f"{path.name}: {'/'.join(str(p) for p in error.path)}: {error.message}")
    assert failures == []


def test_every_hazard_id_is_in_the_taxonomy(case_studies, taxonomy):
    known = set(taxonomy["hazards"])
    unknown = set()
    for _, record in case_studies:
        unknown |= set(record.get("hazards") or []) - known
    assert unknown == set()


def test_the_records_with_no_hazards_stay_that_way(case_studies):
    empty = [p.name for p, r in case_studies if not r.get("hazards")]
    assert len(empty) == EXPECTED_EMPTY_HAZARDS, (
        "the number of records no hazard filter can reach changed; if a mapping "
        "improved, update EXPECTED_EMPTY_HAZARDS"
    )


def test_records_whose_tags_did_not_map_keep_them(case_studies):
    """A record dropped by the mapping must say what it was tagged with.

    Without the tags there is no way to tell a hazard we chose not to map from
    one we lost.
    """
    kept = [
        p.name
        for p, r in case_studies
        if not r.get("hazards") and r.get("source_hazard_tags")
    ]
    assert len(kept) == EXPECTED_UNMAPPED_WITH_TAGS


def test_ids_are_unique(case_studies):
    ids = [r["id"] for _, r in case_studies]
    assert len(ids) == len(set(ids))


def test_the_filename_matches_the_record_id(case_studies):
    mismatched = [p.name for p, r in case_studies if p.stem != r["id"]]
    assert mismatched == []


def test_every_live_layer_is_reachable_from_the_taxonomy(taxonomy):
    """Selecting a hazard layer has to be able to find its case studies.

    The taxonomy covers the whole GCHD vocabulary, so it lists many layers this
    fork does not run. That is fine. What matters is the other direction: a
    layer the app does run must appear somewhere in the taxonomy, or picking it
    returns nothing and looks like an empty result rather than a broken link.
    """
    import config

    listed = {
        layer
        for entry in taxonomy["hazards"].values()
        for layer in entry.get("layers", [])
    }
    hazard_layers = {
        h["name"] for h in config.HAZARDS if h.get("threshold") is not None
    }
    assert hazard_layers <= listed


def test_every_live_topic_is_reachable_from_the_taxonomy(taxonomy):
    """Each dashboard topic needs at least one case-study hazard pointing at it,
    or the case-study filter can never select it."""
    import config

    topics = {
        entry.get("dashboard_topic")
        for entry in taxonomy["hazards"].values()
        if entry.get("dashboard_topic")
    }
    missing = set(config.HAZARD_TOPICS) - topics
    assert missing == set()


def test_locations_name_a_level_they_actually_carry(case_studies):
    for path, record in case_studies:
        for location in record.get("locations") or []:
            level = location.get("level")
            if level in ("adm0", "adm1", "adm2"):
                assert location.get(level), f"{path.name} claims {level} but carries none"
