"""Smoke tests for the Orbis data loader."""

from __future__ import annotations

import pytest

from src import config
from src.data_loader import load_comparables, load_tested_party


def test_load_tested_party_smoke() -> None:
    """Load the tested-party export if present and validate basic fields."""

    if not config.TESTED_PARTY_PATH.exists():
        pytest.skip("Tested-party Orbis export not present in data/raw/.")

    dataframe = load_tested_party()

    assert len(dataframe) == 1
    assert dataframe.loc[0, config.LATEST_REVENUE_COLUMN] > 0
    assert "pfizer" in dataframe.loc[0, config.COMPANY_NAME_COLUMN].lower()


def test_load_synthetic_demo_data() -> None:
    """Synthetic demo data should be committed and loadable without Orbis files."""

    tested_party = load_tested_party(config.DATA_MODE_SYNTHETIC)
    comparables = load_comparables(config.DATA_MODE_SYNTHETIC)

    assert len(tested_party) == 1
    assert len(comparables) == 55
    assert "demo" in tested_party.loc[0, config.COMPANY_NAME_COLUMN].lower()
