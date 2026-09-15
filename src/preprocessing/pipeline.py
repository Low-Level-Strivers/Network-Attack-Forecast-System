"""
End-to-End Preprocessing Pipeline for Network Attack Forecast System.
Ingests raw flow CSV, cleans values, parses timestamps, sorts chronologically, and saves to Parquet.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import json
import pandas as pd

from src.ingestion.loader import load_raw_flow_csv
from src.preprocessing.cleaner import clean_flow_data
from src.preprocessing.timestamp_parser import parse_and_sort_timestamps


def run_pipeline(
    input_csv: str | Path,
    output_parquet: str | Path | None = None,
    drop_duplicates: bool = True,
    nrows: int | None = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes Phase 1 & 2 pipeline:
    1. Ingests raw CSV and sanitizes headers.
    2. Cleans NaN/Inf and removes duplicates.
    3. Normalizes attack labels.
    4. Parses timestamps and enforces chronological order.
    5. Saves output to optimized Parquet format.

    Args:
        input_csv: Path to raw CIC-IDS2017 CSV.
        output_parquet: Destination path for cleaned Parquet file.
        drop_duplicates: Whether to drop duplicate flows.
        nrows: Optional row limit for testing.

    Returns:
        Tuple of (processed DataFrame, complete audit dict)
    """
    input_path = Path(input_csv)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    print(f"[Phase 1: Ingestion] Loading raw data from: {input_path.name}...")
    df_raw, ingestion_meta = load_raw_flow_csv(input_path, nrows=nrows)
    print(f"  -> Loaded {ingestion_meta['raw_rows']:,} rows, {ingestion_meta['raw_columns']} columns ({ingestion_meta['memory_mb']} MB)")

    print(f"[Phase 2: Cleaning] Sanitizing numerical features and labels...")
    df_clean, cleaning_audit = clean_flow_data(df_raw, drop_duplicates=drop_duplicates)
    print(f"  -> Dropped {cleaning_audit['nan_or_inf_rows_dropped']:,} NaN/Inf rows")
    print(f"  -> Dropped {cleaning_audit['duplicate_rows_dropped']:,} duplicate rows")
    print(f"  -> Retained {cleaning_audit['final_rows']:,} clean flows ({cleaning_audit['retention_rate_pct']}%)")
    print(f"  -> Label Distribution: {cleaning_audit['benign_flows_count']:,} BENIGN, {cleaning_audit['attack_flows_count']:,} Attack")

    print(f"[Phase 2: Timestamps] Parsing timestamps & chronological sorting...")
    df_processed, temporal_audit = parse_and_sort_timestamps(df_clean)
    print(f"  -> Time Range: {temporal_audit['start_time']} to {temporal_audit['end_time']}")
    print(f"  -> Total Span: {temporal_audit['duration_minutes']} minutes across {temporal_audit['unique_1min_windows']} 1-minute windows")

    # Determine default output path if not provided
    if output_parquet is None:
        processed_dir = Path("data/processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        stem = input_path.stem.replace(".pcap_ISCX", "").replace(" ", "_")
        output_parquet = processed_dir / f"{stem}_cleaned.parquet"

    output_path = Path(output_parquet)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Storage] Saving optimized Parquet to: {output_path}...")
    df_processed.to_parquet(output_path, engine="pyarrow", index=False)
    file_size_mb = round(output_path.stat().st_size / (1024 * 1024), 2)
    print(f"  -> Saved successfully ({file_size_mb} MB)")

    full_audit = {
        "ingestion": ingestion_meta,
        "cleaning": cleaning_audit,
        "temporal": temporal_audit,
        "output_file": str(output_path),
        "output_file_size_mb": file_size_mb,
    }

    return df_processed, full_audit


if __name__ == "__main__":
    raw_file = Path("data/raw/Tuesday-WorkingHours.pcap_ISCX.csv")
    if raw_file.exists():
        print("=" * 60)
        print("RUNNING NETWORK ATTACK FORECAST - PHASE 1 & 2 PIPELINE")
        print("=" * 60)
        _, audit = run_pipeline(raw_file)
        print("\nAudit Summary:")
        print(json.dumps(audit, indent=2, default=str))
        print("\nPhase 1 & 2 Completed Successfully! [SUCCESS]")
    else:
        print(f"Target raw file not found at: {raw_file}")
