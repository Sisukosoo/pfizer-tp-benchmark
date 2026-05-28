"""Dash entry point for the Pfizer transfer pricing benchmark app.

This app is a parallel UI experiment that reuses the same calculation engine as
the Streamlit app. It is intentionally read-only in the first Dash iteration.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import pandas as pd
from dash import Dash, Input, Output, State, dash_table, dcc, html

from src import config
from src.comparables import load_decisions
from src.data_loader import load_comparables, load_tested_party
from src.pli_calculator import operating_margin
from src.reporting import (
    REPORT_FILENAME,
    accepted_comparables_frame,
    build_excel_report,
    build_report_context,
    executive_conclusion,
    range_frame,
    rejected_candidates_frame,
    sensitivity_frame,
)
from src.sensitivity import run_all_scenarios, scenario_summary_frame
from src.visualizations import (
    arms_length_plot,
    revenue_vs_margin_scatter,
    sensitivity_range_plot,
    sorted_comparables_bar,
    tested_party_trend_plot,
)

APP_TITLE = "Pfizer TP Benchmark - Dash"


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
          background: #080D13;
          color: #F8FAFC;
          font-family: Inter, Arial, sans-serif;
        }
        .app-shell {
          min-height: 100vh;
          display: grid;
          grid-template-columns: 290px minmax(0, 1fr);
        }
        .sidebar {
          position: sticky;
          top: 0;
          height: 100vh;
          padding: 32px 26px;
          background: #111827;
          border-right: 1px solid #243042;
          box-sizing: border-box;
        }
        .sidebar h2 {
          margin: 0 0 8px 0;
          font-size: 24px;
        }
        .sidebar-note {
          color: #AAB4C3;
          line-height: 1.45;
          margin-bottom: 28px;
        }
        .control-label {
          display: block;
          margin-bottom: 10px;
          font-weight: 700;
        }
        .mode-radio label {
          display: block;
          margin-bottom: 12px;
        }
        #download-button {
          width: 100%;
          margin: 22px 0;
          padding: 12px 14px;
          border: 1px solid #38BDF8;
          background: #075985;
          color: white;
          border-radius: 6px;
          font-weight: 700;
          cursor: pointer;
        }
        .main {
          padding: 28px 42px 70px 42px;
          box-sizing: border-box;
        }
        .status {
          display: inline-flex;
          gap: 6px;
          padding: 8px 12px;
          border-radius: 999px;
          margin-bottom: 22px;
          background: #102033;
          color: #CFE8FF;
          border: 1px solid #244563;
          font-size: 13px;
        }
        .hero {
          position: relative;
          min-height: 250px;
          overflow: hidden;
          border-bottom: 1px solid rgba(255,255,255,0.12);
          margin-bottom: 28px;
        }
        .watermark {
          position: absolute;
          right: 2%;
          top: 0;
          width: min(58vw, 720px);
          opacity: 0.055;
          transform: rotate(-6deg);
          pointer-events: none;
        }
        .hero-content {
          position: relative;
          z-index: 1;
          max-width: 920px;
          padding: 34px 0 46px 0;
        }
        .eyebrow {
          text-transform: uppercase;
          color: #38BDF8;
          font-size: 13px;
          font-weight: 800;
          letter-spacing: 0.08em;
        }
        h1 {
          font-size: 48px;
          margin: 10px 0 16px 0;
          letter-spacing: 0;
        }
        .lede {
          max-width: 780px;
          color: #D5DEE9;
          line-height: 1.55;
          font-size: 18px;
        }
        .metric-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 16px;
          margin-bottom: 28px;
        }
        .metric-card {
          padding: 18px;
          border: 1px solid #243042;
          background: #0B1117;
          border-radius: 8px;
        }
        .metric-card p {
          margin: 0 0 8px 0;
          color: #AAB4C3;
          font-weight: 700;
        }
        .metric-card h3 {
          margin: 0;
          font-size: 30px;
          font-weight: 650;
        }
        .section {
          margin: 24px 0;
        }
        .section h2 {
          margin-bottom: 12px;
        }
        .error-panel {
          max-width: 760px;
          padding: 28px;
          border: 1px solid #7F1D1D;
          background: rgba(127, 29, 29, 0.18);
          border-radius: 8px;
        }
        @media (max-width: 900px) {
          .app-shell { grid-template-columns: 1fr; }
          .sidebar { position: relative; height: auto; }
          .metric-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
          h1 { font-size: 36px; }
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
                    html.P("Dash by Plotly prototype", className="sidebar-note"),
                    html.Label("Data mode", className="control-label"),
                    dcc.RadioItems(
                        id="data-mode",
                        options=[
                            {
                                "label": "Synthetic demo",
                                "value": config.DATA_MODE_SYNTHETIC,
                            },
                            {
                                "label": "Real local Orbis",
                                "value": config.DATA_MODE_REAL,
                            },
                        ],
                        value=initial_mode,
                        className="mode-radio",
                    ),
                    html.Button("Download Excel workpaper", id="download-button"),
                    html.P(
                        "Synthetic mode is safe for public demos and screenshots.",
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
)
def render_app(data_mode: str) -> tuple[Any, Any]:
    """Render the Dash app body for the selected data mode."""

    try:
        context = _load_context(data_mode)
    except (FileNotFoundError, ValueError) as error:
        return _status_banner(data_mode), _error_panel(str(error))
    return _status_banner(data_mode), _dashboard(context)


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


def _dashboard(context: dict[str, Any]) -> html.Div:
    """Return the main dashboard content."""

    base_result = context["base_result"]
    stats = context["cascade_stats"]
    tested_party = context["tested_party"]
    accepted = context["accepted"]
    tested_revenue = pd.to_numeric(
        tested_party.iloc[0].get(config.LATEST_REVENUE_COLUMN),
        errors="coerce",
    )
    sensitivity = scenario_summary_frame(
        run_all_scenarios(tested_party, accepted, include_fy22_adjustment=True)
    )
    return html.Div(
        [
            _hero(context),
            html.Div(
                [
                    _metric_card("Raw candidates", f"{stats['raw']:,}"),
                    _metric_card("Accepted", f"{stats['accepted']:,}"),
                    _metric_card("Rejected", f"{stats['rejected']:,}"),
                    _metric_card(
                        "Pfizer OM",
                        _format_percent(base_result["tested_pli"]),
                    ),
                ],
                className="metric-grid",
            ),
            dcc.Tabs(
                [
                    dcc.Tab(
                        label="Overview",
                        children=[
                            _section(
                                "Executive conclusion",
                                html.P(executive_conclusion(context)),
                            ),
                            _table(range_frame(context)),
                        ],
                    ),
                    dcc.Tab(
                        label="Analysis",
                        children=[
                            dcc.Graph(
                                figure=arms_length_plot(
                                    base_result["comparables_pli"],
                                    float(base_result["tested_pli"]),
                                    "Arm's-Length Range - Operating Margin",
                                    "Operating Margin (%)",
                                )
                            ),
                            dcc.Graph(
                                figure=sorted_comparables_bar(
                                    base_result["comparables_detail"],
                                    float(base_result["tested_pli"]),
                                    base_result["range"],
                                )
                            ),
                        ],
                    ),
                    dcc.Tab(
                        label="Sensitivity",
                        children=[
                            dcc.Graph(figure=sensitivity_range_plot(sensitivity)),
                            _table(sensitivity_frame(context)),
                        ],
                    ),
                    dcc.Tab(
                        label="Comparables",
                        children=[
                            _section(
                                "Accepted comparables",
                                _table(accepted_comparables_frame(context)),
                            ),
                            _section(
                                "Rejected candidates",
                                _table(rejected_candidates_frame(context).head(20)),
                            ),
                        ],
                    ),
                    dcc.Tab(
                        label="Context",
                        children=[
                            dcc.Graph(
                                figure=tested_party_trend_plot(
                                    _tested_party_trend_series(tested_party),
                                    title="Tested Party Operating Margin Trend",
                                )
                            ),
                            dcc.Graph(
                                figure=revenue_vs_margin_scatter(
                                    base_result["comparables_detail"],
                                    float(tested_revenue),
                                    float(base_result["tested_pli"]),
                                )
                            ),
                        ],
                    ),
                ],
                className="tabs",
            ),
        ]
    )


def _hero(context: dict[str, Any]) -> html.Section:
    """Return the Dash hero block."""

    row = context["tested_party"].iloc[0]
    return html.Section(
        [
            html.Img(
                src=_asset_data_uri(config.PFIZER_LOGO_PATH), className="watermark"
            ),
            html.Div(
                [
                    html.P("Transfer pricing benchmark", className="eyebrow"),
                    html.H1(row.get(config.COMPANY_NAME_COLUMN, "Tested party")),
                    html.P(
                        "TNMM workflow combining FAR context, comparable-company "
                        "screening, PLI calculation, sensitivity analysis, and "
                        "Excel workpaper output.",
                        className="lede",
                    ),
                ],
                className="hero-content",
            ),
        ],
        className="hero",
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


def _section(title: str, children: Any) -> html.Section:
    """Return a titled content section."""

    return html.Section([html.H2(title), children], className="section")


def _table(dataframe: pd.DataFrame) -> dash_table.DataTable:
    """Return a Dash DataTable with sane defaults."""

    display = dataframe.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].round(4)
    return dash_table.DataTable(
        data=display.to_dict("records"),
        columns=[
            {"name": str(column), "id": str(column)} for column in display.columns
        ],
        page_size=10,
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
        },
        style_header={
            "backgroundColor": "#111827",
            "fontWeight": "700",
            "color": "#FFFFFF",
        },
    )


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


def _format_percent(value: object) -> str:
    """Format a decimal as a percent string."""

    if pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.2f}%"


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
