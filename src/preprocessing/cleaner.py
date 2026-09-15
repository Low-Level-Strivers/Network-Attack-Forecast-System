"""
Data Preprocessing Cleaner Module for Network Attack Forecast System.
Handles Infinity, NaN values, row deduplication, and label standardization.
"""

from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd


def clean_flow_data(
    df: pd.DataFrame,
    drop_duplicates: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans raw network flow records:
    1. Replaces +/- Inf with NaN in numeric columns.
    2. Drops rows with NaN values in flow metrics.
    3. Optionally removes exact duplicate flow records.
    4. Normalizes Label column and generates 'is_attack' flag.

    Args:
        df: Raw DataFrame with sanitized column names.
        drop_duplicates: Whether to drop duplicate flow rows.

    Returns:
        Tuple of (cleaned DataFrame, cleaning audit dictionary)
    """
    initial_rows = len(df)

    # 0. Deduplicate column names if any exist
    df = df.loc[:, ~df.columns.duplicated()].copy()

    # 1. Replace +/- Inf with NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    # If any object column contains 'Infinity' or 'NaN' strings, convert to NaN
    for col in df.select_dtypes(include=["object"]).columns:
        if col not in ["Flow ID", "Source IP", "Destination IP", "Timestamp", "Label"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Count and drop rows with NaN values
    nan_rows_count = int(df.isna().any(axis=1).sum())
    df_cleaned = df.dropna().copy()

    # 3. Deduplication
    duplicate_rows_count = 0
    if drop_duplicates:
        duplicate_rows_count = int(df_cleaned.duplicated().sum())
        df_cleaned = df_cleaned.drop_duplicates().copy()

    # 4. Standardize Label & Generate Binary Flag
    if "Label" in df_cleaned.columns:
        df_cleaned["Label"] = df_cleaned["Label"].astype(str).str.strip()
        # Binary attack indicator: 0 = BENIGN, 1 = Attack
        df_cleaned["is_attack"] = (df_cleaned["Label"].str.upper() != "BENIGN").astype(int)
    else:
        df_cleaned["is_attack"] = 0

    final_rows = len(df_cleaned)

    audit = {
        "initial_rows": initial_rows,
        "nan_or_inf_rows_dropped": nan_rows_count,
        "duplicate_rows_dropped": duplicate_rows_count,
        "final_rows": final_rows,
        "retention_rate_pct": round((final_rows / initial_rows) * 100, 2) if initial_rows > 0 else 0.0,
        "attack_flows_count": int(df_cleaned["is_attack"].sum()),
        "benign_flows_count": int((df_cleaned["is_attack"] == 0).sum()),
    }

    return df_cleaned, audit
