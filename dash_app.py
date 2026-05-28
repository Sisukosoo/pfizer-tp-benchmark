"""Dash executive dashboard for the Pfizer transfer pricing benchmark."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html

from src import config
from src.benchmarking import run_benchmark
from src.comparables import load_decisions
from src.data_loader import load_comparables, load_tested_party
from src.pli_calculator import operating_margin
from src.reporting import (
    REPORT_FILENAME,
    build_excel_report,
    build_report_context,
)
from src.sensitivity import (
    PERIOD_SCENARIOS,
    POOL_SCENARIOS,
    apply_pool_scenario,
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

APP_TITLE = "Pfizer TP Benchmark - Dash"
GRAPH_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}

app = Dash(__name__, title=APP_TITLE, suppress_callback_exceptions=True)
server = app.server

app.index_string = """
<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
      body {
        margin: 0;
        background: #070B10;
        color: #F8FAFC;
        font-family: Inter, Arial, sans-serif;
      }
      .app-shell {
        min-height: 100vh;
        display: grid;
        grid-template-columns: 320px minmax(0, 1fr);
      }
      .sidebar {
        position: sticky;
        top: 0;
        height: 100vh;
        padding: 28px 24px;
        background: #111827;
        border-right: 1px solid #263244;
        box-sizing: border-box;
        overflow-y: auto;
      }
      .sidebar h2 {
        margin: 0 0 6px 0;
        font-size: 24px;
        line-height: 1.2;
      }
      .sidebar-note {
        color: #AAB4C3;
        line-height: 1.45;
        margin: 0 0 22px 0;
        font-size: 13px;
      }
      .control-group {
        margin: 18px 0;
      }
      .control-label {
        display: block;
        margin-bottom: 8px;
        color: #E5E7EB;
        font-weight: 750;
        font-size: 13px;
      }
      .mode-radio label,
      .adjustment-check label {
        display: block;
        margin: 8px 0;
        color: #D5DEE9;
      }
      .Select-control,
      .Select-menu-outer {
        background: #0B1117 !important;
        border-color: #263244 !important;
        color: #F8FAFC !important;
      }
      .Select-value-label,
      .Select-placeholder,
      .Select-input input {
        color: #F8FAFC !important;
      }
      .Select-menu-outer * {
        color: #111827 !important;
      }
      #download-button {
        width: 100%;
        margin: 22px 0 12px 0;
        padding: 12px 14px;
        border: 1px solid #38BDF8;
        background: #075985;
        color: white;
        border-radius: 6px;
        font-weight: 750;
        cursor: pointer;
      }
      .main {
        padding: 24px 36px 64px 36px;
        box-sizing: border-box;
      }
      .status {
        display: inline-flex;
        gap: 6px;
        padding: 7px 11px;
        border-radius: 999px;
        margin-bottom: 18px;
        background: #102033;
        color: #CFE8FF;
        border: 1px solid #244563;
        font-size: 13px;
      }
      .hero {
        position: relative;
        min-height: 210px;
        overflow: hidden;
        margin-bottom: 22px;
        border-bottom: 1px solid rgba(255,255,255,0.12);
      }
      .watermark {
        position: absolute;
        right: 0;
        top: -20px;
        width: min(52vw, 680px);
        opacity: 0.055;
        transform: rotate(-6deg);
        pointer-events: none;
      }
      .hero-content {
        position: relative;
        z-index: 1;
        max-width: 940px;
        padding: 26px 0 38px 0;
      }
      .eyebrow {
        text-transform: uppercase;
        color: #38BDF8;
        font-size: 12px;
        font-weight: 850;
        letter-spacing: 0.08em;
      }
      h1 {
        font-size: 44px;
        margin: 8px 0 12px 0;
        letter-spacing: 0;
        line-height: 1.1;
      }
      .lede {
        max-width: 820px;
        color: #D5DEE9;
        line-height: 1.55;
        font-size: 17px;
      }
      .metric-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 14px;
        margin-bottom: 20px;
      }
      .metric-card,
      .insight-card,
      .panel {
        border: 1px solid #243042;
        background: #0B1117;
        border-radius: 8px;
        box-sizing: border-box;
      }
      .metric-card {
        padding: 16px;
      }
      .metric-card p {
        margin: 0 0 7px 0;
        color: #AAB4C3;
        font-weight: 750;
        font-size: 13px;
      }
      .metric-card h3 {
        margin: 0;
        font-size: 26px;
        font-weight: 650;
      }
      .badge {
        display: inline-flex;
        padding: 6px 10px;
        border-radius: 999px;
        font-weight: 800;
        font-size: 12px;
        border: 1px solid #14532D;
        background: rgba(22, 163, 74, 0.16);
        color: #BBF7D0;
      }
      .badge-above_q3,
      .badge-below_q1 {
        border-color: #7F1D1D;
        background: rgba(220, 38, 38, 0.16);
        color: #FECACA;
      }
      .dashboard-grid {
        display: grid;
        grid-template-columns: minmax(0, 1.45fr) minmax(340px, 0.75fr);
        gap: 18px;
        margin-bottom: 18px;
      }
      .panel {
        padding: 14px;
        overflow: hidden;
      }
      .panel h2,
      .insight-card h2 {
        margin: 0 0 12px 0;
        font-size: 19px;
      }
      .insight-card {
        padding: 18px;
        line-height: 1.55;
      }
      .insight-card p {
        color: #D5DEE9;
      }
      .two-column {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 18px;
        margin-bottom: 18px;
      }
      .table-section {
        margin-top: 20px;
      }
      .table-section h2 {
        margin: 0 0 12px 0;
      }
      .dash-graph {
        border-radius: 6px;
        overflow: hidden;
      }
      .error-panel {
        max-width: 760px;
        padding: 28px;
        border: 1px solid #7F1D1D;
        background: rgba(127, 29, 29, 0.18);
        border-radius: 8px;
      }
      @media (max-width: 1100px) {
        .app-shell { grid-template-columns: 1fr; }
        .sidebar { position: relative; height: auto; }
        .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .dashboard-grid,
        .two-column { grid-template-columns: 1fr; }
        h1 { font-size: 34px; }
      }
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>
      {%config%}
      {%scripts%}
      {%renderer%}
    </footer>
  </body>
</html>
"""


def layout() -> html.Div:
    """Return the Dash app layout."""

    initial_mode = config.active_data_mode()
    return html.Div(
        [
            dcc.Download(id="excel-download"),
            html.Aside(
                [
                    html.H2("Pfizer TP Benchmark"),
                    html.P(
                        "Interactive Dash prototype using the same benchmark engine.",
                        className="sidebar-note",
                    ),
                    _radio_control(
                        "Data mode",
                        "data-mode",
                        [
                            ("Synthetic demo", config.DATA_MODE_SYNTHETIC),
                            ("Real local Orbis", config.DATA_MODE_REAL),
                        ],
                        initial_mode,
                    ),
                    _dropdown_control(
                        "Profit Level Indicator",
                        "pli-select",
                        [
                            (config.PLI_LABELS[option], option)
                            for option in config.PLI_OPTIONS
                        ],
                        config.PLI_OPERATING_MARGIN,
                    ),
                    _dropdown_control(
                        "Benchmark period",
                        "period-select",
                        [(name, name) for name in PERIOD_SCENARIOS],
                        "3-year weighted (FY22-FY24, base)",
                    ),
                    _dropdown_control(
                        "Comparable pool",
                        "pool-select",
                        [(name, name) for name in POOL_SCENARIOS],
                        "All accepted comparables",
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Tested-party adjustment",
                                className="control-label",
                            ),
                            dcc.Checklist(
                                id="adjustment-check",
                                options=[
                                    {
                                        "label": "Normalize FY22 EBIT restructuring",
                                        "value": "fy22",
                                    }
                                ],
                                value=[],
                                className="adjustment-check",
                            ),
                        ],
                        className="control-group",
                    ),
                    html.Button("Download Excel workpaper", id="download-button"),
                    html.P(
                        "Controls update the dashboard live. Decision editing remains "
                        "in the Streamlit workpaper app.",
                        className="sidebar-note",
                    ),
                ],
                className="sidebar",
            ),
            html.Main(
                [
                    html.Div(id="status-banner"),
                    html.Div(id="app-content"),
                ],
                className="main",
            ),
        ],
        className="app-shell",
    )


app.layout = layout


@app.callback(
    Output("status-banner", "children"),
    Output("app-content", "children"),
    Input("data-mode", "value"),
    Input("pli-select", "value"),
    Input("period-select", "value"),
    Input("pool-select", "value"),
    Input("adjustment-check", "value"),
)
def render_app(
    data_mode: str,
    pli_type: str,
    period_name: str,
    pool_name: str,
    adjustments: list[str],
) -> tuple[Any, Any]:
    """Render the interactive executive dashboard."""

    try:
        context = _load_context(data_mode)
        view = _scenario_view(
            context,
            pli_type,
            period_name,
            pool_name,
            "fy22" in adjustments,
        )
    except (FileNotFoundError, ValueError) as error:
        return _status_banner(data_mode), _error_panel(str(error))
    return _status_banner(data_mode), _dashboard(context, view)


@app.callback(
    Output("excel-download", "data"),
    Input("download-button", "n_clicks"),
    State("data-mode", "value"),
    prevent_initial_call=True,
)
def download_excel(_: int, data_mode: str) -> dict[str, Any]:
    """Return the Excel workpaper download for the selected mode."""

    tested_party = load_tested_party(data_mode)
    raw_comparables = load_comparables(data_mode)
    decisions = load_decisions(data_mode=data_mode)
    report_bytes = build_excel_report(tested_party, raw_comparables, decisions)
    return dcc.send_bytes(lambda buffer: buffer.write(report_bytes), REPORT_FILENAME)


def _load_context(data_mode: str) -> dict[str, Any]:
    """Load benchmark context for Dash."""

    tested_party_path = config.resolve_tested_party_path(data_mode)
    comparables_path = config.resolve_comparables_path(data_mode)
    if not tested_party_path.exists() or not comparables_path.exists():
        raise FileNotFoundError(f"Data files for mode '{data_mode}' are not available.")

    tested_party = load_tested_party(data_mode)
    raw_comparables = load_comparables(data_mode)
    decisions = load_decisions(data_mode=data_mode)
    return build_report_context(tested_party, raw_comparables, decisions)


def _scenario_view(
    context: dict[str, Any],
    pli_type: str,
    period_name: str,
    pool_name: str,
    normalize_fy22: bool,
) -> dict[str, Any]:
    """Return benchmark output for the current Dash controls."""

    years = PERIOD_SCENARIOS.get(period_name, config.DEFAULT_BENCHMARK_PERIOD)
    tested_party = context["tested_party"]
    if normalize_fy22:
        tested_party = normalize_pfizer_fy22_ebit(tested_party)
    comparables = apply_pool_scenario(context["accepted"], pool_name)
    result = run_benchmark(
        tested_party_df=tested_party,
        comparables_df=comparables,
        pli_type=pli_type,
        years=years,
    )
    return {
        "tested_party": tested_party,
        "comparables": comparables,
        "result": result,
        "period_name": period_name,
        "pool_name": pool_name,
        "normalize_fy22": normalize_fy22,
    }


def _dashboard(context: dict[str, Any], view: dict[str, Any]) -> html.Div:
    """Return the main dashboard content."""

    result = view["result"]
    range_dict = result["range"]
    stats = context["cascade_stats"]
    tested_party = view["tested_party"]
    comparables = view["comparables"]
    tested_revenue = pd.to_numeric(
        tested_party.iloc[0].get(config.LATEST_REVENUE_COLUMN),
        errors="coerce",
    )
    sensitivity = scenario_summary_frame(
        run_all_scenarios(tested_party, comparables, include_fy22_adjustment=True)
    )
    pli_label = str(result["pli_label"])

    return html.Div(
        [
            _hero(context, view),
            html.Div(
                [
                    _metric_card(
                        "Tested PLI",
                        _format_pli(result["tested_pli"], result["pli_type"]),
                    ),
                    _metric_card(
                        "Q1", _format_pli(range_dict["q1"], result["pli_type"])
                    ),
                    _metric_card(
                        "Median", _format_pli(range_dict["median"], result["pli_type"])
                    ),
                    _metric_card(
                        "Q3", _format_pli(range_dict["q3"], result["pli_type"])
                    ),
                    _metric_card("Comparable N", f"{range_dict['n']:,}"),
                ],
                className="metric-grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2(f"Arm's-Length Range - {pli_label}"),
                            _graph(
                                arms_length_plot(
                                    result["comparables_pli"],
                                    float(result["tested_pli"]),
                                    f"{pli_label} Range",
                                    (
                                        f"{pli_label} (%)"
                                        if config.PLI_PERCENT_FORMAT.get(
                                            result["pli_type"], False
                                        )
                                        else pli_label
                                    ),
                                )
                            ),
                        ],
                        className="panel",
                    ),
                    _insight_card(context, view),
                ],
                className="dashboard-grid",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Comparable Ranking"),
                            _graph(
                                sorted_comparables_bar(
                                    result["comparables_detail"],
                                    float(result["tested_pli"]),
                                    range_dict,
                                    title="Accepted Comparables Weighted PLI",
                                )
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H2("Sensitivity Ranges"),
                            _graph(sensitivity_range_plot(sensitivity)),
                        ],
                        className="panel",
                    ),
                ],
                className="two-column",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.H2("Scale Check"),
                            _graph(
                                revenue_vs_margin_scatter(
                                    result["comparables_detail"],
                                    float(tested_revenue),
                                    float(result["tested_pli"]),
                                )
                            ),
                        ],
                        className="panel",
                    ),
                    html.Div(
                        [
                            html.H2("Tested Party Trend"),
                            _graph(
                                tested_party_trend_plot(
                                    _tested_party_trend_series(tested_party),
                                    title="Operating Margin Trend",
                                )
                            ),
                        ],
                        className="panel",
                    ),
                ],
                className="two-column",
            ),
            html.Div(
                [
                    html.H2("Accepted Comparables"),
                    _table(
                        _selected_comparables_frame(
                            result["comparables_detail"], result["pli_type"]
                        )
                    ),
                ],
                className="table-section",
            ),
            html.Div(
                [
                    html.H2("Rejection Cascade Snapshot"),
                    _table(_cascade_frame(stats)),
                ],
                className="table-section",
            ),
        ]
    )


def _hero(context: dict[str, Any], view: dict[str, Any]) -> html.Section:
    """Return the Dash hero block."""

    row = context["tested_party"].iloc[0]
    result = view["result"]
    figure_status = "FY22 adjusted" if view["normalize_fy22"] else "Reported figures"
    return html.Section(
        [
            html.Img(
                src=_asset_data_uri(config.PFIZER_LOGO_PATH), className="watermark"
            ),
            html.Div(
                [
                    html.P(
                        "Interactive transfer pricing dashboard", className="eyebrow"
                    ),
                    html.H1(row.get(config.COMPANY_NAME_COLUMN, "Tested party")),
                    html.P(
                        f"{result['pli_label']} over {result['period_label']} | "
                        f"{view['pool_name']} | {figure_status}",
                        className="lede",
                    ),
                ],
                className="hero-content",
            ),
        ],
        className="hero",
    )


def _insight_card(context: dict[str, Any], view: dict[str, Any]) -> html.Div:
    """Return conclusion and control context."""

    result = view["result"]
    position = str(result["position"]["position"])
    stats = context["cascade_stats"]
    return html.Div(
        [
            html.H2("Executive Readout"),
            html.Span(_position_label(position), className=f"badge badge-{position}"),
            html.P(
                f"The selected view tests {result['pli_label']} using "
                f"{result['period_label']}. The candidate pool starts with "
                f"{stats['raw']} companies and the current scenario includes "
                f"{result['range']['n']} accepted comparables."
            ),
            html.P(_position_sentence(result)),
            html.P(
                "Use the controls in the sidebar to test period, PLI, pool, and "
                "tested-party adjustment assumptions without changing the underlying "
                "workpaper state."
            ),
        ],
        className="insight-card",
    )


def _status_banner(data_mode: str) -> html.Div:
    """Return a compact data-mode status banner."""

    mode_label = (
        "Synthetic public demo"
        if data_mode == config.DATA_MODE_SYNTHETIC
        else "Real local Orbis"
    )
    return html.Div(
        [html.Strong("Data mode: "), html.Span(mode_label)],
        className=f"status status-{data_mode}",
    )


def _metric_card(label: str, value: str) -> html.Div:
    """Return a dashboard metric card."""

    return html.Div([html.P(label), html.H3(value)], className="metric-card")


def _radio_control(
    label: str,
    component_id: str,
    options: list[tuple[str, str]],
    value: str,
) -> html.Div:
    """Return a styled radio control."""

    return html.Div(
        [
            html.Label(label, className="control-label"),
            dcc.RadioItems(
                id=component_id,
                options=[
                    {"label": item_label, "value": item_value}
                    for item_label, item_value in options
                ],
                value=value,
                className="mode-radio",
            ),
        ],
        className="control-group",
    )


def _dropdown_control(
    label: str,
    component_id: str,
    options: list[tuple[str, str]],
    value: str,
) -> html.Div:
    """Return a styled dropdown control."""

    return html.Div(
        [
            html.Label(label, className="control-label"),
            dcc.Dropdown(
                id=component_id,
                options=[
                    {"label": item_label, "value": item_value}
                    for item_label, item_value in options
                ],
                value=value,
                clearable=False,
            ),
        ],
        className="control-group",
    )


def _table(dataframe: pd.DataFrame) -> dash_table.DataTable:
    """Return a Dash DataTable with dashboard defaults."""

    display = dataframe.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].round(4)
    return dash_table.DataTable(
        data=display.to_dict("records"),
        columns=[
            {"name": str(column), "id": str(column)} for column in display.columns
        ],
        page_size=8,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_cell={
            "backgroundColor": "#0B1117",
            "color": "#E5E7EB",
            "border": "1px solid #1F2937",
            "fontFamily": "Inter, Arial, sans-serif",
            "fontSize": "13px",
            "padding": "9px",
            "whiteSpace": "normal",
            "height": "auto",
            "textAlign": "left",
        },
        style_header={
            "backgroundColor": "#111827",
            "fontWeight": "700",
            "color": "#FFFFFF",
        },
    )


def _graph(figure: go.Figure) -> dcc.Graph:
    """Return a Dash graph with the dashboard visual theme applied."""

    return dcc.Graph(
        figure=_style_figure(figure),
        config=GRAPH_CONFIG,
        className="dash-graph",
    )


def _style_figure(figure: go.Figure) -> go.Figure:
    """Apply a dark executive-dashboard theme to a Plotly figure."""

    styled = go.Figure(figure)
    styled.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0B1117",
        plot_bgcolor="#111827",
        font={
            "family": "Inter, Arial, sans-serif",
            "color": "#E5E7EB",
            "size": 12,
        },
        title={
            "font": {"color": "#F8FAFC", "size": 15},
            "x": 0.02,
            "xanchor": "left",
        },
        legend={
            "bgcolor": "rgba(11, 17, 23, 0)",
            "font": {"color": "#D5DEE9", "size": 11},
        },
        margin={
            "l": max(int(styled.layout.margin.l or 0), 30),
            "r": max(int(styled.layout.margin.r or 0), 24),
            "t": max(int(styled.layout.margin.t or 0), 54),
            "b": max(int(styled.layout.margin.b or 0), 45),
        },
    )
    styled.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.16)",
        zerolinecolor="rgba(226, 232, 240, 0.34)",
        linecolor="rgba(148, 163, 184, 0.32)",
        tickfont={"color": "#CBD5E1", "size": 11},
        title_font={"color": "#E5E7EB", "size": 12},
        automargin=True,
    )
    styled.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.12)",
        zerolinecolor="rgba(226, 232, 240, 0.28)",
        linecolor="rgba(148, 163, 184, 0.28)",
        tickfont={"color": "#CBD5E1", "size": 11},
        title_font={"color": "#E5E7EB", "size": 12},
        automargin=True,
    )
    return styled


def _selected_comparables_frame(detail: pd.DataFrame, pli_type: str) -> pd.DataFrame:
    """Return selected-scenario comparable table."""

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
        ]
    ]


def _cascade_frame(stats: dict[str, Any]) -> pd.DataFrame:
    """Return rejection cascade category table."""

    rows = [
        {"Stage": "Raw candidates", "Count": stats["raw"]},
        {"Stage": "Accepted comparables", "Count": stats["accepted"]},
        {"Stage": "Rejected total", "Count": stats["rejected"]},
    ]
    rejected_by_category = stats.get("rejected_by_category", {})
    if isinstance(rejected_by_category, dict):
        for category in config.CATEGORY_DISPLAY_ORDER:
            rows.append(
                {
                    "Stage": config.REJECT_CATEGORIES[category]["label"],
                    "Count": rejected_by_category.get(category, 0),
                }
            )
    return pd.DataFrame(rows)


def _tested_party_trend_series(tested_party: pd.DataFrame) -> pd.Series:
    """Return yearly Operating Margin in chronological order."""

    values = {}
    for year_suffix in reversed(config.YEAR_SUFFIXES):
        values[config.PERIOD_LABELS[year_suffix]] = operating_margin(
            tested_party,
            year_suffix,
        ).iloc[0]
    return pd.Series(values)


def _asset_data_uri(path: Path) -> str:
    """Return an SVG asset as an inline data URI."""

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _format_pli(value: object, pli_type: str) -> str:
    """Format a PLI value for display."""

    if pd.isna(value):
        return "n/a"
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        return f"{float(value) * 100:.2f}%"
    return f"{float(value):.2f}x"


def _position_label(position: str) -> str:
    """Return a human-readable tested-party position label."""

    labels = {
        "below_q1": "Below Q1",
        "within_range": "Within range",
        "above_q3": "Above Q3",
        "not_available": "Not available",
    }
    return labels.get(position, position)


def _position_sentence(result: dict[str, Any]) -> str:
    """Return a short result sentence for the insight card."""

    position = result["position"]["position"]
    pli_type = result["pli_type"]
    distance = result["position"]["distance_to_range"]
    if position == "within_range":
        return "The tested party falls within the interquartile arm's-length range."
    if position == "above_q3":
        return (
            "The tested party is "
            f"{abs(float(distance)) * 100:.2f} percentage points above Q3."
            if config.PLI_PERCENT_FORMAT.get(pli_type, False)
            else "The tested party is above Q3."
        )
    if position == "below_q1":
        return (
            "The tested party is "
            f"{abs(float(distance)) * 100:.2f} percentage points below Q1."
            if config.PLI_PERCENT_FORMAT.get(pli_type, False)
            else "The tested party is below Q1."
        )
    return "The tested-party position could not be determined."


def _error_panel(message: str) -> html.Div:
    """Return an error panel for unavailable data."""

    return html.Div(
        [
            html.H1("Data unavailable"),
            html.P(message),
            html.P(
                "Use synthetic mode for public demo data, or place private Orbis "
                "exports and decisions locally for real-data mode."
            ),
        ],
        className="error-panel",
    )


if __name__ == "__main__":
    app.run(debug=True, port=8050)
