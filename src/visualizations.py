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
        height=430,
        margin={"l": 20, "r": 20, "t": 60, "b": 40},
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
        height=390,
        margin={"l": 20, "r": 20, "t": 60, "b": 40},
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
    colors = [
        (
            "#16A34A"
            if float(range_dict["q1"]) <= value <= float(range_dict["q3"])
            else "#94A3B8"
        )
        for value in display["weighted_pli"]
    ]

    figure = go.Figure()
    figure.add_trace(
        go.Bar(
            x=values,
            y=display[config.COMPANY_NAME_COLUMN],
            orientation="h",
            marker={"color": colors},
            name="Accepted comparables",
            hovertemplate="%{y}<br>Weighted OM: %{x:.2f}%<extra></extra>",
        )
    )
    figure.add_vline(
        x=tested_pli * 100,
        line_color="#DC2626",
        line_width=3,
        annotation_text="Pfizer",
        annotation_position="top",
    )
    for label, key in [("Q1", "q1"), ("Median", "median"), ("Q3", "q3")]:
        figure.add_vline(
            x=float(range_dict[key]) * 100,
            line_dash="dash",
            line_color="#0F766E",
            annotation_text=label,
            annotation_position="bottom",
        )
    figure.update_layout(
        title=title,
        xaxis_title="Weighted Operating Margin (%)",
        yaxis_title="",
        height=470,
        margin={"l": 20, "r": 20, "t": 60, "b": 40},
        showlegend=False,
    )
    return figure


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
        height=max(420, 42 * len(display)),
        margin={"l": 20, "r": 20, "t": 60, "b": 40},
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
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=display["Revenue EURm"],
            y=display["weighted_pli"] * 100,
            mode="markers+text",
            name="Accepted comparables",
            text=display[config.COMPANY_NAME_COLUMN],
            textposition="top center",
            marker={"size": 10, "color": "#2563EB", "opacity": 0.78},
            hovertemplate=(
                "%{text}<br>Revenue: €%{x:.0f}M<br>" "OM: %{y:.2f}%<extra></extra>"
            ),
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[tested_revenue_eur_k / 1_000],
            y=[tested_pli * 100],
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
            hovertemplate=(
                "Pfizer Pharma GmbH<br>Revenue: €%{x:.0f}M<br>"
                "OM: %{y:.2f}%<extra></extra>"
            ),
        )
    )
    figure.update_layout(
        title=title,
        xaxis_title="Latest revenue (€M)",
        yaxis_title="Weighted Operating Margin (%)",
        height=430,
        margin={"l": 20, "r": 20, "t": 60, "b": 40},
    )
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
