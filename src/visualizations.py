"""Plotly visualizations for benchmark results."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src import config


def arms_length_plot(
    comparables_pli: pd.Series,
    tested_pli: float,
    title: str,
    pli_label: str = "Operating Margin (%)",
) -> go.Figure:
    """Return a Plotly figure showing range and tested-party position.

    Args:
        comparables_pli: Comparable-company PLI observations.
        tested_pli: Tested-party PLI observation.
        title: Chart title.
        pli_label: X-axis label.

    Returns:
        Plotly box-and-marker figure.
    """

    valid = pd.to_numeric(comparables_pli, errors="coerce").dropna()
    scale = 100 if "%" in pli_label else 1
    values = valid * scale
    tested_value = tested_pli * scale

    figure = go.Figure()
    if values.empty:
        figure.update_layout(title=title)
        return figure

    q1, median, q3 = np.percentile(
        values.to_numpy(),
        [25, 50, 75],
        method=config.QUARTILE_METHOD,
    )
    axis_min, axis_max = _axis_bounds(values, tested_value)

    figure.add_shape(
        type="rect",
        x0=axis_min,
        x1=q1,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        fillcolor="rgba(239, 68, 68, 0.10)",
        line={"width": 0},
        layer="below",
    )
    figure.add_shape(
        type="rect",
        x0=q1,
        x1=q3,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        fillcolor="rgba(34, 197, 94, 0.14)",
        line={"width": 0},
        layer="below",
    )
    figure.add_shape(
        type="rect",
        x0=q3,
        x1=axis_max,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        fillcolor="rgba(239, 68, 68, 0.10)",
        line={"width": 0},
        layer="below",
    )
    figure.add_trace(
        go.Box(
            x=values,
            name="Accepted comparables",
            orientation="h",
            boxpoints="all",
            jitter=0.3,
            pointpos=0,
            text=valid.index.astype(str),
            hovertemplate="%{text}<br>" + pli_label + ": %{x:.2f}<extra></extra>",
            marker={"color": "#2563EB", "size": 8},
            line={"color": "#1D4ED8"},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[tested_value],
            y=["Accepted comparables"],
            mode="markers+text",
            name="Pfizer Pharma GmbH",
            text=["Pfizer Pharma GmbH"],
            textposition="top center",
            marker={
                "symbol": "diamond",
                "size": 15,
                "color": "#DC2626",
                "line": {"color": "white", "width": 1},
            },
            hovertemplate="Pfizer Pharma GmbH<br>"
            + pli_label
            + ": %{x:.2f}<extra></extra>",
        )
    )

    for label, value, color in [
        ("Q1", q1, "#16A34A"),
        ("Median", median, "#0F766E"),
        ("Q3", q3, "#16A34A"),
    ]:
        figure.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{label}: {value:.2f}",
            annotation_position="top",
        )

    figure.update_layout(
        title=title,
        xaxis_title=pli_label,
        yaxis_title="",
        xaxis={"range": [axis_min, axis_max]},
        height=350,
        margin={"l": 20, "r": 20, "t": 46, "b": 34},
        showlegend=True,
    )
    return figure


def tested_party_trend_plot(
    yearly_pli: pd.Series,
    adjusted_points: dict[str, float] | None = None,
    title: str = "Pfizer Operating Margin Trend",
) -> go.Figure:
    """Return a line chart for tested-party yearly PLI development.

    Args:
        yearly_pli: Series indexed by fiscal year label with decimal PLI values.
        adjusted_points: Optional adjusted observations keyed by fiscal year label.
        title: Chart title.

    Returns:
        Plotly line chart.
    """

    display = pd.to_numeric(yearly_pli, errors="coerce").dropna() * 100
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=display.index,
            y=display,
            mode="lines+markers",
            name="Reported OM",
            line={"color": "#2563EB", "width": 3},
            marker={"size": 9},
            hovertemplate="%{x}<br>Reported OM: %{y:.2f}%<extra></extra>",
        )
    )

    if adjusted_points:
        adjusted = pd.Series(adjusted_points, dtype=float).dropna() * 100
        figure.add_trace(
            go.Scatter(
                x=adjusted.index,
                y=adjusted,
                mode="markers+text",
                name="Adjusted point",
                text=["FY22 restructuring adjusted" for _ in adjusted.index],
                textposition="top center",
                marker={
                    "symbol": "diamond",
                    "size": 13,
                    "color": "#DC2626",
                    "line": {"color": "white", "width": 1},
                },
                hovertemplate="%{x}<br>Adjusted OM: %{y:.2f}%<extra></extra>",
            )
        )

    figure.update_layout(
        title=title,
        xaxis_title="Fiscal year",
        yaxis_title="Operating Margin (%)",
        height=330,
        margin={"l": 20, "r": 20, "t": 54, "b": 36},
        hovermode="x unified",
    )
    return figure


def sorted_comparables_bar(
    comparables_detail: pd.DataFrame,
    tested_pli: float,
    range_dict: dict[str, float | int],
    title: str = "Accepted Comparables Weighted Operating Margin",
) -> go.Figure:
    """Return a sorted comparable-company PLI bar chart.

    Args:
        comparables_detail: Benchmark comparable detail table.
        tested_pli: Tested-party weighted PLI as a decimal.
        range_dict: Arm's-length range statistics.
        title: Chart title.

    Returns:
        Plotly bar chart.
    """

    display = comparables_detail.dropna(subset=["weighted_pli"]).copy()
    display = display.sort_values("weighted_pli", ascending=True)
    values = display["weighted_pli"] * 100
    q1 = float(range_dict["q1"]) * 100
    q3 = float(range_dict["q3"]) * 100
    tested_value = tested_pli * 100
    display["chart_name"] = display[config.COMPANY_NAME_COLUMN].apply(
        _short_company_name
    )
    display["iqr_status"] = display["weighted_pli"].between(
        float(range_dict["q1"]),
        float(range_dict["q3"]),
        inclusive="both",
    )
    colors = [
        "#16A34A" if is_inside else "#94A3B8" for is_inside in display["iqr_status"]
    ]

    figure = go.Figure()
    figure.add_vrect(
        x0=q1,
        x1=q3,
        fillcolor="#16A34A",
        opacity=0.12,
        layer="below",
        line_width=0,
    )
    figure.add_trace(
        go.Bar(
            x=values,
            y=display["chart_name"],
            orientation="h",
            marker={"color": colors},
            name="Accepted comparables",
            customdata=display[[config.COMPANY_NAME_COLUMN, "iqr_status"]].to_numpy(),
            hovertemplate=(
                "%{customdata[0]}<br>"
                "Weighted OM: %{x:.2f}%<br>"
                "Inside IQR: %{customdata[1]}<extra></extra>"
            ),
        )
    )
    figure.add_vline(
        x=tested_value,
        line_color="#DC2626",
        line_width=3,
    )
    for label, key in [("Q1", "q1"), ("Median", "median"), ("Q3", "q3")]:
        value = float(range_dict[key]) * 100
        figure.add_vline(
            x=value,
            line_dash="dash",
            line_color="#0F766E",
            line_width=2,
        )
        figure.add_annotation(
            x=value,
            y=1.03,
            xref="x",
            yref="paper",
            text=label,
            showarrow=False,
            font={"size": 12, "color": "#14B8A6"},
            xanchor="center",
        )
    figure.add_annotation(
        x=tested_value,
        y=1.11,
        xref="x",
        yref="paper",
        text="Pfizer",
        showarrow=False,
        font={"size": 12, "color": "#FFFFFF"},
        xanchor="center",
    )
    axis_min = min(float(values.min()), q1, tested_value, 0) - 1
    axis_max = max(float(values.max()), q3, tested_value, 0) + 1
    figure.update_layout(
        title=title,
        xaxis_title="Weighted Operating Margin (%)",
        yaxis_title="",
        height=max(390, 33 * len(display) + 120),
        margin={"l": 155, "r": 20, "t": 58, "b": 42},
        showlegend=False,
        bargap=0.22,
    )
    figure.update_xaxes(
        range=[axis_min, axis_max],
        zeroline=True,
        zerolinecolor="rgba(255,255,255,0.35)",
        gridcolor="rgba(255,255,255,0.12)",
    )
    return figure


def _short_company_name(company_name: object, max_length: int = 30) -> str:
    """Return a compact company label for charts."""

    name = str(company_name)
    if len(name) <= max_length:
        return name
    return f"{name[: max_length - 3].rstrip()}..."


def sensitivity_range_plot(
    summary: pd.DataFrame,
    title: str = "Sensitivity Ranges Compared to Pfizer",
) -> go.Figure:
    """Return a scenario range chart with tested-party markers.

    Args:
        summary: Scenario summary table from `scenario_summary_frame`.
        title: Chart title.

    Returns:
        Plotly range chart.
    """

    display = summary.loc[summary["PLI"].isin(["Operating Margin", "ROCE"])].copy()
    display = display.tail(12)
    y_labels = display["Group"] + " | " + display["Scenario"]

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=display["Q1"] * 100,
            y=y_labels,
            mode="markers",
            marker={"color": "#0F766E", "size": 8},
            name="Q1",
            hovertemplate="%{y}<br>Q1: %{x:.2f}%<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=display["Q3"] * 100,
            y=y_labels,
            mode="markers",
            marker={"color": "#0F766E", "size": 8},
            name="Q3",
            hovertemplate="%{y}<br>Q3: %{x:.2f}%<extra></extra>",
        )
    )
    for _, row in display.iterrows():
        y_label = f"{row['Group']} | {row['Scenario']}"
        figure.add_shape(
            type="line",
            x0=row["Q1"] * 100,
            x1=row["Q3"] * 100,
            y0=y_label,
            y1=y_label,
            xref="x",
            yref="y",
            line={"color": "#16A34A", "width": 8},
            layer="below",
        )
    figure.add_trace(
        go.Scatter(
            x=display["Tested PLI"] * 100,
            y=y_labels,
            mode="markers",
            marker={
                "symbol": "diamond",
                "color": "#DC2626",
                "size": 11,
                "line": {"color": "white", "width": 1},
            },
            name="Pfizer",
            hovertemplate="%{y}<br>Pfizer: %{x:.2f}%<extra></extra>",
        )
    )
    figure.update_layout(
        title=title,
        xaxis_title="PLI (%)",
        yaxis_title="",
        height=max(390, 34 * len(display)),
        margin={"l": 20, "r": 20, "t": 54, "b": 36},
    )
    return figure


def revenue_vs_margin_scatter(
    comparables_detail: pd.DataFrame,
    tested_revenue_eur_k: float,
    tested_pli: float,
    title: str = "Revenue Size vs Weighted Operating Margin",
) -> go.Figure:
    """Return a scatter plot showing size mismatch and profitability.

    Args:
        comparables_detail: Benchmark comparable detail table.
        tested_revenue_eur_k: Tested-party latest sales in thousand EUR.
        tested_pli: Tested-party weighted PLI as a decimal.
        title: Chart title.

    Returns:
        Plotly scatter plot.
    """

    display = comparables_detail.dropna(subset=["weighted_pli"]).copy()
    display["Revenue EURm"] = display[config.LATEST_REVENUE_COLUMN] / 1_000
    tested_revenue_eur_m = tested_revenue_eur_k / 1_000
    tested_margin = tested_pli * 100
    axis_max = max(float(display["Revenue EURm"].max()), tested_revenue_eur_m) * 1.12

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=display["Revenue EURm"],
            y=display["weighted_pli"] * 100,
            mode="markers",
            name="Accepted comparables",
            customdata=display[config.COMPANY_NAME_COLUMN],
            marker={
                "size": 11,
                "color": "#2563EB",
                "opacity": 0.78,
                "line": {"color": "rgba(255,255,255,0.35)", "width": 1},
            },
            hovertemplate=(
                "%{customdata}<br>"
                "Revenue: €%{x:.0f}M<br>"
                "OM: %{y:.2f}%<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[tested_revenue_eur_m],
            y=[tested_margin],
            mode="markers",
            name="Pfizer Pharma GmbH",
            marker={
                "symbol": "diamond",
                "size": 17,
                "color": "#DC2626",
                "line": {"color": "white", "width": 1},
            },
            hovertemplate=(
                "Pfizer Pharma GmbH<br>Revenue: €%{x:.0f}M<br>"
                "OM: %{y:.2f}%<extra></extra>"
            ),
        )
    )
    figure.add_annotation(
        x=tested_revenue_eur_m,
        y=tested_margin,
        text="Pfizer Pharma GmbH",
        showarrow=True,
        arrowhead=2,
        ax=-92,
        ay=-34,
        xanchor="right",
        font={"size": 12, "color": "#F8FAFC"},
        bgcolor="rgba(15, 23, 42, 0.78)",
        bordercolor="rgba(255,255,255,0.18)",
        borderpad=4,
    )
    figure.update_layout(
        title=title,
        xaxis_title="Latest revenue (€M)",
        yaxis_title="Weighted Operating Margin (%)",
        height=430,
        margin={"l": 82, "r": 112, "t": 58, "b": 56},
        legend={
            "orientation": "h",
            "x": 1,
            "xanchor": "right",
            "y": 1.08,
            "yanchor": "bottom",
        },
    )
    figure.update_xaxes(
        range=[0, axis_max],
        gridcolor="rgba(255,255,255,0.12)",
        zeroline=False,
    )
    figure.update_yaxes(gridcolor="rgba(255,255,255,0.12)", zeroline=False)
    return figure


def _axis_bounds(values: pd.Series, tested_value: float) -> tuple[float, float]:
    """Return padded axis bounds for comparable and tested-party values."""

    combined = pd.concat([values, pd.Series([tested_value])]).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    combined = combined.dropna()
    minimum = float(combined.min())
    maximum = float(combined.max())
    padding = max((maximum - minimum) * 0.15, 1.0)
    return minimum - padding, maximum + padding
