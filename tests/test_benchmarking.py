"""Tests for arm's-length range and benchmark orchestration."""

from __future__ import annotations

import pandas as pd
import pytest

from src import config
from src.benchmarking import (
    ArmsLengthRange,
    arms_length_range,
    position_tested_party,
    run_benchmark,
)
from src.comparables import get_accepted, load_decisions
from src.data_loader import load_comparables, load_tested_party


def test_arms_length_range_with_known_distribution() -> None:
    """Known 10-point distribution should produce linear quartiles."""

    values = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10])

    result = arms_length_range(values)

    assert result.n == 10
    assert result.q1 == pytest.approx(0.0325)
    assert result.median == pytest.approx(0.055)
    assert result.q3 == pytest.approx(0.0775)


def _sample_range() -> ArmsLengthRange:
    """Return a fixed arm's-length range for positioning tests."""

    return ArmsLengthRange(
        n=5,
        min=0.01,
        q1=0.03,
        median=0.05,
        q3=0.07,
        max=0.09,
        iqr_width=0.04,
    )


def test_position_above_q3() -> None:
    """A tested PLI above Q3 should be flagged for downward adjustment."""

    result = position_tested_party(tested_pli=0.10, range_result=_sample_range())

    assert result.position == "above_q3"
    assert result.adjustment_direction == "downward"


def test_position_within_range() -> None:
    """A tested PLI within Q1-Q3 should be considered within range."""

    result = position_tested_party(tested_pli=0.05, range_result=_sample_range())

    assert result.position == "within_range"
    assert result.adjustment_direction == "none"


def test_run_benchmark_end_to_end(
    sample_tested_party_df: pd.DataFrame,
    sample_comparables_df: pd.DataFrame,
) -> None:
    """Benchmark orchestration should return all major result blocks."""

    result = run_benchmark(
        tested_party_df=sample_tested_party_df,
        comparables_df=sample_comparables_df,
        pli_type=config.PLI_OPERATING_MARGIN,
        years=config.DEFAULT_BENCHMARK_PERIOD,
    )

    assert result.tested_pli == pytest.approx(0.10)
    assert result.range.n == 3
    assert len(result.comparables_detail) == 3
    assert result.position.position == "above_q3"


def test_real_benchmark_integration() -> None:
    """Run the real benchmark if confidential Orbis exports are available."""

    if not config.TESTED_PARTY_PATH.exists() or not config.COMPARABLES_PATH.exists():
        pytest.skip("Confidential Orbis exports not present in data/raw/.")

    tested_party = load_tested_party()
    raw_comparables = load_comparables()
    accepted = get_accepted(raw_comparables, load_decisions())
    result = run_benchmark(
        tested_party_df=tested_party,
        comparables_df=accepted,
        pli_type=config.PLI_OPERATING_MARGIN,
        years=config.DEFAULT_BENCHMARK_PERIOD,
    )

    assert 0 < result.tested_pli < 0.20
    assert result.range.q1 < result.range.median < result.range.q3
    assert result.range.n == 10
