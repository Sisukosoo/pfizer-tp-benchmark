"""Profit Level Indicator calculations for TNMM benchmarking."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config


def operating_margin(
    dataframe: pd.DataFrame,
    year_suffix: str = "Last avail. yr",
) -> pd.Series:
    """Calculate yearly Operating Margin for each row.

    Args:
        dataframe: Orbis financial data.
        year_suffix: Relative Orbis year suffix.

    Returns:
        EBIT divided by Sales as a decimal ratio.
    """

    ebit = _numeric_column(dataframe, _column(config.EBIT_COLUMN_PREFIX, year_suffix))
    sales = _numeric_column(dataframe, _column(config.SALES_COLUMN_PREFIX, year_suffix))
    return _safe_divide(ebit, sales)


def weighted_operating_margin(
    dataframe: pd.DataFrame,
    years: list[str],
) -> pd.Series:
    """Calculate multi-year weighted Operating Margin per row.

    Args:
        dataframe: Orbis financial data.
        years: Relative Orbis year suffixes to include.

    Returns:
        Sum of EBIT divided by sum of Sales across valid years.
    """

    return _weighted_ratio(
        dataframe=dataframe,
        numerator_prefix=config.EBIT_COLUMN_PREFIX,
        denominator_prefix=config.SALES_COLUMN_PREFIX,
        years=years,
    )


def berry_ratio(
    dataframe: pd.DataFrame,
    year_suffix: str = "Last avail. yr",
) -> pd.Series:
    """Calculate yearly Berry Ratio for each row.

    The denominator is operating expenses derived as Sales - EBIT - Material
    Costs. Orbis does not provide a direct Other Operating Expenses column in
    the current export, so this derives personnel, depreciation/amortization,
    and other operating expenses from the available income-statement lines.

    Args:
        dataframe: Orbis financial data.
        year_suffix: Relative Orbis year suffix.

    Returns:
        Gross Profit divided by derived operating expenses.
    """

    gross_profit = _numeric_column(
        dataframe,
        _column(config.GROSS_PROFIT_COLUMN_PREFIX, year_suffix),
    )
    operating_expenses = _operating_expenses(dataframe, year_suffix)
    return _safe_divide(gross_profit, operating_expenses)


def weighted_berry_ratio(
    dataframe: pd.DataFrame,
    years: list[str],
) -> pd.Series:
    """Calculate multi-year weighted Berry Ratio per row.

    Args:
        dataframe: Orbis financial data.
        years: Relative Orbis year suffixes to include.

    Returns:
        Sum of Gross Profit divided by sum of derived operating expenses.
    """

    numerator_sum = pd.Series(0.0, index=dataframe.index)
    denominator_sum = pd.Series(0.0, index=dataframe.index)
    valid_count = pd.Series(0, index=dataframe.index)

    for year in years:
        numerator = _numeric_column(
            dataframe,
            _column(config.GROSS_PROFIT_COLUMN_PREFIX, year),
        )
        denominator = _operating_expenses(dataframe, year)
        valid = numerator.notna() & denominator.notna() & denominator.ne(0)
        numerator_sum = numerator_sum + numerator.where(valid, 0.0)
        denominator_sum = denominator_sum + denominator.where(valid, 0.0)
        valid_count = valid_count + valid.astype(int)

    result = _safe_divide(numerator_sum, denominator_sum)
    return result.where(valid_count.gt(0), np.nan)


def roce(
    dataframe: pd.DataFrame,
    year_suffix: str = "Last avail. yr",
) -> pd.Series:
    """Read pre-calculated ROCE from Orbis data.

    Orbis stores ROCE in percentage-point form in the current export (for
    example, 6.49 means 6.49%). The returned value is normalized to a decimal
    ratio so it can be compared consistently with Operating Margin.

    Args:
        dataframe: Orbis financial data.
        year_suffix: Relative Orbis year suffix.

    Returns:
        ROCE as a decimal ratio.
    """

    values = _numeric_column(dataframe, _column(config.ROCE_COLUMN_PREFIX, year_suffix))
    return _normalize_orbis_percent(values)


def weighted_roce(dataframe: pd.DataFrame, years: list[str]) -> pd.Series:
    """Calculate an average multi-year ROCE from Orbis-provided yearly values.

    ROCE is already a ratio in Orbis and the current export does not include
    capital-employed numerator and denominator lines needed for true weighting.
    This function therefore averages the available yearly ROCE observations.

    Args:
        dataframe: Orbis financial data.
        years: Relative Orbis year suffixes to include.

    Returns:
        Average ROCE as a decimal ratio.
    """

    yearly_values = [roce(dataframe, year) for year in years]
    if not yearly_values:
        return pd.Series(np.nan, index=dataframe.index)
    return pd.concat(yearly_values, axis=1).mean(axis=1, skipna=True)


def yearly_pli_table(
    dataframe: pd.DataFrame,
    pli_type: str,
    years: list[str],
) -> pd.DataFrame:
    """Build a per-year PLI table plus weighted or averaged result.

    Args:
        dataframe: Orbis financial data.
        pli_type: One of the configured PLI option keys.
        years: Relative Orbis year suffixes to include.

    Returns:
        DataFrame with company name, yearly PLIs, and weighted PLI.
    """

    result = pd.DataFrame(index=dataframe.index)
    if config.COMPANY_NAME_COLUMN in dataframe.columns:
        result[config.COMPANY_NAME_COLUMN] = dataframe[config.COMPANY_NAME_COLUMN]
    if config.COUNTRY_COLUMN in dataframe.columns:
        result[config.COUNTRY_COLUMN] = dataframe[config.COUNTRY_COLUMN]

    for year in years:
        result[config.PERIOD_LABELS.get(year, year)] = calculate_pli(
            dataframe,
            pli_type,
            year,
        )
    result["Weighted PLI"] = calculate_weighted_pli(dataframe, pli_type, years)
    return result


def calculate_pli(
    dataframe: pd.DataFrame,
    pli_type: str,
    year_suffix: str = "Last avail. yr",
) -> pd.Series:
    """Calculate a yearly PLI by configured type.

    Args:
        dataframe: Orbis financial data.
        pli_type: One of `operating_margin`, `berry_ratio`, or `roce`.
        year_suffix: Relative Orbis year suffix.

    Returns:
        Yearly PLI as a Series.

    Raises:
        ValueError: If the PLI type is unknown.
    """

    if pli_type == config.PLI_OPERATING_MARGIN:
        return operating_margin(dataframe, year_suffix)
    if pli_type == config.PLI_BERRY_RATIO:
        return berry_ratio(dataframe, year_suffix)
    if pli_type == config.PLI_ROCE:
        return roce(dataframe, year_suffix)
    raise ValueError(f"Unsupported PLI type: {pli_type}")


def calculate_weighted_pli(
    dataframe: pd.DataFrame,
    pli_type: str,
    years: list[str],
) -> pd.Series:
    """Calculate a multi-year PLI by configured type.

    Args:
        dataframe: Orbis financial data.
        pli_type: One of `operating_margin`, `berry_ratio`, or `roce`.
        years: Relative Orbis year suffixes to include.

    Returns:
        Multi-year PLI as a Series.

    Raises:
        ValueError: If the PLI type is unknown.
    """

    if pli_type == config.PLI_OPERATING_MARGIN:
        return weighted_operating_margin(dataframe, years)
    if pli_type == config.PLI_BERRY_RATIO:
        return weighted_berry_ratio(dataframe, years)
    if pli_type == config.PLI_ROCE:
        return weighted_roce(dataframe, years)
    raise ValueError(f"Unsupported PLI type: {pli_type}")


def _weighted_ratio(
    dataframe: pd.DataFrame,
    numerator_prefix: str,
    denominator_prefix: str,
    years: list[str],
) -> pd.Series:
    """Calculate sum(numerator) / sum(denominator) across valid years."""

    numerator_sum = pd.Series(0.0, index=dataframe.index)
    denominator_sum = pd.Series(0.0, index=dataframe.index)
    valid_count = pd.Series(0, index=dataframe.index)

    for year in years:
        numerator = _numeric_column(dataframe, _column(numerator_prefix, year))
        denominator = _numeric_column(dataframe, _column(denominator_prefix, year))
        valid = numerator.notna() & denominator.notna() & denominator.ne(0)
        numerator_sum = numerator_sum + numerator.where(valid, 0.0)
        denominator_sum = denominator_sum + denominator.where(valid, 0.0)
        valid_count = valid_count + valid.astype(int)

    result = _safe_divide(numerator_sum, denominator_sum)
    return result.where(valid_count.gt(0), np.nan)


def _operating_expenses(dataframe: pd.DataFrame, year_suffix: str) -> pd.Series:
    """Derive operating expenses as Sales - EBIT - Material Costs."""

    sales = _numeric_column(dataframe, _column(config.SALES_COLUMN_PREFIX, year_suffix))
    ebit = _numeric_column(dataframe, _column(config.EBIT_COLUMN_PREFIX, year_suffix))
    material_costs = _numeric_column(
        dataframe,
        _column(config.MATERIAL_COSTS_COLUMN_PREFIX, year_suffix),
    )
    return sales - ebit - material_costs


def _numeric_column(dataframe: pd.DataFrame, column: str) -> pd.Series:
    """Return a numeric column, or NaN values when absent."""

    if column not in dataframe.columns:
        return pd.Series(np.nan, index=dataframe.index)
    return pd.to_numeric(dataframe[column], errors="coerce")


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide while returning NaN for missing or zero denominators."""

    result = numerator / denominator
    invalid = numerator.isna() | denominator.isna() | denominator.eq(0)
    return result.mask(invalid, np.nan)


def _normalize_orbis_percent(values: pd.Series) -> pd.Series:
    """Convert percentage-point values to ratios while preserving ratio inputs."""

    return values.where(values.abs().le(1), values / 100)


def _column(prefix: str, year_suffix: str) -> str:
    """Build an Orbis metric column name from prefix and year suffix."""

    return f"{prefix} {year_suffix}"
