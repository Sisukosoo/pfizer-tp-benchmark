"""Tests for comparables decision-state handling."""

from __future__ import annotations

import pandas as pd

from src import config
from src.comparables import (
    compute_cascade_stats,
    default_decisions_frame,
    load_decisions,
    save_decisions,
)


def test_default_decisions_count() -> None:
    """Default triage should encode 10 accepts, 45 rejects, and no pending."""

    decisions = default_decisions_frame()

    assert (decisions["decision"] == config.DECISION_ACCEPT).sum() == 10
    assert (decisions["decision"] == config.DECISION_REJECT).sum() == 45
    assert (decisions["decision"] == config.DECISION_PENDING).sum() == 0


def test_all_categories_have_at_least_one() -> None:
    """Every configured rejection category should appear in default decisions."""

    decisions = default_decisions_frame()
    used_categories = set(
        decisions.loc[decisions["decision"] == config.DECISION_REJECT, "reason"]
    )

    assert set(config.REJECT_CATEGORIES) <= used_categories


def test_decisions_csv_roundtrip(tmp_path) -> None:
    """Decisions should persist and reload without data loss."""

    path = tmp_path / "comparables_decisions.csv"
    decisions = default_decisions_frame()

    save_decisions(decisions, path)
    loaded = load_decisions(path)

    pd.testing.assert_frame_equal(loaded, decisions)


def test_load_decisions_creates_csv_if_missing(tmp_path) -> None:
    """Missing mutable CSV state should be initialized from defaults."""

    path = tmp_path / "comparables_decisions.csv"

    decisions = load_decisions(path)

    assert path.exists()
    pd.testing.assert_frame_equal(decisions, default_decisions_frame())


def test_cascade_stats_sum() -> None:
    """Cascade counts should sum to the total decision population."""

    decisions = default_decisions_frame()
    stats = compute_cascade_stats(decisions)

    assert stats["accepted"] + stats["rejected"] + stats["pending"] == stats["raw"]


def test_no_company_in_both_accept_and_reject() -> None:
    """A company key cannot be both accepted and rejected."""

    decisions = default_decisions_frame()
    accepted = set(
        decisions.loc[decisions["decision"] == config.DECISION_ACCEPT, "bvd_id"]
    )
    rejected = set(
        decisions.loc[decisions["decision"] == config.DECISION_REJECT, "bvd_id"]
    )

    assert accepted.isdisjoint(rejected)


def test_default_decisions_use_demo_companies() -> None:
    """Committed defaults should not expose the private Orbis candidate list."""

    decisions = default_decisions_frame()

    assert decisions["company_name"].str.startswith("Demo ").all()
