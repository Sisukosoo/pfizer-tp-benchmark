"""Streamlit entry point for the Pfizer transfer pricing benchmark app."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import config
from src.data_loader import load_comparables, load_tested_party

st.set_page_config(
    page_title="Pfizer TP Benchmark",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def get_tested_party() -> pd.DataFrame:
    """Load tested-party data for Streamlit with caching."""

    return load_tested_party()


@st.cache_data(show_spinner=False)
def get_comparables() -> pd.DataFrame:
    """Load comparables data for Streamlit with caching."""

    return load_comparables()


def main() -> None:
    """Render the Streamlit application."""

    with st.sidebar:
        st.title("Pfizer TP Benchmark")
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    pages = [
        st.Page(_overview_page, title="Overview"),
        st.Page(_comparables_page, title="Comparables"),
        st.Page(_analysis_page, title="Analysis"),
        st.Page(_about_page, title="About"),
    ]
    navigation = st.navigation(pages)
    navigation.run()


def _overview_page() -> None:
    """Render the overview page."""

    st.header("Overview")

    if not config.TESTED_PARTY_PATH.exists():
        _show_missing_data_message()
        return

    try:
        tested_party = get_tested_party()
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    if tested_party.empty:
        st.info("The tested-party export loaded, but no company rows were found.")
        return

    row = tested_party.iloc[0]
    latest_revenue = row.get(config.LATEST_REVENUE_COLUMN, pd.NA)
    latest_employees = row.get(config.LATEST_EMPLOYEES_COLUMN, pd.NA)
    st.subheader(str(row.get(config.COMPANY_NAME_COLUMN, "Tested party")))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Country", _display_value(row.get(config.COUNTRY_COLUMN)))
    col2.metric("NACE", _format_nace(row.get(config.NACE_COLUMN)))
    col3.metric("Latest revenue", _format_revenue_millions(latest_revenue))
    col4.metric("Employees (latest)", _format_number(latest_employees))

    st.write(config.TESTED_PARTY_CHARACTERIZATION)


def _comparables_page() -> None:
    """Render the comparables page."""

    st.header("Comparables")

    if not config.COMPARABLES_PATH.exists():
        _show_missing_data_message()
        return

    try:
        comparables = get_comparables()
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    st.metric("Candidate companies", f"{len(comparables):,}")
    st.dataframe(comparables.head(10), use_container_width=True)


def _analysis_page() -> None:
    """Render the analysis placeholder page."""

    st.header("Analysis")
    st.info("Coming soon")


def _about_page() -> None:
    """Render the about page."""

    st.header("About")
    st.write(
        "This portfolio project benchmarks Pfizer Pharma GmbH under the OECD "
        "Transactional Net Margin Method using Orbis comparables data."
    )
    st.write(
        "Data files are excluded from the repository because the source exports "
        "are confidential under TU München's Bureau van Dijk subscription."
    )


def _show_missing_data_message() -> None:
    """Show a friendly message when confidential Orbis exports are absent."""

    st.info("Place Orbis exports in data/raw/ to proceed.")


def _display_value(value: object) -> str:
    """Format a display value for Streamlit metrics."""

    if pd.isna(value):
        return "n/a"
    return str(value)


def _format_number(value: object) -> str:
    """Format a numeric metric for display."""

    if pd.isna(value):
        return "n/a"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _format_revenue_millions(value: object) -> str:
    """Format a thousand-EUR value as EUR millions."""

    if pd.isna(value):
        return "n/a"
    try:
        return f"€{float(value) / 1_000:,.0f}M"
    except (TypeError, ValueError):
        return str(value)


def _format_nace(value: object) -> str:
    """Format a NACE core code with its configured description."""

    if pd.isna(value):
        return "n/a"
    try:
        code = f"{int(float(value)):04d}"
    except (TypeError, ValueError):
        code = str(value).strip()

    description = config.NACE_DESCRIPTIONS.get(code)
    if description is None:
        return code
    return f"{code} - {description}"


if __name__ == "__main__":
    main()
