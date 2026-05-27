"""Project paths and shared constants for the benchmark application."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"
DECISIONS_CSV_PATH = PROCESSED_DATA_DIR / "comparables_decisions.csv"

TESTED_PARTY_FILENAME = "Final_Pfizer_testedparty.xlsx"
COMPARABLES_FILENAME = "Export_27_05_2026_13_13.xlsx"
TESTED_PARTY_PATH = RAW_DATA_DIR / TESTED_PARTY_FILENAME
COMPARABLES_PATH = RAW_DATA_DIR / COMPARABLES_FILENAME

ORBIS_RESULTS_SHEET = "Results"
ORBIS_IGNORED_SHEET = "Search summary"
UNNAMED_LEADING_COLUMN = "Unnamed: 0"

COMPANY_NAME_COLUMN = "Company name Latin alphabet"
COUNTRY_COLUMN = "Country"
NACE_COLUMN = "NACE Rev. 2, core code (4 digits)"
INDEPENDENCE_COLUMN = "Independence indicator"
GUO_COLUMN = "Global Ultimate Owner"
LATEST_REVENUE_COLUMN = "Sales th EUR Last avail. yr"
LATEST_EMPLOYEES_COLUMN = "Number of employees Last avail. yr"
TRADE_DESCRIPTION_COLUMN = "Trade description (English)"
BVD_ID_COLUMN = "BvD ID"

NACE_DESCRIPTIONS = {
    "4646": "Wholesale of pharmaceutical goods",
}

TESTED_PARTY_CHARACTERIZATION = (
    "Tested party characterization: Limited-Risk Distributor with Sales and "
    "Marketing functions (LRD-SM)"
)

DECISION_ACCEPT = "accept"
DECISION_REJECT = "reject"
DECISION_PENDING = "pending"
DECISION_OPTIONS = (DECISION_ACCEPT, DECISION_REJECT, DECISION_PENDING)

CATEGORY_MANUFACTURER = "MANUFACTURER"
CATEGORY_COOPERATIVE = "COOPERATIVE"
CATEGORY_RETAIL = "RETAIL"
CATEGORY_WRONG_SEGMENT = "WRONG_SEGMENT"
CATEGORY_HOLDING = "HOLDING"
CATEGORY_LOGISTICS = "LOGISTICS"
CATEGORY_BRAND_OWNER = "BRAND_OWNER"
CATEGORY_MIXED_PORTFOLIO = "MIXED_PORTFOLIO"
CATEGORY_LOW_DATA_QUALITY = "LOW_DATA_QUALITY"

CATEGORY_DISPLAY_ORDER = [
    CATEGORY_MANUFACTURER,
    CATEGORY_COOPERATIVE,
    CATEGORY_RETAIL,
    CATEGORY_WRONG_SEGMENT,
    CATEGORY_HOLDING,
    CATEGORY_LOGISTICS,
    CATEGORY_BRAND_OWNER,
    CATEGORY_MIXED_PORTFOLIO,
    CATEGORY_LOW_DATA_QUALITY,
]

REJECT_CATEGORIES = {
    CATEGORY_MANUFACTURER: {
        "label": "Manufacturer",
        "description": (
            "Excluded because manufacturing functions and production assets are "
            "not comparable to a limited-risk distributor."
        ),
    },
    CATEGORY_COOPERATIVE: {
        "label": "Pharmacy cooperative",
        "description": (
            "Excluded because pharmacy-owned cooperatives and consortia have "
            "member-service economics unlike a manufacturer's distributor."
        ),
    },
    CATEGORY_RETAIL: {
        "label": "Retail / B2C",
        "description": (
            "Excluded because retail pharmacies and online B2C channels perform "
            "consumer-facing functions outside the wholesale distributor profile."
        ),
    },
    CATEGORY_WRONG_SEGMENT: {
        "label": "Wrong product segment",
        "description": (
            "Excluded because the business focuses on medical devices, dental, "
            "veterinary, diagnostics, packaging, or other non-pharma segments."
        ),
    },
    CATEGORY_HOLDING: {
        "label": "Holding company",
        "description": (
            "Excluded because holding entities do not perform the operating "
            "distribution functions tested under TNMM."
        ),
    },
    CATEGORY_LOGISTICS: {
        "label": "Logistics service provider",
        "description": (
            "Excluded because logistics service providers are not principal "
            "pharmaceutical distributors."
        ),
    },
    CATEGORY_BRAND_OWNER: {
        "label": "Brand owner / IP profile",
        "description": (
            "Excluded because entities owning or developing pharmaceutical brands "
            "bear IP and market risks beyond the tested-party profile."
        ),
    },
    CATEGORY_MIXED_PORTFOLIO: {
        "label": "Mixed portfolio",
        "description": (
            "Excluded where pharma distribution is materially mixed with "
            "cosmetics, perfumes, devices, or own-marketed specialty products."
        ),
    },
    CATEGORY_LOW_DATA_QUALITY: {
        "label": "Low data quality",
        "description": (
            "Excluded where available financial or business-description evidence "
            "is insufficient to validate functional comparability."
        ),
    },
}

EURO_SIGN = "\N{EURO SIGN}"

YEAR_SUFFIXES = (
    "Last avail. yr",
    "Year - 1",
    "Year - 2",
    "Year - 3",
    "Year - 4",
)

MISSING_VALUE_TOKENS = ("n.a.", "n.a", "N.A.", "N/A", "na", "-")
