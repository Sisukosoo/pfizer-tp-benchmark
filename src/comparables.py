"""Decision-state helpers for the comparables rejection cascade."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src import config
from src.default_decisions import DEFAULT_DECISIONS, make_decision_key

DECISION_COLUMNS = [
    "bvd_id",
    "company_name",
    "country",
    "decision",
    "reason",
    "notes",
    "modified_at",
    "modified_by",
]


def default_decisions_frame() -> pd.DataFrame:
    """Return default manual triage decisions as a DataFrame.

    Returns:
        DataFrame in the canonical decisions schema.
    """

    return _normalize_decisions_frame(pd.DataFrame(DEFAULT_DECISIONS))


def load_decisions(
    path: Path | str | None = None,
    data_mode: str | None = None,
) -> pd.DataFrame:
    """Load mutable comparables decisions, creating the CSV from defaults if needed.

    Args:
        path: Optional CSV path for mutable decision state.
        data_mode: Optional data mode, `real` or `synthetic`.

    Returns:
        Decisions DataFrame in the canonical schema.
    """

    resolved_mode = data_mode or config.active_data_mode()
    decisions_path = (
        Path(path)
        if path is not None
        else config.resolve_decisions_csv_path(resolved_mode)
    )
    if not decisions_path.exists():
        if path is None and resolved_mode == config.DATA_MODE_REAL:
            raise FileNotFoundError(
                "Real-data decisions CSV not found. Keep the private decisions "
                "file in data/processed/comparables_decisions.csv or switch to "
                "synthetic demo mode."
            )
        decisions = default_decisions_frame()
        save_decisions(decisions, decisions_path)
        return decisions

    return _normalize_decisions_frame(
        pd.read_csv(decisions_path, dtype=str, keep_default_na=False)
    )


def save_decisions(
    dataframe: pd.DataFrame,
    path: Path | str | None = None,
    data_mode: str | None = None,
) -> None:
    """Persist mutable comparables decisions to CSV.

    Args:
        dataframe: Decisions DataFrame in the canonical schema.
        path: Optional destination CSV path.
        data_mode: Optional data mode, `real` or `synthetic`.
    """

    decisions_path = (
        Path(path) if path is not None else config.resolve_decisions_csv_path(data_mode)
    )
    decisions_path.parent.mkdir(parents=True, exist_ok=True)
    _normalize_decisions_frame(dataframe).to_csv(decisions_path, index=False)


def reset_to_defaults(
    path: Path | str | None = None,
    data_mode: str | None = None,
) -> pd.DataFrame:
    """Overwrite mutable decisions with the default manual triage.

    Args:
        path: Optional CSV path for mutable decision state.
        data_mode: Optional data mode, `real` or `synthetic`.

    Returns:
        Default decisions DataFrame.
    """

    if (
        path is None
        and (data_mode or config.active_data_mode()) == config.DATA_MODE_REAL
    ):
        raise ValueError(
            "Reset to defaults is only available for synthetic demo decisions. "
            "Real-data decisions are private local state."
        )
    decisions = default_decisions_frame()
    save_decisions(decisions, path, data_mode)
    return decisions


def get_accepted(raw_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    """Return accepted comparables with full Orbis data attached.

    Args:
        raw_df: Raw comparables DataFrame loaded from Orbis.
        decisions_df: Decisions DataFrame.

    Returns:
        Orbis rows whose decision is `accept`.
    """

    merged = attach_decisions(raw_df, decisions_df)
    return merged.loc[merged["decision"] == config.DECISION_ACCEPT].reset_index(
        drop=True
    )


def get_rejected(raw_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    """Return rejected comparables with reason metadata attached.

    Args:
        raw_df: Raw comparables DataFrame loaded from Orbis.
        decisions_df: Decisions DataFrame.

    Returns:
        Orbis rows whose decision is `reject`.
    """

    merged = attach_decisions(raw_df, decisions_df)
    rejected = merged.loc[merged["decision"] == config.DECISION_REJECT].copy()
    rejected["reason_label"] = rejected["reason"].map(_category_label)
    return rejected.reset_index(drop=True)


def get_pending(raw_df: pd.DataFrame, decisions_df: pd.DataFrame) -> pd.DataFrame:
    """Return candidates with no accepted or rejected decision.

    Args:
        raw_df: Raw comparables DataFrame loaded from Orbis.
        decisions_df: Decisions DataFrame.

    Returns:
        Orbis rows whose decision is `pending`.
    """

    merged = attach_decisions(raw_df, decisions_df)
    return merged.loc[merged["decision"] == config.DECISION_PENDING].reset_index(
        drop=True
    )


def compute_cascade_stats(
    decisions_df: pd.DataFrame,
    raw_count: int | None = None,
) -> dict[str, object]:
    """Compute headline counts for the rejection cascade.

    Args:
        decisions_df: Decisions DataFrame.
        raw_count: Optional raw candidate count from the Orbis export.

    Returns:
        Dictionary with raw, accepted, rejected, pending, and category counts.
    """

    decisions = _normalize_decisions_frame(decisions_df)
    rejected = decisions.loc[decisions["decision"] == config.DECISION_REJECT]
    rejected_by_category = {
        category: int((rejected["reason"] == category).sum())
        for category in config.CATEGORY_DISPLAY_ORDER
    }
    accepted = int((decisions["decision"] == config.DECISION_ACCEPT).sum())
    pending = int((decisions["decision"] == config.DECISION_PENDING).sum())
    rejected_count = int(sum(rejected_by_category.values()))
    return {
        "raw": int(raw_count if raw_count is not None else len(decisions)),
        "accepted": accepted,
        "rejected": rejected_count,
        "pending": pending,
        "rejected_by_category": rejected_by_category,
    }


def attach_decisions(
    raw_df: pd.DataFrame,
    decisions_df: pd.DataFrame,
) -> pd.DataFrame:
    """Attach decision-state columns to a raw Orbis comparables DataFrame.

    Args:
        raw_df: Raw comparables DataFrame loaded from Orbis.
        decisions_df: Decisions DataFrame.

    Returns:
        Raw comparables with canonical decision columns appended.
    """

    raw = raw_df.copy()
    raw["bvd_id"] = raw.apply(resolve_bvd_id, axis=1)

    decisions = _normalize_decisions_frame(decisions_df)
    merge_columns = [
        "bvd_id",
        "decision",
        "reason",
        "notes",
        "modified_at",
        "modified_by",
    ]
    merged = raw.merge(
        decisions[merge_columns],
        on="bvd_id",
        how="left",
        validate="one_to_one",
    )
    merged["decision"] = merged["decision"].fillna(config.DECISION_PENDING)
    merged["reason"] = merged["reason"].fillna("")
    merged["notes"] = merged["notes"].fillna("")
    merged["modified_at"] = merged["modified_at"].fillna("")
    merged["modified_by"] = merged["modified_by"].fillna("")
    return merged


def resolve_bvd_id(row: pd.Series) -> str:
    """Resolve the BvD ID for a raw Orbis row, falling back if absent.

    Args:
        row: Raw Orbis row.

    Returns:
        Literal BvD ID when available, otherwise a deterministic fallback key.
    """

    if config.BVD_ID_COLUMN in row.index and pd.notna(row[config.BVD_ID_COLUMN]):
        return str(row[config.BVD_ID_COLUMN]).strip()
    return make_decision_key(
        str(row.get(config.COMPANY_NAME_COLUMN, "")),
        str(row.get(config.COUNTRY_COLUMN, "")),
    )


def mark_user_edits(
    original_df: pd.DataFrame,
    edited_df: pd.DataFrame,
) -> pd.DataFrame:
    """Mark edited rows as user-modified with a current timestamp.

    Args:
        original_df: Decisions before editing.
        edited_df: Decisions after Streamlit editing.

    Returns:
        Edited decisions with modification metadata updated where needed.
    """

    original = _normalize_decisions_frame(original_df).set_index("bvd_id")
    edited = _normalize_decisions_frame(edited_df)
    now = datetime.now(UTC).isoformat(timespec="seconds")

    for index, row in edited.iterrows():
        bvd_id = row["bvd_id"]
        if bvd_id not in original.index:
            edited.at[index, "modified_at"] = now
            edited.at[index, "modified_by"] = "user"
            continue
        original_row = original.loc[bvd_id]
        fields = ("decision", "reason", "notes")
        if any(str(row[field]) != str(original_row[field]) for field in fields):
            edited.at[index, "modified_at"] = now
            edited.at[index, "modified_by"] = "user"

    return edited


def _normalize_decisions_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize a decisions DataFrame to the canonical schema."""

    normalized = dataframe.copy()
    for column in DECISION_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[DECISION_COLUMNS].fillna("")
    normalized["bvd_id"] = normalized["bvd_id"].astype(str).str.strip()
    normalized["company_name"] = normalized["company_name"].astype(str).str.strip()
    normalized["country"] = normalized["country"].astype(str).str.strip()
    normalized["decision"] = (
        normalized["decision"]
        .replace("", config.DECISION_PENDING)
        .astype(str)
        .str.strip()
        .str.lower()
    )
    normalized["reason"] = normalized["reason"].astype(str).str.strip()
    normalized["notes"] = normalized["notes"].astype(str).str.strip()
    normalized["modified_at"] = normalized["modified_at"].astype(str).str.strip()
    normalized["modified_by"] = normalized["modified_by"].astype(str).str.strip()
    return normalized


def _category_label(category: str) -> str:
    """Return a human-readable label for a rejection category."""

    metadata = config.REJECT_CATEGORIES.get(category)
    if metadata is None:
        return category
    return metadata["label"]
