"""Arm's-length range and tested-party positioning calculations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from src import config
from src.pli_calculator import calculate_weighted_pli, yearly_pli_table


def arms_length_range(comparables_pli: pd.Series) -> dict[str, float | int]:
    """Calculate the interquartile arm's-length range.

    Quartiles use `numpy.percentile` with the method configured in
    `config.QUARTILE_METHOD` (`linear` by default).

    Args:
        comparables_pli: Comparable-company PLI observations.

    Returns:
        Range statistics including min, Q1, median, Q3, max, and IQR width.
    """

    valid_values = pd.to_numeric(comparables_pli, errors="coerce").dropna()
    if valid_values.empty:
        return {
            "n": 0,
            "min": math.nan,
            "q1": math.nan,
            "median": math.nan,
            "q3": math.nan,
            "max": math.nan,
            "iqr_width": math.nan,
        }

    minimum, q1, median, q3, maximum = np.percentile(
        valid_values.to_numpy(dtype=float),
        [0, 25, 50, 75, 100],
        method=config.QUARTILE_METHOD,
    )
    return {
        "n": int(len(valid_values)),
        "min": float(minimum),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "max": float(maximum),
        "iqr_width": float(q3 - q1),
    }


def position_tested_party(
    tested_pli: float,
    range_dict: dict[str, float | int],
) -> dict[str, float | str]:
    """Position the tested party relative to the interquartile range.

    Args:
        tested_pli: Tested-party PLI.
        range_dict: Output from `arms_length_range`.

    Returns:
        Positioning metadata and adjustment direction.
    """

    q1 = float(range_dict["q1"])
    median = float(range_dict["median"])
    q3 = float(range_dict["q3"])

    if math.isnan(tested_pli) or math.isnan(q1) or math.isnan(q3):
        return {
            "tested_pli": tested_pli,
            "position": "not_available",
            "distance_to_range": math.nan,
            "adjustment_direction": "none",
            "adjustment_to_median": math.nan,
            "adjustment_to_q1": math.nan,
            "adjustment_to_q3": math.nan,
        }

    if tested_pli < q1:
        return {
            "tested_pli": tested_pli,
            "position": "below_q1",
            "distance_to_range": tested_pli - q1,
            "adjustment_direction": "upward",
            "adjustment_to_median": median - tested_pli,
            "adjustment_to_q1": q1 - tested_pli,
            "adjustment_to_q3": 0.0,
        }

    if tested_pli > q3:
        return {
            "tested_pli": tested_pli,
            "position": "above_q3",
            "distance_to_range": tested_pli - q3,
            "adjustment_direction": "downward",
            "adjustment_to_median": median - tested_pli,
            "adjustment_to_q1": 0.0,
            "adjustment_to_q3": q3 - tested_pli,
        }

    return {
        "tested_pli": tested_pli,
        "position": "within_range",
        "distance_to_range": 0.0,
        "adjustment_direction": "none",
        "adjustment_to_median": median - tested_pli,
        "adjustment_to_q1": 0.0,
        "adjustment_to_q3": 0.0,
    }


def run_benchmark(
    tested_party_df: pd.DataFrame,
    comparables_df: pd.DataFrame,
    pli_type: str = config.PLI_OPERATING_MARGIN,
    years: list[str] | None = None,
) -> dict[str, Any]:
    """Run the full TNMM benchmark for one PLI and period.

    Args:
        tested_party_df: Tested-party Orbis data.
        comparables_df: Accepted comparable-company Orbis data.
        pli_type: PLI type to calculate.
        years: Relative Orbis year suffixes to include.

    Returns:
        Dictionary containing tested-party PLI, comparable PLIs, range, position,
        and detail tables.
    """

    benchmark_years = years or config.DEFAULT_BENCHMARK_PERIOD
    tested_pli_series = calculate_weighted_pli(
        tested_party_df,
        pli_type,
        benchmark_years,
    )
    comparables_pli = calculate_weighted_pli(
        comparables_df,
        pli_type,
        benchmark_years,
    )

    if config.COMPANY_NAME_COLUMN in comparables_df.columns:
        comparables_pli.index = comparables_df[config.COMPANY_NAME_COLUMN].astype(str)

    tested_pli = (
        float(tested_pli_series.iloc[0]) if not tested_pli_series.empty else math.nan
    )
    range_dict = arms_length_range(comparables_pli)
    position = position_tested_party(tested_pli, range_dict)
    comparables_detail = _build_comparables_detail(
        comparables_df,
        comparables_pli,
        range_dict,
    )

    return {
        "pli_type": pli_type,
        "pli_label": config.PLI_LABELS.get(pli_type, pli_type),
        "years": benchmark_years,
        "period_label": _period_label(benchmark_years),
        "tested_pli": tested_pli,
        "comparables_pli": comparables_pli,
        "range": range_dict,
        "position": position,
        "comparables_detail": comparables_detail,
        "yearly_comparables_pli": yearly_pli_table(
            comparables_df,
            pli_type,
            benchmark_years,
        ),
        "yearly_tested_pli": yearly_pli_table(
            tested_party_df,
            pli_type,
            benchmark_years,
        ),
    }


def _build_comparables_detail(
    comparables_df: pd.DataFrame,
    comparables_pli: pd.Series,
    range_dict: dict[str, float | int],
) -> pd.DataFrame:
    """Build a transparent comparable-company result table."""

    display_columns = [
        column
        for column in [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            config.LATEST_REVENUE_COLUMN,
            config.LATEST_EMPLOYEES_COLUMN,
            config.TRADE_DESCRIPTION_COLUMN,
        ]
        if column in comparables_df.columns
    ]
    detail = comparables_df[display_columns].copy()
    detail["weighted_pli"] = comparables_pli.to_numpy()
    q1 = float(range_dict["q1"])
    q3 = float(range_dict["q3"])
    detail["valid_for_range"] = detail["weighted_pli"].notna()
    detail["inside_iqr"] = detail["weighted_pli"].between(q1, q3, inclusive="both")
    return detail.sort_values("weighted_pli", ascending=False, na_position="last")


def _period_label(years: list[str]) -> str:
    """Format a compact benchmark-period label."""

    labels = [config.PERIOD_LABELS.get(year, year) for year in years]
    return ", ".join(labels)
