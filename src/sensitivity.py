"""Sensitivity scenarios for the TNMM benchmark."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src import config
from src.benchmarking import run_benchmark

PERIOD_SCENARIOS = {
    "2-year weighted (FY23-FY24)": ["Last avail. yr", "Year - 1"],
    "3-year weighted (FY22-FY24, base)": config.DEFAULT_BENCHMARK_PERIOD,
    "4-year weighted (FY21-FY24)": [
        "Last avail. yr",
        "Year - 1",
        "Year - 2",
        "Year - 3",
    ],
    "5-year weighted (FY20-FY24)": list(config.YEAR_SUFFIXES),
    "3-year excluding FY22": ["Last avail. yr", "Year - 1", "Year - 3"],
}

POOL_SCENARIOS = {
    "All 10 comparables": [],
    "Exclude smallest comparable (MICERIUM)": ["MICERIUM S.P.A."],
    "Exclude two smallest (MICERIUM, BB FARMA)": ["MICERIUM S.P.A.", "BB FARMA SRL"],
    "Exclude largest comparable (TEDIS)": ["TEDIS"],
    "Exclude Italian regional distributors": [
        "UFM - UNIONE FARMACEUTICA MITO S.R.L.",
        "CLUB SALUTE S.P.A.",
        "SAIMA S.P.A.",
        "ALCYON ITALIA S.P.A.",
        "BB FARMA SRL",
        "MICERIUM S.P.A.",
    ],
}


def normalize_pfizer_fy22_ebit(tested_party_df: pd.DataFrame) -> pd.DataFrame:
    """Return tested-party data with FY22 EBIT adjusted for restructuring.

    Args:
        tested_party_df: Tested-party Orbis data.

    Returns:
        Copy of tested-party data with Year - 2 EBIT increased by the
        restructuring charge value configured in `src.config`.
    """

    adjusted = tested_party_df.copy()
    fy22_ebit_column = f"{config.EBIT_COLUMN_PREFIX} Year - 2"
    if fy22_ebit_column in adjusted.columns:
        adjusted[fy22_ebit_column] = (
            pd.to_numeric(adjusted[fy22_ebit_column], errors="coerce")
            + config.PFIZER_FY22_RESTRUCTURING_CHARGE_EUR_K
        )
    return adjusted


def run_all_scenarios(
    tested_party_df: pd.DataFrame,
    comparables_df: pd.DataFrame,
    include_fy22_adjustment: bool = False,
) -> list[dict[str, Any]]:
    """Run period, PLI, outlier, and optional tested-party adjustment scenarios.

    Args:
        tested_party_df: Tested-party Orbis data.
        comparables_df: Accepted comparable-company data.
        include_fy22_adjustment: Whether to include the FY22 EBIT normalization.

    Returns:
        List of scenario records containing benchmark outputs.
    """

    scenarios: list[dict[str, Any]] = []
    for scenario_name, years in PERIOD_SCENARIOS.items():
        scenarios.append(
            _scenario(
                group="Period",
                name=scenario_name,
                tested_party_df=tested_party_df,
                comparables_df=comparables_df,
                pli_type=config.PLI_OPERATING_MARGIN,
                years=years,
            )
        )

    for pli_type in config.PLI_OPTIONS:
        scenarios.append(
            _scenario(
                group="PLI",
                name=f"{config.PLI_LABELS[pli_type]} ({_base_period_label()})",
                tested_party_df=tested_party_df,
                comparables_df=comparables_df,
                pli_type=pli_type,
                years=config.DEFAULT_BENCHMARK_PERIOD,
            )
        )

    for scenario_name, excluded_names in POOL_SCENARIOS.items():
        scenario_comparables = _exclude_companies(comparables_df, excluded_names)
        scenarios.append(
            _scenario(
                group="Comparable pool",
                name=scenario_name,
                tested_party_df=tested_party_df,
                comparables_df=scenario_comparables,
                pli_type=config.PLI_OPERATING_MARGIN,
                years=config.DEFAULT_BENCHMARK_PERIOD,
            )
        )

    if include_fy22_adjustment:
        scenarios.append(
            _scenario(
                group="Tested party adjustment",
                name="Normalize Pfizer FY22 EBIT for restructuring charge",
                tested_party_df=normalize_pfizer_fy22_ebit(tested_party_df),
                comparables_df=comparables_df,
                pli_type=config.PLI_OPERATING_MARGIN,
                years=config.DEFAULT_BENCHMARK_PERIOD,
            )
        )

    return scenarios


def scenario_summary_frame(scenarios: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert scenario outputs into a Streamlit-friendly summary table.

    Args:
        scenarios: Scenario records from `run_all_scenarios`.

    Returns:
        Summary DataFrame with tested PLI, range, and position.
    """

    rows = []
    for scenario in scenarios:
        result = scenario["result"]
        range_dict = result["range"]
        position = result["position"]
        rows.append(
            {
                "Group": scenario["group"],
                "Scenario": scenario["name"],
                "PLI": result["pli_label"],
                "N": range_dict["n"],
                "Tested PLI": result["tested_pli"],
                "Q1": range_dict["q1"],
                "Median": range_dict["median"],
                "Q3": range_dict["q3"],
                "Position": position["position"],
            }
        )
    return pd.DataFrame(rows)


def _scenario(
    group: str,
    name: str,
    tested_party_df: pd.DataFrame,
    comparables_df: pd.DataFrame,
    pli_type: str,
    years: list[str],
) -> dict[str, Any]:
    """Run one benchmark scenario."""

    return {
        "group": group,
        "name": name,
        "result": run_benchmark(
            tested_party_df=tested_party_df,
            comparables_df=comparables_df,
            pli_type=pli_type,
            years=years,
        ),
    }


def _exclude_companies(
    comparables_df: pd.DataFrame,
    excluded_names: list[str],
) -> pd.DataFrame:
    """Return comparables excluding named companies."""

    if not excluded_names:
        return comparables_df.copy()
    return comparables_df.loc[
        ~comparables_df[config.COMPANY_NAME_COLUMN].isin(excluded_names)
    ].copy()


def _base_period_label() -> str:
    """Return the display label for the default benchmark period."""

    return ", ".join(
        config.PERIOD_LABELS[year] for year in config.DEFAULT_BENCHMARK_PERIOD
    )
