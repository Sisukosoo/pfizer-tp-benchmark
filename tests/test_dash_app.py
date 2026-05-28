"""Smoke tests for the parallel Dash app."""

from __future__ import annotations

from dash_app import _load_context
from src import config


def test_dash_app_loads_synthetic_context() -> None:
    """Dash app should load the committed synthetic demo dataset."""

    context = _load_context(config.DATA_MODE_SYNTHETIC)

    assert context["cascade_stats"]["raw"] == 55
    assert context["cascade_stats"]["accepted"] == 10
    assert context["base_result"]["range"]["n"] == 10
