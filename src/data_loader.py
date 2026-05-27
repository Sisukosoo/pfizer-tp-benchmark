"""Utilities for loading and normalizing Orbis Excel exports."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

from src import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CompanyMetadata:
    """Selected company descriptors from an Orbis export row.

    Attributes:
        name: Company name in Latin alphabet.
        country: ISO country code, if available.
        nace: NACE descriptor or code, if available.
        independence: Orbis independence indicator, if available.
        guo: Global Ultimate Owner, if available.
    """

    name: str
    country: str | None = None
    nace: str | None = None
    independence: str | None = None
    guo: str | None = None


def load_orbis_export(path: Path | str) -> pd.DataFrame:
    """Load an Orbis Excel export from its Results sheet.

    Args:
        path: Path to an Orbis `.xlsx` or `.xls` export.

    Returns:
        Cleaned wide-format DataFrame with one row per company.

    Raises:
        FileNotFoundError: If the requested export file does not exist.
        ValueError: If the required company name column is missing.
    """

    export_path = Path(path)
    if not export_path.exists():
        raise FileNotFoundError(f"Orbis export not found: {export_path}")

    dataframe = _read_results_sheet(export_path)

    if config.UNNAMED_LEADING_COLUMN in dataframe.columns:
        dataframe = dataframe.drop(columns=[config.UNNAMED_LEADING_COLUMN])

    if config.COMPANY_NAME_COLUMN not in dataframe.columns:
        raise ValueError(
            f"Required column missing from Orbis export: {config.COMPANY_NAME_COLUMN}"
        )

    dataframe = dataframe.dropna(subset=[config.COMPANY_NAME_COLUMN]).reset_index(
        drop=True
    )
    dataframe = _coerce_numeric_columns(dataframe)

    years_covered = infer_year_suffixes(dataframe)
    missing_cells = int(dataframe.isna().sum().sum())
    logger.info(
        "Loaded %s rows from %s; year suffixes: %s; missing cells: %s",
        len(dataframe),
        export_path.name,
        ", ".join(years_covered) or "none detected",
        missing_cells,
    )
    if missing_cells:
        logger.warning("Loaded Orbis export contains %s missing cells", missing_cells)

    return dataframe


def load_tested_party(data_mode: str | None = None) -> pd.DataFrame:
    """Load the Pfizer tested-party Orbis export from `data/raw/`.

    Args:
        data_mode: Optional data mode, `real` or `synthetic`.

    Returns:
        Cleaned tested-party DataFrame.
    """

    return load_orbis_export(config.resolve_tested_party_path(data_mode))


def load_comparables(data_mode: str | None = None) -> pd.DataFrame:
    """Load the comparables candidate Orbis export from `data/raw/`.

    Args:
        data_mode: Optional data mode, `real` or `synthetic`.

    Returns:
        Cleaned comparables candidate DataFrame.
    """

    return load_orbis_export(config.resolve_comparables_path(data_mode))


def extract_company_metadata(dataframe: pd.DataFrame) -> list[CompanyMetadata]:
    """Extract selected company metadata from a cleaned Orbis DataFrame.

    Args:
        dataframe: Cleaned Orbis DataFrame.

    Returns:
        Company metadata records, one per row.
    """

    records: list[CompanyMetadata] = []
    for _, row in dataframe.iterrows():
        records.append(
            CompanyMetadata(
                name=_optional_string(row.get(config.COMPANY_NAME_COLUMN)) or "",
                country=_optional_string(row.get(config.COUNTRY_COLUMN)),
                nace=_optional_string(row.get(config.NACE_COLUMN)),
                independence=_optional_string(row.get(config.INDEPENDENCE_COLUMN)),
                guo=_optional_string(row.get(config.GUO_COLUMN)),
            )
        )
    return records


def to_long_format(
    dataframe: pd.DataFrame,
    id_columns: list[str] | None = None,
) -> pd.DataFrame:
    """Reshape wide Orbis year-suffix columns to long analysis format.

    Args:
        dataframe: Cleaned Orbis DataFrame in wide format.
        id_columns: Columns to preserve as identifiers. Defaults to company name.

    Returns:
        DataFrame with columns for identifiers, `metric`, `year_suffix`, and `value`.
    """

    identifiers = id_columns or [config.COMPANY_NAME_COLUMN]
    value_columns = [
        column
        for column in dataframe.columns
        if column not in identifiers and _split_year_suffix(column)[1] is not None
    ]
    if not value_columns:
        return pd.DataFrame(columns=[*identifiers, "metric", "year_suffix", "value"])

    melted = dataframe.melt(
        id_vars=identifiers,
        value_vars=value_columns,
        var_name="metric_year",
        value_name="value",
    )
    metric_suffix = melted["metric_year"].apply(_split_year_suffix)
    melted["metric"] = metric_suffix.apply(lambda item: item[0])
    melted["year_suffix"] = metric_suffix.apply(lambda item: item[1])
    return melted[[*identifiers, "metric", "year_suffix", "value"]]


def infer_year_suffixes(dataframe: pd.DataFrame) -> list[str]:
    """Detect the Orbis relative year suffixes present in a DataFrame.

    Args:
        dataframe: Orbis DataFrame.

    Returns:
        Detected suffixes in configured chronological order.
    """

    present_suffixes: list[str] = []
    for suffix in config.YEAR_SUFFIXES:
        if any(str(column).endswith(suffix) for column in dataframe.columns):
            present_suffixes.append(suffix)
    return present_suffixes


def map_year_suffixes(
    latest_fiscal_year: int,
    suffixes: tuple[str, ...] = config.YEAR_SUFFIXES,
) -> dict[str, int]:
    """Map Orbis relative year suffixes to absolute fiscal years.

    Args:
        latest_fiscal_year: Absolute fiscal year represented by `Last avail. yr`.
        suffixes: Relative Orbis suffixes to map.

    Returns:
        Mapping from Orbis relative suffix to absolute fiscal year.
    """

    mapping: dict[str, int] = {}
    for offset, suffix in enumerate(suffixes):
        mapping[suffix] = latest_fiscal_year - offset
    return mapping


def _read_results_sheet(export_path: Path) -> pd.DataFrame:
    """Read the Orbis Results sheet, repairing known workbook quirks if needed."""

    try:
        return pd.read_excel(
            export_path,
            sheet_name=config.ORBIS_RESULTS_SHEET,
            header=0,
            na_values=config.MISSING_VALUE_TOKENS,
            keep_default_na=True,
        )
    except TypeError as error:
        if "applyNumFmt" not in str(error):
            raise
        logger.warning(
            "Repairing unsupported Orbis workbook style attribute in %s",
            export_path.name,
        )
        return pd.read_excel(
            _repair_openpyxl_style_alias(export_path),
            sheet_name=config.ORBIS_RESULTS_SHEET,
            header=0,
            na_values=config.MISSING_VALUE_TOKENS,
            keep_default_na=True,
        )


def _repair_openpyxl_style_alias(export_path: Path) -> BytesIO:
    """Return an in-memory workbook with `applyNumFmt` normalized for openpyxl."""

    repaired_workbook = BytesIO()
    with (
        ZipFile(export_path) as source,
        ZipFile(
            repaired_workbook,
            mode="w",
            compression=ZIP_DEFLATED,
        ) as target,
    ):
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename == "xl/styles.xml":
                content = content.replace(b"applyNumFmt=", b"applyNumberFormat=")
            target.writestr(item, content)

    repaired_workbook.seek(0)
    return repaired_workbook


def _coerce_numeric_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert columns that appear mostly numeric while preserving text columns."""

    cleaned = dataframe.copy()
    for column in cleaned.columns:
        if column == config.COMPANY_NAME_COLUMN:
            continue
        series = cleaned[column]
        if not pd.api.types.is_object_dtype(series):
            continue
        numeric = pd.to_numeric(series, errors="coerce")
        non_missing_count = int(series.notna().sum())
        if non_missing_count and int(numeric.notna().sum()) >= non_missing_count * 0.8:
            cleaned[column] = numeric
    return cleaned


def _split_year_suffix(column_name: object) -> tuple[str, str | None]:
    """Split an Orbis column into metric name and relative year suffix."""

    column_text = str(column_name)
    for suffix in config.YEAR_SUFFIXES:
        marker = f" {suffix}"
        if column_text.endswith(marker):
            return column_text.removesuffix(marker).strip(), suffix
    return column_text, None


def _optional_string(value: object) -> str | None:
    """Return a stripped string value, or None for missing values."""

    if pd.isna(value):
        return None
    return str(value).strip()
