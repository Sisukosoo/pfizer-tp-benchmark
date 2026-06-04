"""Tests for PLI calculation functions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.pli_calculator import (
    berry_ratio,
    operating_margin,
    roce,
    weighted_berry_ratio,
    weighted_operating_margin,
    weighted_roce,
)


def test_operating_margin_basic(sample_tested_party_df: pd.DataFrame) -> None:
    """EBIT 100 / Sales 1000 should produce 10% Operating Margin."""

    result = operating_margin(sample_tested_party_df, "Last avail. yr")

    assert result.iloc[0] == pytest.approx(0.10)


def test_weighted_operating_margin_handles_zero_sales() -> None:
    """Weighted Operating Margin should return NaN when sales denominator is zero."""

    dataframe = pd.DataFrame(
        {
            "Sales th EUR Last avail. yr": [0.0],
            "Operating profit (loss) [EBIT] th EUR Last avail. yr": [10.0],
        }
    )

    result = weighted_operating_margin(dataframe, ["Last avail. yr"])

    assert np.isnan(result.iloc[0])


def test_berry_ratio_basic(sample_tested_party_df: pd.DataFrame) -> None:
    """Gross profit 300 / derived operating expenses 200 should produce 1.5x."""

    result = berry_ratio(sample_tested_party_df, "Last avail. yr")

    assert result.iloc[0] == pytest.approx(1.5)


def test_weighted_berry_ratio_basic(sample_tested_party_df: pd.DataFrame) -> None:
    """Weighted Berry Ratio should use summed numerator and denominator."""

    result = weighted_berry_ratio(
        sample_tested_party_df,
        ["Last avail. yr", "Year - 1", "Year - 2"],
    )

    assert result.iloc[0] == pytest.approx(1.5)


def test_roce_normalizes_percentage_points(
    sample_tested_party_df: pd.DataFrame,
) -> None:
    """Orbis ROCE stored as 10.0 percentage points should become a 0.10 ratio."""

    result = roce(sample_tested_party_df, "Last avail. yr")

    assert result.iloc[0] == pytest.approx(0.10)


def test_roce_small_value_is_not_treated_as_a_ratio() -> None:
    """A genuinely small ROCE of 0.8 percentage points must become 0.008.

    This is a regression test for the previous heuristic that skipped dividing
    values with absolute magnitude <= 1 and misread 0.8 (0.8%) as 0.8 (80%).
    """

    dataframe = pd.DataFrame({"ROCE using P/L before tax Last avail. yr": [0.8]})

    result = roce(dataframe, "Last avail. yr")

    assert result.iloc[0] == pytest.approx(0.008)


def test_roce_handles_negative_percentage_points() -> None:
    """A negative ROCE of -5.0 percentage points should become -0.05."""

    dataframe = pd.DataFrame({"ROCE using P/L before tax Last avail. yr": [-5.0]})

    result = roce(dataframe, "Last avail. yr")

    assert result.iloc[0] == pytest.approx(-0.05)


def test_weighted_roce_averages_yearly_values(
    sample_tested_party_df: pd.DataFrame,
) -> None:
    """Weighted ROCE should average the normalized yearly ROCE observations."""

    result = weighted_roce(
        sample_tested_party_df,
        ["Last avail. yr", "Year - 1", "Year - 2"],
    )

    assert result.iloc[0] == pytest.approx(0.11)
