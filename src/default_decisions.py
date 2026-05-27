"""Synthetic default triage decisions for public demo mode.

The private Orbis candidate list is intentionally not stored in this module.
Real-data decisions are kept locally in the gitignored
`data/processed/comparables_decisions.csv` file.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from src import config

DEFAULT_MODIFIED_AT = datetime(2026, 5, 27, tzinfo=UTC).isoformat()

ACCEPTED_DEMO_COMPANIES: tuple[tuple[str, str], ...] = (
    ("Demo Pharma Distribution GmbH", "Germany"),
    ("Nordic Rx Wholesale AB", "Sweden"),
    ("Alpine Medicines Trading AG", "Austria"),
    ("Iberia Pharma Supply SL", "Spain"),
    ("Baltic Health Distribution OÜ", "Estonia"),
    ("Benelux Medicines Wholesale BV", "Netherlands"),
    ("Adriatic Pharma Trade SRL", "Italy"),
    ("Central Europe Rx Sp zoo", "Poland"),
    ("Lusitania Pharma Logistics SA", "Portugal"),
    ("Danube Healthcare Wholesale Kft", "Hungary"),
)

REJECTED_DEMO_COUNTS: dict[str, int] = {
    config.CATEGORY_MANUFACTURER: 7,
    config.CATEGORY_COOPERATIVE: 11,
    config.CATEGORY_RETAIL: 4,
    config.CATEGORY_WRONG_SEGMENT: 7,
    config.CATEGORY_HOLDING: 1,
    config.CATEGORY_LOGISTICS: 1,
    config.CATEGORY_BRAND_OWNER: 3,
    config.CATEGORY_MIXED_PORTFOLIO: 7,
    config.CATEGORY_LOW_DATA_QUALITY: 4,
}

DEMO_COUNTRIES: tuple[str, ...] = (
    "Germany",
    "France",
    "Italy",
    "Spain",
    "Austria",
    "Sweden",
    "Netherlands",
    "Belgium",
    "Finland",
    "Portugal",
)


def make_decision_key(company_name: str, country: str) -> str:
    """Build a stable fallback key when an Orbis export lacks literal BvD IDs.

    Args:
        company_name: Company name from the export.
        country: Country from the export.

    Returns:
        Deterministic fallback identifier stored in the `bvd_id` field.
    """

    country_token = _slug(country)
    company_token = _slug(company_name)
    return f"FALLBACK:{country_token}:{company_token}"


def synthetic_company_names() -> list[tuple[str, str]]:
    """Return the public-demo company universe in decision order.

    Returns:
        List of company name and country pairs.
    """

    companies = list(ACCEPTED_DEMO_COMPANIES)
    for category, count in REJECTED_DEMO_COUNTS.items():
        label = config.REJECT_CATEGORIES[category]["label"]
        for index in range(1, count + 1):
            country = DEMO_COUNTRIES[(len(companies) + index) % len(DEMO_COUNTRIES)]
            companies.append((f"Demo {label} Candidate {index:02d}", country))
    return companies


def _accept(company_name: str, country: str) -> dict[str, Any]:
    """Create an accepted default decision record."""

    return _decision(company_name, country, config.DECISION_ACCEPT, None, None)


def _reject(
    company_name: str,
    country: str,
    reason: str,
    notes: str,
) -> dict[str, Any]:
    """Create a rejected default decision record."""

    return _decision(company_name, country, config.DECISION_REJECT, reason, notes)


def _decision(
    company_name: str,
    country: str,
    decision: str,
    reason: str | None,
    notes: str | None,
) -> dict[str, Any]:
    """Create a default decision record in the canonical schema."""

    return {
        "bvd_id": make_decision_key(company_name, country),
        "company_name": company_name,
        "country": country,
        "decision": decision,
        "reason": reason,
        "notes": notes,
        "modified_at": DEFAULT_MODIFIED_AT,
        "modified_by": "default",
    }


def _slug(value: str) -> str:
    """Normalize text for a stable fallback decision key."""

    normalized = re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")
    return re.sub(r"-+", "-", normalized)


def _build_default_decisions() -> tuple[dict[str, Any], ...]:
    """Build synthetic default decisions for the public demo workflow."""

    decisions: list[dict[str, Any]] = [
        _accept(company_name, country)
        for company_name, country in ACCEPTED_DEMO_COMPANIES
    ]
    company_offset = 0
    for category, count in REJECTED_DEMO_COUNTS.items():
        label = config.REJECT_CATEGORIES[category]["label"]
        description = config.REJECT_CATEGORIES[category]["description"]
        for index in range(1, count + 1):
            country = DEMO_COUNTRIES[
                (len(ACCEPTED_DEMO_COMPANIES) + company_offset + index)
                % len(DEMO_COUNTRIES)
            ]
            company_name = f"Demo {label} Candidate {index:02d}"
            decisions.append(_reject(company_name, country, category, description))
        company_offset += count
    return tuple(decisions)


DEFAULT_DECISIONS: tuple[dict[str, Any], ...] = _build_default_decisions()
