"""Shared display formatting helpers for the benchmark UI and reports.

These helpers are the single source of truth for formatting PLI values, NACE
codes, and tested-party positions, so the Streamlit app and the Excel/report
layer cannot drift apart.
"""

from __future__ import annotations

import pandas as pd

from src import config

_POSITION_LABELS = {
    "below_q1": "Below Q1",
    "within_range": "Within range",
    "above_q3": "Above Q3",
    "not_available": "Not available",
}

_POSITION_PHRASES = {
    "below_q1": "below the arm's-length range",
    "within_range": "within the arm's-length range",
    "above_q3": "above the arm's-length range",
    "not_available": "not available",
}


def format_pli_value(value: object, pli_type: str) -> str:
    """Format a PLI value as a percentage or a ratio multiple."""

    if pd.isna(value):
        return "n/a"
    numeric_value = float(value)
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        return f"{numeric_value * 100:.2f}%"
    return f"{numeric_value:.2f}x"


def format_pli_spread(value: object, pli_type: str) -> str:
    """Format a PLI distance or range width in percentage points or multiples."""

    if pd.isna(value):
        return "n/a"
    numeric_value = float(value)
    if config.PLI_PERCENT_FORMAT.get(pli_type, False):
        return f"{numeric_value * 100:.2f} pp"
    return f"{numeric_value:.2f}x"


def format_percent(value: object) -> str:
    """Format a decimal ratio as a percentage string."""

    if pd.isna(value):
        return "n/a"
    return f"{float(value) * 100:.2f}%"


def format_nace(value: object) -> str:
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


def position_label(position: object) -> str:
    """Return a compact tested-party position label (for example, `Above Q3`)."""

    key = str(position)
    return _POSITION_LABELS.get(key, key)


def position_phrase(position: object) -> str:
    """Return a tested-party position phrase (for example, `above the ...`)."""

    key = str(position)
    return _POSITION_PHRASES.get(key, key)
