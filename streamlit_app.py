"""Streamlit entry point for the Pfizer transfer pricing benchmark app."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config
from src.comparables import (
    compute_cascade_stats,
    get_accepted,
    get_pending,
    get_rejected,
    load_decisions,
    mark_user_edits,
    reset_to_defaults,
    save_decisions,
)
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
    st.write(
        "This page shows the comparables selection process. From an initial pool "
        "of 55 candidates retrieved from Orbis with NACE 4646 (Wholesale of "
        "pharmaceutical goods), Independence A+B, EU/EFTA geography, the rejection "
        "cascade applies functional comparability criteria to identify the final "
        "pool of accepted comparables."
    )

    if not config.COMPARABLES_PATH.exists():
        _show_missing_data_message()
        return

    try:
        comparables = get_comparables()
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    decisions = load_decisions()
    accepted = get_accepted(comparables, decisions)
    rejected = get_rejected(comparables, decisions)
    pending = get_pending(comparables, decisions)
    stats = compute_cascade_stats(decisions, raw_count=len(comparables))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Raw candidates", f"{stats['raw']:,}")
    col2.metric("Rejected", f"{stats['rejected']:,}")
    col3.metric("Pending", f"{len(pending):,}")
    col4.metric("Final pool", f"{stats['accepted']:,}")

    st.plotly_chart(_build_funnel_chart(stats), use_container_width=True)

    accepted_tab, rejected_tab, edit_tab = st.tabs(
        [
            f"Accepted ({len(accepted)})",
            f"Rejected ({len(rejected)})",
            "Edit decisions",
        ]
    )

    with accepted_tab:
        st.dataframe(
            _comparables_display_frame(accepted),
            use_container_width=True,
            hide_index=True,
            column_config=_comparables_column_config(),
        )

    with rejected_tab:
        reason_options = ["All", *config.CATEGORY_DISPLAY_ORDER]
        selected_reason = st.selectbox(
            "Filter by rejection category",
            reason_options,
            format_func=lambda value: (
                "All" if value == "All" else config.REJECT_CATEGORIES[value]["label"]
            ),
        )
        rejected_view = rejected
        if selected_reason != "All":
            rejected_view = rejected.loc[rejected["reason"] == selected_reason]
        st.dataframe(
            _rejected_display_frame(rejected_view),
            use_container_width=True,
            hide_index=True,
            column_config=_rejected_column_config(),
        )

    with edit_tab:
        st.warning(
            "Changing decisions here will affect downstream PLI calculations and "
            "arm's length range outputs in later workflow steps."
        )
        edited_decisions = st.data_editor(
            decisions.copy(),
            use_container_width=True,
            hide_index=True,
            disabled=[
                "bvd_id",
                "company_name",
                "country",
                "modified_at",
                "modified_by",
            ],
            column_config={
                "decision": st.column_config.SelectboxColumn(
                    "Decision",
                    options=list(config.DECISION_OPTIONS),
                    required=True,
                ),
                "reason": st.column_config.SelectboxColumn(
                    "Reason",
                    options=["", *config.CATEGORY_DISPLAY_ORDER],
                ),
                "notes": st.column_config.TextColumn("Notes"),
            },
        )
        if st.button("Save edited decisions"):
            save_decisions(mark_user_edits(decisions, edited_decisions))
            st.success("Decisions saved.")
            st.cache_data.clear()
            st.rerun()

    st.divider()
    reset_col, download_col = st.columns(2)
    with reset_col:
        confirm_reset = st.checkbox("Confirm reset to default decisions")
        if st.button("Reset to default decisions", disabled=not confirm_reset):
            reset_to_defaults()
            st.success("Default decisions restored.")
            st.cache_data.clear()
            st.rerun()
    with download_col:
        st.download_button(
            "Download decisions as CSV",
            data=decisions.to_csv(index=False).encode("utf-8"),
            file_name="comparables_decisions.csv",
            mime="text/csv",
        )


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
        return f"{config.EURO_SIGN}{float(value) / 1_000:,.0f}M"
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


def _build_funnel_chart(stats: dict[str, object]) -> go.Figure:
    """Build a Plotly funnel chart for the rejection cascade."""

    rejected_by_category = stats["rejected_by_category"]
    if not isinstance(rejected_by_category, dict):
        rejected_by_category = {}

    labels = [f"Raw candidates ({stats['raw']})"]
    values = [int(stats["raw"])]
    hover_text = ["Initial Orbis candidate pool"]
    remaining = int(stats["raw"])

    for category in config.CATEGORY_DISPLAY_ORDER:
        rejected_count = int(rejected_by_category.get(category, 0))
        if rejected_count == 0:
            continue
        remaining -= rejected_count
        label = config.REJECT_CATEGORIES[category]["label"]
        labels.append(f"{label} excluded ({rejected_count})")
        values.append(remaining)
        hover_text.append(config.REJECT_CATEGORIES[category]["description"])

    labels.append(f"After category exclusions ({stats['accepted']} accepted)")
    values.append(int(stats["accepted"]))
    hover_text.append("Final accepted comparable pool")

    figure = go.Figure(
        go.Funnel(
            y=labels,
            x=values,
            textinfo="value+percent initial",
            hovertext=hover_text,
            marker={"color": _funnel_colors(len(labels))},
        )
    )
    figure.update_layout(
        margin={"l": 20, "r": 20, "t": 20, "b": 20},
        height=520,
    )
    return figure


def _comparables_display_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return accepted comparables display columns."""

    display = dataframe[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            config.LATEST_REVENUE_COLUMN,
            config.LATEST_EMPLOYEES_COLUMN,
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ].copy()
    display["Revenue EURm"] = display[config.LATEST_REVENUE_COLUMN] / 1_000
    display["Employees"] = display[config.LATEST_EMPLOYEES_COLUMN]
    return display[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            "Revenue EURm",
            "Employees",
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ]


def _rejected_display_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return rejected comparables display columns."""

    display = dataframe[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            "reason_label",
            "notes",
            config.LATEST_REVENUE_COLUMN,
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ].copy()
    display["Revenue EURm"] = display[config.LATEST_REVENUE_COLUMN] / 1_000
    return display[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            "reason_label",
            "notes",
            "Revenue EURm",
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ].sort_values(["reason_label", config.COMPANY_NAME_COLUMN])


def _comparables_column_config() -> dict[str, object]:
    """Return Streamlit column configuration for accepted comparables."""

    return {
        config.COMPANY_NAME_COLUMN: "Company",
        config.COUNTRY_COLUMN: "Country",
        "Revenue EURm": st.column_config.NumberColumn(
            f"Revenue ({config.EURO_SIGN}M)",
            format=f"{config.EURO_SIGN} %.0fM",
        ),
        "Employees": st.column_config.NumberColumn("Employees", format="%d"),
        config.TRADE_DESCRIPTION_COLUMN: "Trade description",
    }


def _rejected_column_config() -> dict[str, object]:
    """Return Streamlit column configuration for rejected comparables."""

    return {
        config.COMPANY_NAME_COLUMN: "Company",
        config.COUNTRY_COLUMN: "Country",
        "reason_label": "Reason",
        "notes": "Notes",
        "Revenue EURm": st.column_config.NumberColumn(
            f"Revenue ({config.EURO_SIGN}M)",
            format=f"{config.EURO_SIGN} %.0fM",
        ),
        config.TRADE_DESCRIPTION_COLUMN: "Trade description",
    }


def _funnel_colors(count: int) -> list[str]:
    """Return a short Plotly-friendly color sequence."""

    palette = [
        "#3B82F6",
        "#EF4444",
        "#F97316",
        "#EAB308",
        "#22C55E",
        "#14B8A6",
        "#6366F1",
        "#8B5CF6",
        "#EC4899",
        "#64748B",
        "#111827",
    ]
    return [palette[index % len(palette)] for index in range(count)]


if __name__ == "__main__":
    main()
