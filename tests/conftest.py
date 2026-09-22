"""Shared paths and fixtures. Puts web_app on the import path."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_APP = REPO_ROOT / "web_app"

if str(WEB_APP) not in sys.path:
    sys.path.insert(0, str(WEB_APP))


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def case_studies():
    """Every case-study record, as (path, parsed json)."""
    paths = sorted((REPO_ROOT / "case_studies").glob("*.json"))
    if not paths:
        pytest.skip("no case studies found")
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in paths]


@pytest.fixture(scope="session")
def taxonomy():
    return json.loads(
        (REPO_ROOT / "schema" / "hazard-taxonomy.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="session")
def boundaries_db():
    """The local boundary cache, or a skip if this machine has not built one.

    The cache is 50 MB and gitignored, so it exists only where someone has run
    scripts/build_georepo_cache.py.
    """
    import georepo_core

    if not Path(georepo_core.DB_PATH).exists():
        pytest.skip("boundary cache not built on this machine")
    return georepo_core.DB_PATH
