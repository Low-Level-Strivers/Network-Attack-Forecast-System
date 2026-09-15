"""
Timestamp Parsing and Chronological Sorting Module for Network Attack Forecast System.
Ensures strict temporal order and minute-window quantization.
"""

from typing import Dict, Any, Tuple
import pandas as pd


def parse_and_sort_timestamps(
    df: pd.DataFrame,
    time_col: str = "Timestamp",
    round_freq: str = "1min"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Parses timestamp strings into datetime objects, sorts DataFrame chronologically,
    and creates a floored time-window column for state aggregation.

    Args:
        df: Flow DataFrame containing timestamp column.
        time_col: Name of the timestamp column (default: "Timestamp").
        round_freq: Frequency for floored time window (default: "1min").

    Returns:
        Tuple of (chronologically sorted DataFrame, temporal audit dict)
    """
    if time_col not in df.columns:
        raise KeyError(f"Timestamp column '{time_col}' not found in DataFrame.")

    df_sorted = df.copy()

    # Parse datetime with dayfirst=True for CIC-IDS2017 (e.g., 4/7/2017 = 4th July 2017)
    df_sorted[time_col] = pd.to_datetime(df_sorted[time_col], dayfirst=True, errors="coerce")

    # Drop any records with unparseable timestamps
    initial_count = len(df_sorted)
    df_sorted = df_sorted.dropna(subset=[time_col]).copy()
    invalid_dates_dropped = initial_count - len(df_sorted)

    # Strictly sort chronologically
    df_sorted = df_sorted.sort_values(by=time_col, ascending=True).reset_index(drop=True)

    # Add discrete minute_window column for Phase 3 aggregation
    # Using '1min' or 'min' compatible with pandas
    df_sorted["minute_window"] = df_sorted[time_col].dt.floor(round_freq)

    # Compute temporal metadata
    start_time = df_sorted[time_col].min()
    end_time = df_sorted[time_col].max()
    duration_minutes = round((end_time - start_time).total_seconds() / 60, 2)
    unique_windows = df_sorted["minute_window"].nunique()

    temporal_stats = {
        "start_time": str(start_time),
        "end_time": str(end_time),
        "duration_minutes": duration_minutes,
        "unique_1min_windows": unique_windows,
        "invalid_timestamps_dropped": invalid_dates_dropped,
    }

    return df_sorted, temporal_stats
