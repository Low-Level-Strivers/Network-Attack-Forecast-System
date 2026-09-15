"""
State Pipeline Runner.
Loads processed flow data, executes 1-minute state construction, and persists state tables.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import json
import pandas as pd

from src.state_builder.aggregator import construct_network_states


def run_state_pipeline(
    input_parquet: str | Path,
    output_state_parquet: str | Path | None = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Loads cleaned parquet flows and produces 1-minute state table S(t).
    """
    input_path = Path(input_parquet)
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned flows file not found: {input_path}")

    print(f"[Phase 3: State Construction] Loading flows from: {input_path.name}...")
    df_flows = pd.read_parquet(input_path)
    print(f"  -> Total input flows: {len(df_flows):,}")

    print(f"[Phase 3: State Construction] Aggregating into 1-minute state vectors S(t)...")
    df_states, meta = construct_network_states(df_flows)
    print(f"  -> Continuous States S(t) Created: {meta['total_continuous_states']} minutes")
    print(f"  -> Observed: {meta['observed_windows']}, Idle Filled: {meta['idle_minutes_filled']}")
    print(f"  -> Attack States: {meta['attack_states_count']} | Benign States: {meta['benign_states_count']}")

    if output_state_parquet is None:
        state_dir = Path("data/state_vectors")
        state_dir.mkdir(parents=True, exist_ok=True)
        stem = input_path.stem.replace("_cleaned", "")
        output_state_parquet = state_dir / f"{stem}_state_1min.parquet"

    out_path = Path(output_state_parquet)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[Storage] Saving state vectors to: {out_path}...")
    df_states.to_parquet(out_path, engine="pyarrow", index=False)
    file_size_kb = round(out_path.stat().st_size / 1024, 2)
    print(f"  -> Successfully saved state table ({file_size_kb} KB)")

    meta["output_file"] = str(out_path)
    meta["output_size_kb"] = file_size_kb
    return df_states, meta


if __name__ == "__main__":
    processed_file = Path("data/processed/Tuesday-WorkingHours_cleaned.parquet")
    if processed_file.exists():
        print("=" * 60)
        print("RUNNING NETWORK STATE CONSTRUCTION - PHASE 3")
        print("=" * 60)
        _, audit = run_state_pipeline(processed_file)
        print("\nState Construction Audit:")
        print(json.dumps(audit, indent=2, default=str))
        print("\nPhase 3 Completed Successfully! [SUCCESS]")
    else:
        print(f"File not found: {processed_file}")
