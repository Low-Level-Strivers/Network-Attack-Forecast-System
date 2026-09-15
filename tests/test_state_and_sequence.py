"""
Unit Tests for Phase 3 (State Construction) & Phase 4 (Sequence Builder)
"""

import sys
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import torch

from src.state_builder.aggregator import construct_network_states, STATE_FEATURE_COLS
from src.sequence_builder.sequence_generator import create_sliding_sequences
from src.sequence_builder.dataset import NetworkStateDataset, prepare_temporal_dataloaders


def test_state_construction():
    # Synthetic flow records across 3 minutes
    times = [
        "2017-07-04 08:54:10", "2017-07-04 08:54:30",
        "2017-07-04 08:55:10",
        "2017-07-04 08:56:05"
    ]
    df_sample = pd.DataFrame({
        "Timestamp": pd.to_datetime(times),
        "minute_window": pd.to_datetime(times).floor("1min"),
        "Flow Duration": [1000, 2000, 1500, 3000],
        "Destination Port": [80, 443, 80, 22],
        "Source Port": [50001, 50002, 50003, 50004],
        "Total Fwd Packets": [5, 10, 8, 20],
        "Total Backward Packets": [3, 5, 4, 10],
        "Total Length of Fwd Packets": [500, 1000, 800, 2000],
        "Total Length of Bwd Packets": [300, 500, 400, 1000],
        "Packet Length Mean": [100.0, 100.0, 100.0, 100.0],
        "Packet Length Std": [10.0, 10.0, 10.0, 10.0],
        "Flow IAT Mean": [50.0, 50.0, 50.0, 50.0],
        "Flow IAT Std": [5.0, 5.0, 5.0, 5.0],
        "Fwd Packets/s": [10.0, 10.0, 10.0, 10.0],
        "Bwd Packets/s": [5.0, 5.0, 5.0, 5.0],
        "SYN Flag Count": [1, 1, 0, 0],
        "ACK Flag Count": [1, 1, 1, 1],
        "RST Flag Count": [0, 0, 0, 0],
        "FIN Flag Count": [0, 0, 0, 0],
        "PSH Flag Count": [0, 0, 0, 0],
        "Down/Up Ratio": [1.0, 1.0, 1.0, 1.0],
        "Active Mean": [0.0, 0.0, 0.0, 0.0],
        "Idle Mean": [0.0, 0.0, 0.0, 0.0],
        "Label": ["BENIGN", "BENIGN", "PortScan", "SSH-Patator"],
        "is_attack": [0, 0, 1, 1]
    })

    states, meta = construct_network_states(df_sample, reindex_continuous=True)
    assert len(states) == 3
    assert "timestamp" in states.columns
    for feat in STATE_FEATURE_COLS:
        assert feat in states.columns
    assert states.loc[0, "flow_count"] == 2
    assert states.loc[1, "flow_count"] == 1
    assert states.loc[2, "flow_count"] == 1
    assert states.loc[0, "is_attack_state"] == 0
    assert states.loc[1, "is_attack_state"] == 1
    assert states.loc[2, "is_attack_state"] == 1


def test_sequence_generation():
    # 40 states, lookback=10, horizon=3
    T = 40
    F = len(STATE_FEATURE_COLS)
    states = np.random.randn(T, F).astype(np.float32)
    risk = np.random.rand(T).astype(np.float32)
    stage = np.random.randint(0, 3, size=T).astype(np.int64)
    timestamps = pd.date_range("2017-07-04 08:00:00", periods=T, freq="1min")

    X, Y_state, Y_risk, Y_stage, Y_horizon, ref_ts = create_sliding_sequences(
        state_matrix=states,
        risk_vector=risk,
        stage_vector=stage,
        timestamps=pd.Series(timestamps),
        lookback_steps=10,
        forecast_horizon=3
    )

    expected_samples = T - 10 - 3 + 1  # 40 - 10 - 3 + 1 = 28
    assert X.shape == (expected_samples, 10, F)
    assert Y_state.shape == (expected_samples, F)
    assert Y_risk.shape == (expected_samples, 1)
    assert Y_stage.shape == (expected_samples,)
    assert Y_horizon.shape == (expected_samples, 3, F)


def test_pytorch_dataset():
    T = 45
    F = len(STATE_FEATURE_COLS)
    sample_df = pd.DataFrame(
        np.random.randn(T, F),
        columns=STATE_FEATURE_COLS
    )
    sample_df["timestamp"] = pd.date_range("2017-07-04 08:00:00", periods=T, freq="1min")
    sample_df["risk_score"] = np.random.rand(T)
    sample_df["stage_id"] = np.random.randint(0, 3, size=T)

    train_loader, val_loader, test_loader, scaler, meta = prepare_temporal_dataloaders(
        state_df=sample_df,
        lookback_steps=10,
        forecast_horizon=2,
        batch_size=4,
        scaler_save_path="models/test_scaler.joblib"
    )

    # Test batch retrieval from DataLoader
    batch = next(iter(train_loader))
    assert batch["x_seq"].shape == (4, 10, F)
    assert batch["target_state"].shape == (4, F)
    assert batch["target_risk"].shape == (4, 1)
    assert batch["target_stage"].shape == (4,)
    assert batch["target_horizon"].shape == (4, 2, F)


if __name__ == "__main__":
    print("Running State & Sequence Unit Tests...")
    test_state_construction()
    print("  [OK] 1-Minute State Construction test passed")
    test_sequence_generation()
    print("  [OK] Sliding sequence generation test passed")
    test_pytorch_dataset()
    print("  [OK] PyTorch Dataset & DataLoader test passed")
    print("\nALL PHASE 3 & 4 UNIT TESTS PASSED! [OK]")
