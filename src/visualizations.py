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
