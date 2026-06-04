"""Tests for reusable Plotly visualization helpers."""

from __future__ import annotations

import pandas as pd

from src import config
from src.benchmarking import ArmsLengthRange
from src.visualizations import (
    revenue_vs_margin_scatter,
    sensitivity_range_plot,
    sorted_comparables_bar,
)
from src.visualizations import (
    tested_party_trend_plot as build_tested_party_trend_plot,
)


def test_tested_party_trend_plot_has_reported_and_adjusted_traces() -> None:
    """Trend chart should include reported and adjusted observations."""

    figure = build_tested_party_trend_plot(
        pd.Series({"FY 2022": 0.02, "FY 2023": 0.04, "FY 2024": 0.05}),
        adjusted_points={"FY 2022": 0.06},
    )

    assert len(figure.data) == 2
    assert figure.data[0].name == "Reported OM"


def test_sorted_comparables_bar_adds_pfizer_reference_line(
    sample_comparables_df: pd.DataFrame,
) -> None:
    """Sorted bar chart should include bars and reference shapes."""

    detail = sample_comparables_df[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            config.LATEST_REVENUE_COLUMN,
            config.LATEST_EMPLOYEES_COLUMN,
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ].copy()
    detail["weighted_pli"] = [0.04, 0.05, 0.06]
    figure = sorted_comparables_bar(
        detail,
        tested_pli=0.055,
        range_result=ArmsLengthRange(
            n=3,
            min=0.04,
            q1=0.045,
            median=0.05,
            q3=0.055,
            max=0.06,
            iqr_width=0.01,
        ),
    )

    assert len(figure.data) == 1
    assert len(figure.layout.shapes) == 5


def test_sensitivity_range_plot_builds_scenario_markers() -> None:
    """Sensitivity plot should include Q1, Q3, and Pfizer marker traces."""

    summary = pd.DataFrame(
        {
            "Group": ["Period", "Period"],
            "Scenario": ["Base", "Exclude FY22"],
            "PLI": ["Operating Margin", "Operating Margin"],
            "Tested PLI": [0.04, 0.06],
            "Q1": [0.01, 0.02],
            "Median": [0.03, 0.04],
            "Q3": [0.05, 0.05],
        }
    )

    figure = sensitivity_range_plot(summary)

    assert len(figure.data) == 3
    assert len(figure.layout.shapes) == 2


def test_revenue_vs_margin_scatter_includes_pfizer_marker(
    sample_comparables_df: pd.DataFrame,
) -> None:
    """Revenue scatter should show comparable observations and Pfizer."""

    detail = sample_comparables_df[
        [
            config.COMPANY_NAME_COLUMN,
            config.LATEST_REVENUE_COLUMN,
        ]
    ].copy()
    detail["weighted_pli"] = [0.04, 0.05, 0.06]

    figure = revenue_vs_margin_scatter(
        detail,
        tested_revenue_eur_k=1_594_207.0,
        tested_pli=0.0415,
    )

    assert len(figure.data) == 2
    assert figure.data[1].name == "Pfizer Pharma GmbH"
