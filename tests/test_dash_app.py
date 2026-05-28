"""Smoke tests for the parallel Dash app."""

from __future__ import annotations

from dash_app import _load_context, _scenario_view
from src import config


def test_dash_app_loads_synthetic_context() -> None:
    """Dash app should load the committed synthetic demo dataset."""

    context = _load_context(config.DATA_MODE_SYNTHETIC)

    assert context["cascade_stats"]["raw"] == 55
    assert context["cascade_stats"]["accepted"] == 10
    assert context["base_result"]["range"]["n"] == 10


def test_dash_scenario_view_applies_controls() -> None:
    """Dash scenario view should apply PLI, period, pool, and adjustment controls."""

    context = _load_context(config.DATA_MODE_SYNTHETIC)
    view = _scenario_view(
        context,
        config.PLI_ROCE,
        "2-year weighted (FY23-FY24)",
        "Exclude largest comparable by revenue",
        normalize_fy22=True,
    )

    assert view["result"]["pli_type"] == config.PLI_ROCE
    assert view["result"]["range"]["n"] == 9
    assert view["normalize_fy22"] is True
