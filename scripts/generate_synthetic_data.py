"""Generate public-demo synthetic data for the Pfizer TP benchmark app."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import config  # noqa: E402
from src.default_decisions import DEFAULT_DECISIONS  # noqa: E402

ACCEPTED_MARGINS = [
    0.145,
    0.074,
    0.064,
    0.055,
    0.036,
    0.029,
    0.012,
    0.006,
    0.002,
    -0.010,
]
ACCEPTED_REVENUES_EUR_K = [
    210_000,
    115_000,
    90_000,
    240_000,
    55_000,
    78_000,
    39_000,
    34_000,
    28_000,
    25_000,
]
YEAR_FACTORS = {
    "Last avail. yr": 1.00,
    "Year - 1": 0.96,
    "Year - 2": 0.91,
    "Year - 3": 0.88,
    "Year - 4": 0.84,
}


def main() -> None:
    """Generate synthetic tested-party and comparable workbooks."""

    config.SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    _write_workbook(_tested_party_frame(), config.SYNTHETIC_TESTED_PARTY_PATH)
    _write_workbook(_comparables_frame(), config.SYNTHETIC_COMPARABLES_PATH)


def _tested_party_frame() -> pd.DataFrame:
    """Return a synthetic tested-party DataFrame."""

    row = _base_row(
        company_name="Demo Tested Party GmbH",
        country="Germany",
        revenue_eur_k=1_250_000,
        employees=1_180,
        trade_description="Wholesale distribution of prescription medicines",
        margin=0.043,
        index=0,
    )
    yearly_margins = {
        "Last avail. yr": 0.044,
        "Year - 1": 0.061,
        "Year - 2": 0.021,
        "Year - 3": 0.066,
        "Year - 4": 0.064,
    }
    for suffix, margin in yearly_margins.items():
        _set_financials(row, 1_250_000, margin, suffix, 0)
    return pd.DataFrame([row])


def _comparables_frame() -> pd.DataFrame:
    """Return a synthetic 55-company comparable-candidate DataFrame."""

    rows = []
    accepted_index = 0
    for index, decision in enumerate(DEFAULT_DECISIONS):
        is_accepted = decision["decision"] == config.DECISION_ACCEPT
        if is_accepted:
            margin = ACCEPTED_MARGINS[accepted_index]
            revenue = ACCEPTED_REVENUES_EUR_K[accepted_index]
            employees = max(25, int(revenue / 1_800))
            accepted_index += 1
        else:
            margin = 0.015 + (index % 11) * 0.006
            revenue = 18_000 + index * 4_800
            employees = max(12, int(revenue / 2_300))

        rows.append(
            _base_row(
                company_name=decision["company_name"],
                country=decision["country"],
                revenue_eur_k=revenue,
                employees=employees,
                trade_description=_trade_description(decision),
                margin=margin,
                index=index,
            )
        )
    return pd.DataFrame(rows)


def _base_row(
    company_name: str,
    country: str,
    revenue_eur_k: float,
    employees: int,
    trade_description: str,
    margin: float,
    index: int,
) -> dict[str, object]:
    """Return one synthetic Orbis-like row."""

    row: dict[str, object] = {
        config.COMPANY_NAME_COLUMN: company_name,
        config.COUNTRY_COLUMN: country,
        config.NACE_COLUMN: 4646,
        config.INDEPENDENCE_COLUMN: "A",
        config.GUO_COLUMN: "Independent demo group",
        config.TRADE_DESCRIPTION_COLUMN: trade_description,
        config.LATEST_EMPLOYEES_COLUMN: employees,
    }
    for suffix in config.YEAR_SUFFIXES:
        _set_financials(row, revenue_eur_k, margin, suffix, index)
    return row


def _set_financials(
    row: dict[str, object],
    revenue_eur_k: float,
    margin: float,
    suffix: str,
    index: int,
) -> None:
    """Populate synthetic year-suffix financial columns."""

    factor = YEAR_FACTORS[suffix]
    sales = round(revenue_eur_k * factor * (1 + (index % 5) * 0.004), 0)
    year_adjustment = {
        "Last avail. yr": 0.002,
        "Year - 1": 0.000,
        "Year - 2": -0.004,
        "Year - 3": 0.001,
        "Year - 4": -0.001,
    }
    adjusted_margin = margin + year_adjustment[suffix]
    ebit = round(sales * adjusted_margin, 0)
    material_costs = round(sales * (0.70 + (index % 4) * 0.01), 0)
    gross_profit = sales - material_costs
    roce = round((adjusted_margin + 0.018) * 100, 2)

    row[f"{config.SALES_COLUMN_PREFIX} {suffix}"] = sales
    row[f"{config.EBIT_COLUMN_PREFIX} {suffix}"] = ebit
    row[f"{config.GROSS_PROFIT_COLUMN_PREFIX} {suffix}"] = gross_profit
    row[f"{config.MATERIAL_COSTS_COLUMN_PREFIX} {suffix}"] = material_costs
    row[f"{config.ROCE_COLUMN_PREFIX} {suffix}"] = roce
    if suffix == "Last avail. yr":
        row[config.LATEST_EMPLOYEES_COLUMN] = int(
            row.get(config.LATEST_EMPLOYEES_COLUMN, 0) or max(1, int(sales / 2_100))
        )


def _trade_description(decision: dict[str, object]) -> str:
    """Return a synthetic trade description for one candidate."""

    if decision["decision"] == config.DECISION_ACCEPT:
        return "Wholesale distribution of pharmaceutical goods"
    reason = str(decision["reason"])
    label = config.REJECT_CATEGORIES.get(reason, {}).get("label", "Excluded profile")
    return f"Synthetic demo company with {label.lower()} profile"


def _write_workbook(dataframe: pd.DataFrame, path: Path) -> None:
    """Write an Orbis-like workbook with Search summary and Results sheets."""

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Search summary": ["Synthetic public-demo data"]}).to_excel(
            writer,
            sheet_name=config.ORBIS_IGNORED_SHEET,
            index=False,
        )
        dataframe.to_excel(writer, sheet_name=config.ORBIS_RESULTS_SHEET, index=False)


if __name__ == "__main__":
    main()
