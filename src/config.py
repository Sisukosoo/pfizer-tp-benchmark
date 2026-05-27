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

TESTED_PARTY_FILENAME = "Final_Pfizer_testedparty.xlsx"
COMPARABLES_FILENAME = "Export_27_05_2026_13_13.xlsx"
TESTED_PARTY_PATH = RAW_DATA_DIR / TESTED_PARTY_FILENAME
COMPARABLES_PATH = RAW_DATA_DIR / COMPARABLES_FILENAME

ORBIS_RESULTS_SHEET = "Results"
ORBIS_IGNORED_SHEET = "Search summary"
UNNAMED_LEADING_COLUMN = "Unnamed: 0"

COMPANY_NAME_COLUMN = "Company name Latin alphabet"
COUNTRY_COLUMN = "Country ISO code"
NACE_COLUMN = "NACE Rev. 2 main section"
INDEPENDENCE_COLUMN = "Independence indicator"
GUO_COLUMN = "Global Ultimate Owner"
LATEST_REVENUE_COLUMN = "Sales th EUR Last avail. yr"

YEAR_SUFFIXES = (
    "Last avail. yr",
    "Year - 1",
    "Year - 2",
    "Year - 3",
    "Year - 4",
)

MISSING_VALUE_TOKENS = ("n.a.", "n.a", "N.A.", "N/A", "na", "-")
