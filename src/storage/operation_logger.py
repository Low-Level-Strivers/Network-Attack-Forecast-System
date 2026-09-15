"""
Operation and State Logging System for Network Attack Forecast System.
Persists metadata and chronological network state histories generated from uploaded CSVs.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
from datetime import datetime
import pandas as pd
import numpy as np

from src.state_builder.aggregator import STATE_FEATURE_COLS


class OperationLogger:
    """
    Manages persistent logging of CSV ingestion operations and their generated network states.
    Ensures that historical operations and individual network states can be retrieved at any time.
    """

    def __init__(self, storage_dir: str | Path = "data/operations"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "operations_index.json"
        if not self.index_file.exists():
            self._save_index([])

    def _load_index(self) -> List[Dict[str, Any]]:
        """Loads the operations index list."""
        if not self.index_file.exists():
            return []
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_index(self, index_data: List[Dict[str, Any]]) -> None:
        """Saves the operations index list."""
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2, default=str)

    def list_operations(self) -> List[Dict[str, Any]]:
        """
        Lists all recorded operations, ordered by upload timestamp descending.
        """
        ops = self._load_index()
        # Sort descending by upload_time if available
        ops.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
        return ops

    def record_operation(
        self,
        file_name: str,
        states_df: pd.DataFrame,
        num_raw_rows: int = 0,
        k_horizon: int = 5,
        interval_sec: float = 1.0,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        operation_id: Optional[str] = None,
        summary: Optional[str] = None
    ) -> str:
        """
        Records a new CSV processing operation and persists its states.

        Args:
            file_name: Name of the uploaded CSV file.
            states_df: DataFrame of generated network states.
            num_raw_rows: Total raw traffic records processed.
            k_horizon: Configured forecast horizon.
            interval_sec: Simulation update interval in seconds.
            start_time: Processing start timestamp.
            end_time: Processing finish timestamp.
            operation_id: Optional custom ID.
            summary: Optional executive narrative summary.

        Returns:
            The recorded operation_id string.
        """
        now = datetime.now()
        now_iso = now.isoformat()

        if not operation_id:
            safe_name = "".join(c if c.isalnum() else "_" for c in Path(file_name).stem)[:20]
            timestamp_str = now.strftime("%Y%m%d_%H%M%S")
            operation_id = f"op_{safe_name}_{timestamp_str}"

        # Calculate peak risk score
        peak_risk = 0.0
        if "risk_score" in states_df.columns and len(states_df) > 0:
            peak_risk = float(states_df["risk_score"].max()) * 100.0

        risk_category = "High" if peak_risk >= 50.0 else ("Medium" if peak_risk >= 20.0 else "Low")

        # Format state table
        df_to_save = states_df.copy()
        if "state_id" not in df_to_save.columns:
            df_to_save["state_id"] = [f"S{i+1:03d}" for i in range(len(df_to_save))]

        if "risk_pct" not in df_to_save.columns and "risk_score" in df_to_save.columns:
            df_to_save["risk_pct"] = (df_to_save["risk_score"] * 100.0).round(1)

        if "risk_category" not in df_to_save.columns and "risk_pct" in df_to_save.columns:
            df_to_save["risk_category"] = df_to_save["risk_pct"].apply(
                lambda r: "High Risk" if r >= 50.0 else ("Medium Risk" if r >= 20.0 else "Low Risk")
            )

        # Build executive summary if not provided
        if not summary:
            summary = (
                f"Ingested {file_name} with {num_raw_rows:,} flows across {len(states_df)} discrete 1-min states. "
                f"Peak threat risk reached {peak_risk:.1f}% ({risk_category})."
            )

        meta: Dict[str, Any] = {
            "operation_id": operation_id,
            "file_name": file_name,
            "upload_time": now_iso,
            "start_time": start_time or now_iso,
            "end_time": end_time or now_iso,
            "num_rows": int(num_raw_rows),
            "num_states": int(len(df_to_save)),
            "processing_status": "Completed",
            "peak_risk_pct": round(peak_risk, 1),
            "risk_category": risk_category,
            "forecast_config": {
                "k_horizon": int(k_horizon),
                "interval_sec": float(interval_sec)
            },
            "summary": summary
        }

        # Save metadata JSON
        meta_path = self.storage_dir / f"{operation_id}_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, default=str)

        # Save states parquet (and json fallback)
        parquet_path = self.storage_dir / f"{operation_id}_states.parquet"
        try:
            # Ensure timestamp is string for serialization safety
            df_storage = df_to_save.copy()
            if "timestamp" in df_storage.columns:
                df_storage["timestamp"] = df_storage["timestamp"].astype(str)
            df_storage.to_parquet(parquet_path, index=False)
        except Exception:
            # Fallback to csv if pyarrow has schema quirks
            csv_path = self.storage_dir / f"{operation_id}_states.csv"
            df_to_save.to_csv(csv_path, index=False)

        # Update index
        index_data = self._load_index()
        # Remove any previous entry with same operation_id
        index_data = [item for item in index_data if item.get("operation_id") != operation_id]
        index_data.append(meta)
        self._save_index(index_data)

        return operation_id

    def load_operation(self, operation_id: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
        """
        Loads an operation's metadata and state records DataFrame.

        Args:
            operation_id: The ID of the operation.

        Returns:
            Tuple of (metadata_dict, states_dataframe).
        """
        meta_path = self.storage_dir / f"{operation_id}_meta.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"Operation metadata not found for {operation_id}")

        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        parquet_path = self.storage_dir / f"{operation_id}_states.parquet"
        csv_path = self.storage_dir / f"{operation_id}_states.csv"

        if parquet_path.exists():
            states_df = pd.read_parquet(parquet_path)
        elif csv_path.exists():
            states_df = pd.read_csv(csv_path)
        else:
            raise FileNotFoundError(f"State records not found for {operation_id}")

        return meta, states_df

    def ensure_baseline_operation(self, baseline_states_df: pd.DataFrame) -> str:
        """
        Ensures that the default Tuesday baseline dataset is permanently recorded in the
        operations log so that the Operation History and State Explorer are immediately
        populated and ready to use.
        """
        baseline_id = "op_Tuesday_WorkingHours_baseline"
        existing = [op for op in self.list_operations() if op.get("operation_id") == baseline_id]
        if existing and (self.storage_dir / f"{baseline_id}_meta.json").exists():
            return baseline_id

        return self.record_operation(
            file_name="Tuesday-WorkingHours.pcap_ISCX.csv",
            states_df=baseline_states_df,
            num_raw_rows=445641,
            k_horizon=5,
            interval_sec=1.0,
            start_time="2026-09-14T09:00:00",
            end_time="2026-09-14T09:00:45",
            operation_id=baseline_id,
            summary="Default baseline operational traffic capture featuring FTP & SSH brute-force attack progression."
        )
