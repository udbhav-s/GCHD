"""The boundary cache: coverage, nesting, and lookups.

ADM2 was silently empty once, which made every district-level case study draw
its province instead. These tests catch that shape of failure.
"""

import sqlite3

import pytest

# A good build from one export vintage. Recorded so a half-built or mixed cache
# is visible rather than quietly wrong.
EXPECTED_COUNTS = {0: 289, 1: 3578, 2: 41092}


@pytest.fixture(scope="module")
def connection(boundaries_db):
    conn = sqlite3.connect(boundaries_db)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


def _count(connection, level):
    return connection.execute(
        "SELECT count(*) AS n FROM boundaries WHERE level = ?", (level,)
    ).fetchone()["n"]


@pytest.mark.parametrize("level", [0, 1, 2])
def test_every_level_is_populated(connection, level):
    assert _count(connection, level) > 0


@pytest.mark.parametrize("level, expected", sorted(EXPECTED_COUNTS.items()))
def test_counts_match_a_known_good_build(connection, level, expected):
    assert _count(connection, level) == expected


def test_every_country_has_districts(connection):
    countries = _count(connection, 0)
    with_districts = connection.execute(
        "SELECT count(DISTINCT adm0_ucode) AS n FROM boundaries WHERE level = 2"
    ).fetchone()["n"]
    assert with_districts == countries


def test_districts_name_a_parent_that_exists(connection):
    orphans = connection.execute(
        """
        SELECT count(*) AS n FROM boundaries child
        WHERE child.level = 2
          AND child.adm1_ucode IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM boundaries parent
            WHERE parent.level = 1 AND parent.ucode = child.adm1_ucode
          )
        """
    ).fetchone()["n"]
    assert orphans == 0


# The country outlines are simplified more heavily than the district ones, so a
# district edge can sit a little outside its country's box without anything
# being wrong. The worst case in a good build is about 0.022°, roughly 2 km.
# This tolerance leaves that alone and still catches a district filed under the
# wrong country, which would be off by degrees.
BBOX_TOLERANCE_DEGREES = 0.1


@pytest.mark.parametrize("level", [1, 2])
def test_units_sit_inside_their_country_bounds(connection, level):
    outside = connection.execute(
        """
        SELECT count(*) AS n FROM boundaries child
        JOIN boundaries country
          ON country.level = 0 AND country.ucode = child.adm0_ucode
        WHERE child.level = ?
          AND (child.minx < country.minx - ?
            OR child.maxx > country.maxx + ?
            OR child.miny < country.miny - ?
            OR child.maxy > country.maxy + ?)
        """,
        (level,) + (BBOX_TOLERANCE_DEGREES,) * 4,
    ).fetchone()["n"]
    assert outside == 0


def test_ucodes_are_unique(connection):
    duplicates = connection.execute(
        "SELECT count(*) AS n FROM (SELECT ucode FROM boundaries GROUP BY ucode HAVING count(*) > 1)"
    ).fetchone()["n"]
    assert duplicates == 0


def test_a_district_lookup_round_trips(boundaries_db):
    import georepo_core

    georepo_core.get_feature_by_ucode.cache_clear()
    result = georepo_core.get_feature_by_ucode("THA_0056_0005_V1", level=2)
    assert result is not None
    assert result["ucode"] == "THA_0056_0005_V1"
    assert result["name"]
    assert result["feature"]["geometry"]["type"] in ("Polygon", "MultiPolygon")


def test_a_point_resolves_to_the_district_that_contains_it(boundaries_db):
    import georepo_core

    ucode, name = georepo_core.get_feature_at_point(100.5018, 13.7563, 2, "THA_V1")
    assert ucode is not None
    assert name
