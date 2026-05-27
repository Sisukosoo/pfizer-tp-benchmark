"""Tests for PLI calculation functions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.pli_calculator import (
    berry_ratio,
    operating_margin,
    weighted_berry_ratio,
    weighted_operating_margin,
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
