"""Pytest configuration for project tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

from src import config

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_tested_party_df() -> pd.DataFrame:
    """Return a small synthetic tested-party DataFrame."""

    return pd.DataFrame(
        {
            config.COMPANY_NAME_COLUMN: ["TESTED PARTY"],
            config.COUNTRY_COLUMN: ["Germany"],
            "Sales th EUR Last avail. yr": [1_000.0],
            "Sales th EUR Year - 1": [1_100.0],
            "Sales th EUR Year - 2": [1_200.0],
            "Operating profit (loss) [EBIT] th EUR Last avail. yr": [100.0],
            "Operating profit (loss) [EBIT] th EUR Year - 1": [110.0],
            "Operating profit (loss) [EBIT] th EUR Year - 2": [120.0],
            "Material costs th EUR Last avail. yr": [700.0],
            "Material costs th EUR Year - 1": [770.0],
            "Material costs th EUR Year - 2": [840.0],
            "Gross profit th EUR Last avail. yr": [300.0],
            "Gross profit th EUR Year - 1": [330.0],
            "Gross profit th EUR Year - 2": [360.0],
            "ROCE using P/L before tax Last avail. yr": [10.0],
            "ROCE using P/L before tax Year - 1": [11.0],
            "ROCE using P/L before tax Year - 2": [12.0],
        }
    )


@pytest.fixture
def sample_comparables_df() -> pd.DataFrame:
    """Return a small synthetic comparable-company DataFrame."""

    rows = []
    for index, margin in enumerate([0.04, 0.05, 0.06], start=1):
        sales = 1_000.0
        ebit = sales * margin
        material_costs = 700.0
        gross_profit = sales - material_costs
        rows.append(
            {
                config.COMPANY_NAME_COLUMN: f"Comparable {index}",
                config.COUNTRY_COLUMN: "Italy",
                config.TRADE_DESCRIPTION_COLUMN: "Wholesale of pharmaceuticals",
                config.LATEST_REVENUE_COLUMN: sales,
                config.LATEST_EMPLOYEES_COLUMN: 100.0,
                "Sales th EUR Last avail. yr": sales,
                "Sales th EUR Year - 1": sales,
                "Sales th EUR Year - 2": sales,
                "Operating profit (loss) [EBIT] th EUR Last avail. yr": ebit,
                "Operating profit (loss) [EBIT] th EUR Year - 1": ebit,
                "Operating profit (loss) [EBIT] th EUR Year - 2": ebit,
                "Material costs th EUR Last avail. yr": material_costs,
                "Material costs th EUR Year - 1": material_costs,
                "Material costs th EUR Year - 2": material_costs,
                "Gross profit th EUR Last avail. yr": gross_profit,
                "Gross profit th EUR Year - 1": gross_profit,
                "Gross profit th EUR Year - 2": gross_profit,
                "ROCE using P/L before tax Last avail. yr": margin * 100,
                "ROCE using P/L before tax Year - 1": margin * 100,
                "ROCE using P/L before tax Year - 2": margin * 100,
            }
        )
    return pd.DataFrame(rows)
