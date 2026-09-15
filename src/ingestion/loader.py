"""
Data Ingestion Module for Network Attack Forecast System.
Loads raw flow datasets (CSV), sanitizes headers, and handles duplicate columns.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import pandas as pd


def sanitize_column_names(columns: list) -> list:
    """
    Strips leading/trailing whitespace and renames duplicate column names.
    e.g., ' Fwd Header Length', 'Fwd Header Length' -> 'Fwd Header Length', 'Fwd Header Length_1'
    """
    clean_cols = []
    seen = {}
    for col in columns:
        c = str(col).strip()
        if c in seen:
            seen[c] += 1
            clean_cols.append(f"{c}_{seen[c]}")
        else:
            seen[c] = 0
            clean_cols.append(c)
    return clean_cols


def load_raw_flow_csv(
    file_path: str | Path,
    nrows: int | None = None,
    low_memory: bool = False
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads raw CIC-IDS2017 CSV file, sanitizes column names, and returns metadata.

    Args:
        file_path: Path to the raw CSV file.
        nrows: Optional row limit for quick inspection / pilot tests.
        low_memory: Memory optimization flag for large CSVs.

    Returns:
        Tuple of (sanitized DataFrame, metadata dict)
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {path}")

    # Read raw CSV
    df = pd.read_csv(path, nrows=nrows, low_memory=low_memory)

    # Sanitize columns
    original_cols = list(df.columns)
    sanitized_cols = sanitize_column_names(original_cols)
    df.columns = sanitized_cols

    # Strip whitespace from string/object columns (especially Label)
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    metadata = {
        "file_name": path.name,
        "raw_rows": len(df),
        "raw_columns": len(df.columns),
        "columns": sanitized_cols,
        "memory_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
    }

    return df, metadata
