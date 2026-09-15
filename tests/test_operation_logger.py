"""
Unit tests for OperationLogger persistence and state retrieval.
"""

import sys
from pathlib import Path
import shutil

# Ensure project root in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from src.storage.operation_logger import OperationLogger


def test_operation_logger():
    test_dir = Path("tests/temp_operations")
    if test_dir.exists():
        shutil.rmtree(test_dir)

    logger = OperationLogger(storage_dir=test_dir)

    # 1. Verify initially empty
    ops = logger.list_operations()
    assert len(ops) == 0

    # 2. Create dummy states dataframe
    timestamps = pd.date_range("2026-09-14 10:00:00", periods=5, freq="1min")
    dummy_states = pd.DataFrame({
        "timestamp": timestamps,
        "flow_count": [100, 150, 300, 800, 1200],
        "packet_rate": [25.0, 30.0, 60.0, 120.0, 200.0],
        "byte_rate": [1024.0, 2048.0, 4096.0, 8192.0, 16384.0],
        "unique_dst_ports": [2, 5, 20, 50, 80],
        "syn_flag_count": [0, 2, 10, 45, 90],
        "risk_score": [0.05, 0.12, 0.35, 0.68, 0.94]
    })

    # 3. Record operation
    op_id = logger.record_operation(
        file_name="TestTraffic.csv",
        states_df=dummy_states,
        num_raw_rows=50000,
        k_horizon=5,
        interval_sec=1.5
    )

    assert op_id.startswith("op_TestTraffic")

    # 4. Verify listed
    ops = logger.list_operations()
    assert len(ops) == 1
    assert ops[0]["operation_id"] == op_id
    assert ops[0]["num_states"] == 5
    assert ops[0]["num_rows"] == 50000
    assert ops[0]["peak_risk_pct"] == 94.0
    assert ops[0]["risk_category"] == "High"

    # 5. Load operation
    meta, loaded_df = logger.load_operation(op_id)
    assert meta["file_name"] == "TestTraffic.csv"
    assert len(loaded_df) == 5
    assert "state_id" in loaded_df.columns
    assert loaded_df.iloc[0]["state_id"] == "S001"
    assert loaded_df.iloc[4]["state_id"] == "S005"

    # 6. Test ensure_baseline_operation
    base_id = logger.ensure_baseline_operation(dummy_states)
    assert base_id == "op_Tuesday_WorkingHours_baseline"
    ops = logger.list_operations()
    assert len(ops) == 2

    # Clean up
    if test_dir.exists():
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    print("Running OperationLogger Unit Tests...")
    test_operation_logger()
    print("  [OK] OperationLogger test passed successfully!")
