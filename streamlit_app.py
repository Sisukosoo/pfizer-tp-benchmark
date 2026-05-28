"""Streamlit entry point for the Pfizer transfer pricing benchmark app."""

from __future__ import annotations

import base64
import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import config
from src.benchmarking import run_benchmark
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
from src.pli_calculator import operating_margin
from src.reporting import (
    DECISIONS_FILENAME,
    REPORT_FILENAME,
    REPORT_MIME_TYPE,
    accepted_comparables_frame,
    build_decisions_workbook,
    build_excel_report,
    build_report_context,
    executive_conclusion,
    overview_frame,
    range_frame,
    sensitivity_frame,
)
from src.sensitivity import (
    normalize_pfizer_fy22_ebit,
    run_all_scenarios,
    scenario_summary_frame,
)
from src.visualizations import (
    arms_length_plot,
    revenue_vs_margin_scatter,
    sensitivity_range_plot,
    sorted_comparables_bar,
    tested_party_trend_plot,
)

st.set_page_config(
    page_title="Pfizer TP Benchmark",
    layout="wide",
)

PLOTLY_CONFIG = {"displayModeBar": False, "responsive": True}


@st.cache_data(show_spinner=False)
def get_tested_party(data_mode: str) -> pd.DataFrame:
    """Load tested-party data for Streamlit with caching."""

    return load_tested_party(data_mode)


@st.cache_data(show_spinner=False)
def get_comparables(data_mode: str) -> pd.DataFrame:
    """Load comparables data for Streamlit with caching."""

    return load_comparables(data_mode)


def main() -> None:
    """Render the Streamlit application."""

    _inject_global_styles()

    with st.sidebar:
        st.title("Pfizer TP Benchmark")
        current_mode = _selected_data_mode()
        st.caption(f"Data mode: {_data_mode_label(current_mode)}")
        if st.button("Refresh data"):
            st.cache_data.clear()
            st.rerun()

    pages = [
        st.Page(_overview_page, title="Overview"),
        st.Page(_comparables_page, title="Comparables"),
        st.Page(_analysis_page, title="Analysis"),
        st.Page(_report_page, title="Report"),
        st.Page(_about_page, title="About"),
    ]
    navigation = st.navigation(pages)
    navigation.run()


def _selected_data_mode() -> str:
    """Return the current Streamlit data mode."""

    return config.active_data_mode()


def _data_mode_label(data_mode: str) -> str:
    """Return a user-facing data mode label."""

    if data_mode == config.DATA_MODE_SYNTHETIC:
        return "Synthetic (public demo)"
    return "Real Orbis (private local)"


def _data_files_available(data_mode: str) -> bool:
    """Return whether tested-party and comparables files are available."""

    return (
        config.resolve_tested_party_path(data_mode).exists()
        and config.resolve_comparables_path(data_mode).exists()
    )


def _inject_global_styles() -> None:
    """Inject small layout styles shared across Streamlit pages."""

    st.markdown(
        """
        <style>
          .block-container {
            padding-top: 3.4rem;
            padding-bottom: 3rem;
            max-width: 1180px;
          }
          h1, h2, h3 {
            letter-spacing: 0;
          }
          .page-lede {
            max-width: 920px;
            margin: 0.35rem 0 1.35rem 0;
            font-size: 1.02rem;
            line-height: 1.55;
            opacity: 0.94;
          }
          .kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.9rem;
            margin: 1.2rem 0 1.35rem 0;
          }
          .kpi-card {
            min-height: 94px;
            padding: 0.9rem 1rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 7px;
            background: rgba(255, 255, 255, 0.025);
          }
          .kpi-card-highlight {
            border-color: rgba(0, 159, 218, 0.55);
            background: rgba(0, 159, 218, 0.08);
          }
          .kpi-label {
            margin-bottom: 0.35rem;
            font-size: 0.82rem;
            font-weight: 720;
            line-height: 1.25;
            opacity: 0.86;
          }
          .kpi-value {
            font-size: clamp(1.45rem, 2.4vw, 2.05rem);
            line-height: 1.12;
            font-weight: 520;
            letter-spacing: 0;
            overflow-wrap: anywhere;
          }
          @media (max-width: 900px) {
            .kpi-grid {
              grid-template-columns: repeat(2, minmax(0, 1fr));
            }
          }
          @media (max-width: 560px) {
            .kpi-grid {
              grid-template-columns: 1fr;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _kpi_grid_html(
    items: list[tuple[str, str]],
    highlight_index: int | None = None,
) -> str:
    """Return reusable KPI card markup."""

    cards = []
    for index, (label, value) in enumerate(items):
        extra_class = " kpi-card-highlight" if index == highlight_index else ""
        cards.append(
            f'<div class="kpi-card{extra_class}">'
            f'<div class="kpi-label">{html.escape(label)}</div>'
            f'<div class="kpi-value">{html.escape(value)}</div>'
            "</div>"
        )
    return f'<div class="kpi-grid">{"".join(cards)}</div>'


def _overview_page() -> None:
    """Render the overview page."""

    st.header("Overview")
    data_mode = _selected_data_mode()

    if not config.resolve_tested_party_path(data_mode).exists():
        _show_missing_data_message()
        return

    try:
        tested_party = get_tested_party(data_mode)
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    if tested_party.empty:
        st.info("The tested-party export loaded, but no company rows were found.")
        return

    row = tested_party.iloc[0]
    latest_revenue = row.get(config.LATEST_REVENUE_COLUMN, pd.NA)
    latest_employees = row.get(config.LATEST_EMPLOYEES_COLUMN, pd.NA)
    st.markdown(
        _overview_hero_html(row, latest_revenue, latest_employees),
        unsafe_allow_html=True,
    )


def _comparables_page() -> None:
    """Render the comparables page."""

    st.header("Comparables")
    st.markdown(
        """
        <p class="page-lede">
          This page documents the comparables selection process. The candidate
          pool starts from 55 EU/EFTA NACE 4646 companies and applies functional
          comparability criteria to identify the final accepted pool.
        </p>
        """,
        unsafe_allow_html=True,
    )

    data_mode = _selected_data_mode()
    if not config.resolve_comparables_path(data_mode).exists():
        _show_missing_data_message()
        return

    try:
        comparables = get_comparables(data_mode)
        decisions = load_decisions(data_mode=data_mode)
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    accepted = get_accepted(comparables, decisions)
    rejected = get_rejected(comparables, decisions)
    pending = get_pending(comparables, decisions)
    stats = compute_cascade_stats(decisions, raw_count=len(comparables))

    st.markdown(
        _kpi_grid_html(
            [
                ("Raw candidates", f"{stats['raw']:,}"),
                ("Rejected", f"{stats['rejected']:,}"),
                ("Pending", f"{len(pending):,}"),
                ("Final pool", f"{stats['accepted']:,}"),
            ],
            highlight_index=3,
        ),
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _build_funnel_chart(stats),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

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
            save_decisions(
                mark_user_edits(decisions, edited_decisions),
                data_mode=data_mode,
            )
            st.success("Decisions saved.")
            st.cache_data.clear()
            st.rerun()

    st.divider()
    reset_col, download_col = st.columns(2)
    with reset_col:
        if data_mode == config.DATA_MODE_REAL:
            st.caption(
                "Reset is disabled in real-data mode because private Orbis "
                "decisions are local state."
            )
        else:
            confirm_reset = st.checkbox("Confirm reset to default decisions")
            if st.button("Reset to default decisions", disabled=not confirm_reset):
                reset_to_defaults(data_mode=data_mode)
                st.success("Default decisions restored.")
                st.cache_data.clear()
                st.rerun()
    with download_col:
        st.download_button(
            "Download decisions as Excel",
            data=build_decisions_workbook(decisions),
            file_name=DECISIONS_FILENAME,
            mime=REPORT_MIME_TYPE,
        )
        st.download_button(
            "Download decisions as CSV",
            data=decisions.to_csv(index=False).encode("utf-8"),
            file_name="comparables_decisions.csv",
            mime="text/csv",
        )


def _analysis_page() -> None:
    """Render the arm's-length range analysis page."""

    st.header("Analysis")
    data_mode = _selected_data_mode()

    if not _data_files_available(data_mode):
        _show_missing_data_message()
        return

    try:
        tested_party, accepted_comparables = _analysis_inputs(data_mode)
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    if accepted_comparables.empty:
        st.info("No accepted comparables available. Review the Comparables page first.")
        return

    base_result = run_benchmark(
        tested_party_df=tested_party,
        comparables_df=accepted_comparables,
        pli_type=config.PLI_OPERATING_MARGIN,
        years=config.DEFAULT_BENCHMARK_PERIOD,
    )

    dashboard_tab, base_tab, sensitivity_tab, methodology_tab, detail_tab = st.tabs(
        [
            "Executive Dashboard",
            "Base Case",
            "Sensitivity",
            "Methodology",
            "Comparables PLI detail",
        ]
    )

    with dashboard_tab:
        _render_executive_dashboard(tested_party, accepted_comparables, base_result)

    with base_tab:
        _render_base_case(base_result)

    with sensitivity_tab:
        _render_sensitivity(tested_party, accepted_comparables, base_result)

    with methodology_tab:
        st.markdown(_methodology_text())

    with detail_tab:
        _render_pli_detail(base_result)


def _analysis_inputs(data_mode: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load tested party and accepted comparables for analysis."""

    tested_party = get_tested_party(data_mode)
    raw_comparables = get_comparables(data_mode)
    decisions = load_decisions(data_mode=data_mode)
    accepted_comparables = get_accepted(raw_comparables, decisions)
    return tested_party, accepted_comparables


def _report_page() -> None:
    """Render the executive report and Excel export page."""

    st.header("Report")
    st.write(
        "This page turns the current benchmark state into an interview-ready "
        "executive summary and a downloadable Excel workpaper."
    )
    data_mode = _selected_data_mode()

    if not _data_files_available(data_mode):
        _show_missing_data_message()
        return

    try:
        tested_party = get_tested_party(data_mode)
        raw_comparables = get_comparables(data_mode)
        decisions = load_decisions(data_mode=data_mode)
        context = build_report_context(tested_party, raw_comparables, decisions)
    except (FileNotFoundError, ValueError) as error:
        st.warning(str(error))
        return

    if context["accepted"].empty:
        st.info("No accepted comparables available. Review the Comparables page first.")
        return

    result = context["base_result"]
    range_dict = result["range"]
    st.markdown(
        _kpi_grid_html(
            [
                ("Primary PLI", str(result["pli_label"])),
                (
                    "Tested party OM",
                    _format_pli_value(result["tested_pli"], result["pli_type"]),
                ),
                ("IQR", _format_iqr_label(range_dict, str(result["pli_type"]))),
                ("Conclusion", _position_label(result["position"]["position"])),
            ],
            highlight_index=3,
        ),
        unsafe_allow_html=True,
    )

    st.subheader("Executive conclusion")
    st.markdown(executive_conclusion(context))

    preview_tab, workpaper_tab = st.tabs(["Report preview", "Excel workpaper"])
    with preview_tab:
        st.dataframe(overview_frame(context), hide_index=True, use_container_width=True)
        st.dataframe(range_frame(context), hide_index=True, use_container_width=True)
        st.dataframe(
            sensitivity_frame(context),
            hide_index=True,
            use_container_width=True,
        )

    with workpaper_tab:
        st.write(
            "The workbook contains the current tested-party overview, accepted "
            "comparables, rejected candidates, PLI detail, range calculation, "
            "sensitivity scenarios, and methodology notes."
        )
        st.download_button(
            "Download Excel workpaper",
            data=build_excel_report(tested_party, raw_comparables, decisions),
            file_name=REPORT_FILENAME,
            mime=REPORT_MIME_TYPE,
        )

        st.dataframe(
            accepted_comparables_frame(context),
            hide_index=True,
            use_container_width=True,
        )


def _render_executive_dashboard(
    tested_party: pd.DataFrame,
    accepted_comparables: pd.DataFrame,
    base_result: dict[str, object],
) -> None:
    """Render the executive analytics dashboard."""

    st.subheader("Executive Analytics Dashboard")
    st.markdown(
        """
        <p class="page-lede">
          These visuals connect the FAR memo, rejection cascade, and TNMM result:
          tested-party margin development, comparable ranking, sensitivity
          ranges, and the size mismatch limitation.
        </p>
        """,
        unsafe_allow_html=True,
    )

    trend_col, bar_col = st.columns([0.48, 0.52])
    with trend_col:
        st.plotly_chart(
            tested_party_trend_plot(
                _tested_party_trend_series(tested_party),
                adjusted_points=_tested_party_adjusted_points(tested_party),
                title="Pfizer Operating Margin Trend (FY2020-FY2024)",
            ),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )
    with bar_col:
        st.plotly_chart(
            sorted_comparables_bar(
                base_result["comparables_detail"],
                float(base_result["tested_pli"]),
                base_result["range"],
            ),
            use_container_width=True,
            config=PLOTLY_CONFIG,
        )

    sensitivity_summary = scenario_summary_frame(
        run_all_scenarios(
            tested_party_df=tested_party,
            comparables_df=accepted_comparables,
            include_fy22_adjustment=True,
        )
    )
    st.plotly_chart(
        sensitivity_range_plot(sensitivity_summary),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

    tested_revenue = pd.to_numeric(
        tested_party.iloc[0].get(config.LATEST_REVENUE_COLUMN),
        errors="coerce",
    )
    st.plotly_chart(
        revenue_vs_margin_scatter(
            base_result["comparables_detail"],
            float(tested_revenue),
            float(base_result["tested_pli"]),
        ),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )
    st.caption(
        "The revenue scatter is intentionally included as a limitation exhibit: "
        "Pfizer is materially larger than the accepted comparable pool."
    )


def _render_base_case(result: dict[str, object]) -> None:
    """Render the base-case arm's-length range analysis."""

    st.subheader(
        "Arm's-Length Range Analysis - Operating Margin " "(FY22-FY24, 3-year weighted)"
    )

    range_dict = result["range"]
    position = result["position"]
    if not isinstance(range_dict, dict) or not isinstance(position, dict):
        st.warning("Benchmark result is malformed.")
        return

    st.markdown(
        _kpi_grid_html(
            [
                (
                    "Tested party OM",
                    _format_pli_value(
                        float(result["tested_pli"]),
                        config.PLI_OPERATING_MARGIN,
                    ),
                ),
                (
                    "Q1",
                    _format_pli_value(range_dict["q1"], config.PLI_OPERATING_MARGIN),
                ),
                (
                    "Median",
                    _format_pli_value(
                        range_dict["median"],
                        config.PLI_OPERATING_MARGIN,
                    ),
                ),
                (
                    "Q3",
                    _format_pli_value(range_dict["q3"], config.PLI_OPERATING_MARGIN),
                ),
            ],
            highlight_index=0,
        ),
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        arms_length_plot(
            result["comparables_pli"],
            float(result["tested_pli"]),
            "Accepted Comparable Operating Margin Distribution",
            "Operating Margin (%)",
        ),
        use_container_width=True,
        config=PLOTLY_CONFIG,
    )

    st.dataframe(
        _range_summary_frame(range_dict, config.PLI_OPERATING_MARGIN),
        hide_index=True,
        use_container_width=True,
    )
    st.info(_position_sentence(position, config.PLI_OPERATING_MARGIN))

    st.dataframe(
        _benchmark_comparables_frame(
            result["comparables_detail"],
            config.PLI_OPERATING_MARGIN,
        ),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Weighted PLI": st.column_config.NumberColumn(
                "Weighted OM",
                format="%.2f%%",
            ),
            "Revenue EURm": st.column_config.NumberColumn(
                f"Revenue ({config.EURO_SIGN}M)",
                format=f"{config.EURO_SIGN} %.0fM",
            ),
        },
    )


def _render_sensitivity(
    tested_party: pd.DataFrame,
    accepted_comparables: pd.DataFrame,
    base_result: dict[str, object],
) -> None:
    """Render benchmark sensitivity scenarios."""

    include_adjustment = st.checkbox(
        "Include optional Pfizer FY22 EBIT normalization "
        f"({config.EURO_SIGN}{config.PFIZER_FY22_RESTRUCTURING_CHARGE_EUR_K:,.0f}k)",
        value=False,
    )
    scenarios = run_all_scenarios(
        tested_party_df=tested_party,
        comparables_df=accepted_comparables,
        include_fy22_adjustment=include_adjustment,
    )
    summary = scenario_summary_frame(scenarios)
    base_position = str(base_result["position"]["position"])
    summary["Conclusion changes"] = summary["Position"] != base_position
    display = summary.copy()
    for column in ["Tested PLI", "Q1", "Median", "Q3"]:
        display[column] = display.apply(
            lambda row, value_column=column: _format_pli_value(
                row[value_column],
                _pli_type_from_label(row["PLI"]),
            ),
            axis=1,
        )
    display["Position"] = display["Position"].map(_position_label)
    st.dataframe(display, hide_index=True, use_container_width=True)


def _render_pli_detail(result: dict[str, object]) -> None:
    """Render per-comparable yearly PLI detail."""

    detail = result["yearly_comparables_pli"].copy()
    pli_type = str(result["pli_type"])
    display = detail.copy()
    value_columns = [
        column
        for column in display.columns
        if column not in {config.COMPANY_NAME_COLUMN, config.COUNTRY_COLUMN}
    ]
    for column in value_columns:
        display[column] = display[column].apply(
            lambda value: _format_pli_value(value, pli_type)
        )

    st.dataframe(display, hide_index=True, use_container_width=True)
    for _, row in display.iterrows():
        with st.expander(str(row[config.COMPANY_NAME_COLUMN])):
            st.write(row.to_frame(name="Value"))


def _tested_party_trend_series(tested_party: pd.DataFrame) -> pd.Series:
    """Return Pfizer yearly Operating Margin in chronological order."""

    values = {}
    for year_suffix in reversed(config.YEAR_SUFFIXES):
        label = config.PERIOD_LABELS[year_suffix]
        values[label] = operating_margin(tested_party, year_suffix).iloc[0]
    return pd.Series(values)


def _tested_party_adjusted_points(tested_party: pd.DataFrame) -> dict[str, float]:
    """Return the FY22 restructuring-adjusted Operating Margin point."""

    adjusted = normalize_pfizer_fy22_ebit(tested_party)
    fy22_suffix = "Year - 2"
    return {
        config.PERIOD_LABELS[fy22_suffix]: float(
            operating_margin(adjusted, fy22_suffix).iloc[0]
        )
    }


def _range_summary_frame(
    range_dict: dict[str, object],
    pli_type: str,
) -> pd.DataFrame:
    """Return a formatted arm's-length range summary table."""

    rows = [
        ("N comparables", f"{int(range_dict['n']):,}"),
        ("Minimum", _format_pli_value(range_dict["min"], pli_type)),
        ("Q1 (25th percentile)", _format_pli_value(range_dict["q1"], pli_type)),
        ("Median", _format_pli_value(range_dict["median"], pli_type)),
        ("Q3 (75th percentile)", _format_pli_value(range_dict["q3"], pli_type)),
        ("Maximum", _format_pli_value(range_dict["max"], pli_type)),
        ("IQR width", _format_pli_spread(range_dict["iqr_width"], pli_type)),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def _benchmark_comparables_frame(
    detail: pd.DataFrame,
    pli_type: str,
) -> pd.DataFrame:
    """Return formatted comparable-company benchmark detail."""

    display = detail.copy()
    display["Revenue EURm"] = display[config.LATEST_REVENUE_COLUMN] / 1_000
    display["Weighted PLI"] = display["weighted_pli"]
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        display["Weighted PLI"] = display["Weighted PLI"] * 100
    display["IQR status"] = display["inside_iqr"].map(
        {True: "Inside IQR", False: "Outside IQR"}
    )
    return display[
        [
            config.COMPANY_NAME_COLUMN,
            config.COUNTRY_COLUMN,
            "Revenue EURm",
            "Weighted PLI",
            "IQR status",
            config.TRADE_DESCRIPTION_COLUMN,
        ]
    ]


def _position_sentence(position: dict[str, object], pli_type: str) -> str:
    """Return a human-readable tested-party positioning sentence."""

    position_label = _position_label(str(position["position"]))
    distance = float(position["distance_to_range"])
    direction = str(position["adjustment_direction"])
    distance_text = _format_pli_spread(abs(distance), pli_type)

    if position["position"] == "within_range":
        return (
            f"Position: {position_label}. Pfizer is within the interquartile "
            "arm's-length range; no adjustment is indicated by this test."
        )
    if position["position"] == "above_q3":
        return (
            f"Position: {position_label}. Pfizer is {distance_text} above Q3. "
            f"Suggested adjustment direction: {direction}."
        )
    if position["position"] == "below_q1":
        return (
            f"Position: {position_label}. Pfizer is {distance_text} below Q1. "
            f"Suggested adjustment direction: {direction}."
        )
    return "Position could not be determined due to missing data."


def _methodology_text() -> str:
    """Load methodology text for the Analysis tab."""

    methodology_path = config.PROJECT_ROOT / "docs" / "methodology.md"
    return methodology_path.read_text(encoding="utf-8")


def _about_page() -> None:
    """Render the about page."""

    st.markdown(_about_page_html(), unsafe_allow_html=True)


def _show_missing_data_message() -> None:
    """Show a friendly message when confidential Orbis exports are absent."""

    st.info("Place Orbis exports in data/raw/ to proceed.")


def _overview_hero_html(
    row: pd.Series,
    latest_revenue: object,
    latest_employees: object,
) -> str:
    """Return the Overview hero HTML with a subtle background logo."""

    logo_uri = _asset_data_uri(config.PFIZER_LOGO_PATH)
    company = html.escape(str(row.get(config.COMPANY_NAME_COLUMN, "Tested party")))
    country = html.escape(_display_value(row.get(config.COUNTRY_COLUMN)))
    revenue = html.escape(_format_revenue_millions(latest_revenue))
    employees = html.escape(_format_number(latest_employees))
    nace = html.escape(_format_nace(row.get(config.NACE_COLUMN)))
    characterization = html.escape(config.TESTED_PARTY_CHARACTERIZATION)

    return f"""
    <style>
      .overview-hero {{
        position: relative;
        min-height: 315px;
        padding: 0.65rem 0 2rem 0;
        overflow: hidden;
      }}
      .overview-watermark {{
        position: absolute;
        left: 50%;
        top: 48%;
        width: min(78vw, 980px);
        max-width: none;
        transform: translate(-50%, -50%) rotate(-6deg);
        opacity: 0.075;
        pointer-events: none;
        z-index: 0;
      }}
      .overview-content {{
        position: relative;
        z-index: 1;
      }}
      .overview-company {{
        margin: 1.35rem 0 1.45rem 0;
        font-size: 1.85rem;
        line-height: 1.15;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
      }}
      .overview-metrics {{
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 3.5rem;
        max-width: 980px;
        margin: 0 0 1.35rem 0;
      }}
      .overview-label {{
        margin-bottom: 0.45rem;
        font-size: 0.95rem;
        font-weight: 700;
      }}
      .overview-value {{
        font-size: clamp(2rem, 3.1vw, 2.75rem);
        line-height: 1.05;
        font-weight: 400;
        white-space: nowrap;
      }}
      .overview-note {{
        max-width: 980px;
        margin-top: 1.05rem;
        font-size: 1.05rem;
        line-height: 1.45;
        font-weight: 600;
      }}
      @media (max-width: 760px) {{
        .overview-hero {{
          min-height: 520px;
        }}
        .overview-watermark {{
          top: 60%;
          width: 120vw;
          opacity: 0.055;
        }}
        .overview-metrics {{
          grid-template-columns: 1fr;
          gap: 1.35rem;
        }}
      }}
    </style>
    <section class="overview-hero">
      <img class="overview-watermark" src="{logo_uri}" alt="" />
      <div class="overview-content">
        <div class="overview-company">{company}</div>
        <div class="overview-metrics">
          <div>
            <div class="overview-label">Country</div>
            <div class="overview-value">{country}</div>
          </div>
          <div>
            <div class="overview-label">Latest revenue</div>
            <div class="overview-value">{revenue}</div>
          </div>
          <div>
            <div class="overview-label">Employees (latest)</div>
            <div class="overview-value">{employees}</div>
          </div>
        </div>
        <div class="overview-note">NACE: {nace}</div>
        <div class="overview-note">{characterization}</div>
      </div>
    </section>
    """


def _about_page_html() -> str:
    """Return the About page HTML with context and a subtle watermark."""

    logo_uri = _asset_data_uri(config.PFIZER_LOGO_PATH)
    return f"""
    <style>
      .about-hero {{
        position: relative;
        min-height: 540px;
        padding: 0.35rem 0 2.5rem 0;
        overflow: hidden;
      }}
      .about-watermark {{
        position: absolute;
        left: 50%;
        top: 52%;
        width: min(82vw, 1040px);
        max-width: none;
        transform: translate(-50%, -50%) rotate(-6deg);
        opacity: 0.055;
        pointer-events: none;
        z-index: 0;
      }}
      .about-content {{
        position: relative;
        z-index: 1;
        max-width: 1120px;
      }}
      .about-title {{
        margin: 0.7rem 0 0.9rem 0;
        font-size: 2.65rem;
        line-height: 1.1;
        font-weight: 750;
        letter-spacing: 0;
      }}
      .about-lede {{
        max-width: 900px;
        margin: 0 0 1.8rem 0;
        font-size: 1.08rem;
        line-height: 1.55;
        font-weight: 500;
      }}
      .about-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1.35rem 2.4rem;
        max-width: 1040px;
        margin-top: 1.1rem;
      }}
      .about-section {{
        border-left: 3px solid rgba(0, 159, 218, 0.68);
        padding-left: 1rem;
      }}
      .about-section h3 {{
        margin: 0 0 0.45rem 0;
        font-size: 1.08rem;
        line-height: 1.25;
        font-weight: 760;
      }}
      .about-section p {{
        margin: 0;
        font-size: 0.98rem;
        line-height: 1.55;
      }}
      .about-footer {{
        max-width: 980px;
        margin-top: 1.8rem;
        padding-top: 1.15rem;
        border-top: 1px solid rgba(255, 255, 255, 0.16);
        font-size: 0.95rem;
        line-height: 1.55;
        opacity: 0.92;
      }}
      @media (max-width: 760px) {{
        .about-hero {{
          min-height: 820px;
        }}
        .about-watermark {{
          width: 128vw;
          opacity: 0.045;
        }}
        .about-grid {{
          grid-template-columns: 1fr;
          gap: 1.3rem;
        }}
      }}
    </style>
    <section class="about-hero">
      <img class="about-watermark" src="{logo_uri}" alt="" />
      <div class="about-content">
        <div class="about-title">About</div>
        <p class="about-lede">
          This is a student learning and portfolio project by Sisu Kosonen at TU
          München. It uses Pfizer Pharma GmbH as a realistic case to practice
          transfer pricing benchmarking, OECD TNMM logic, Orbis data handling,
          Python analytics, and Streamlit reporting. Public demos use artificial
          synthetic data rather than confidential Orbis exports.
        </p>
        <div class="about-grid">
          <div class="about-section">
            <h3>Why this project exists</h3>
            <p>
              The goal is to show how an accounting and finance student can
              translate transfer pricing methodology into a reproducible
              analytical workflow suitable for Big 4 interview discussion.
            </p>
          </div>
          <div class="about-section">
            <h3>Methodological focus</h3>
            <p>
              The app applies the Transactional Net Margin Method. Operating
              Margin is the primary PLI for the LRD-SM profile, with Berry Ratio
              and ROCE used as secondary checks.
            </p>
          </div>
          <div class="about-section">
            <h3>Data boundaries</h3>
            <p>
              The private workflow uses local Orbis exports for Pfizer Pharma
              GmbH and 55 EU/EFTA NACE 4646 candidate comparables. Public demo
              mode uses artificial synthetic workbooks, so screenshots and
              demos can be shared without exposing licensed source data.
            </p>
          </div>
          <div class="about-section">
            <h3>What the app produces</h3>
            <p>
              The workflow documents the rejection cascade, arm's-length range,
              sensitivity scenarios, comparable-level PLI detail, and an Excel
              workpaper that can be reviewed like a compact TP file.
            </p>
          </div>
        </div>
        <div class="about-footer">
          This is not a statutory transfer pricing report or professional tax
          opinion. It is an educational portfolio project designed to make the
          reasoning, assumptions, limitations, and calculations visible.
        </div>
      </div>
    </section>
    """


def _asset_data_uri(path: object) -> str:
    """Return an SVG asset as an inline data URI."""

    raw_bytes = Path(path).read_bytes()
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


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


def _format_pli_value(value: object, pli_type: str) -> str:
    """Format a PLI value for display."""

    if pd.isna(value):
        return "n/a"
    numeric_value = float(value)
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        return f"{numeric_value * 100:.2f}%"
    return f"{numeric_value:.2f}x"


def _format_pli_spread(value: object, pli_type: str) -> str:
    """Format a PLI distance or range width."""

    if pd.isna(value):
        return "n/a"
    numeric_value = float(value)
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        return f"{numeric_value * 100:.2f} pp"
    return f"{numeric_value:.2f}x"


def _format_iqr_label(range_dict: dict[str, object], pli_type: str) -> str:
    """Format Q1-Q3 as a compact Streamlit metric label."""

    return (
        f"{_format_pli_value(range_dict['q1'], pli_type)} - "
        f"{_format_pli_value(range_dict['q3'], pli_type)}"
    )


def _position_label(position: str) -> str:
    """Return a human-readable position label."""

    labels = {
        "below_q1": "Below Q1",
        "within_range": "Within range",
        "above_q3": "Above Q3",
        "not_available": "Not available",
    }
    return labels.get(position, position)


def _pli_type_from_label(label: str) -> str:
    """Infer the configured PLI key from a display label."""

    for pli_type, pli_label in config.PLI_LABELS.items():
        if label == pli_label:
            return pli_type
    return config.PLI_OPERATING_MARGIN


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
        margin={"l": 150, "r": 20, "t": 6, "b": 8},
        height=390,
        font={"size": 11},
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
