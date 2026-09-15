"""
Unit Tests for Phase 1 (Ingestion) & Phase 2 (Preprocessing)
"""

import sys
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from src.ingestion.loader import sanitize_column_names
from src.preprocessing.cleaner import clean_flow_data
from src.preprocessing.timestamp_parser import parse_and_sort_timestamps


def test_sanitize_column_names():
    raw_cols = [" Flow ID", " Destination Port ", "Fwd Header Length", "Fwd Header Length", " Label "]
    clean_cols = sanitize_column_names(raw_cols)
    assert clean_cols == ["Flow ID", "Destination Port", "Fwd Header Length", "Fwd Header Length_1", "Label"]


def test_clean_flow_data():
    sample_df = pd.DataFrame({
        "Flow Duration": [100, 200, np.inf, 400],
        "Flow Bytes/s": [1000.0, np.nan, 3000.0, 4000.0],
        "Label": ["BENIGN ", "PortScan", "BENIGN", "PortScan"]
    })
    cleaned, audit = clean_flow_data(sample_df, drop_duplicates=False)
    assert len(cleaned) == 2  # rows with inf and nan dropped
    assert "is_attack" in cleaned.columns
    assert list(cleaned["is_attack"]) == [0, 1]
    assert audit["nan_or_inf_rows_dropped"] == 2


def test_timestamp_parsing_and_sorting():
    sample_df = pd.DataFrame({
        "Timestamp": ["4/7/2017 9:15", "4/7/2017 8:54", "4/7/2017 8:55"],
        "Value": [3, 1, 2]
    })
    sorted_df, stats = parse_and_sort_timestamps(sample_df)
    # Check strict chronological order
    assert list(sorted_df["Value"]) == [1, 2, 3]
    assert "minute_window" in sorted_df.columns
    # Check that minute_window is correctly floored
    assert str(sorted_df.loc[0, "minute_window"]) == "2017-07-04 08:54:00"
    assert stats["unique_1min_windows"] == 3


if __name__ == "__main__":
    print("Running Preprocessing Unit Tests...")
    test_sanitize_column_names()
    print("  [OK] Column sanitization test passed")
    test_clean_flow_data()
    print("  [OK] Cleaner (Inf/NaN/Label) test passed")
    test_timestamp_parsing_and_sorting()
    print("  [OK] Timestamp parsing and sorting test passed")
    print("\nALL PREPROCESSING UNIT TESTS PASSED! [OK]")
