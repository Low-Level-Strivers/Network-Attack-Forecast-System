"""
PyTorch Dataset and DataLoader Generator for Network World Model.
Implements temporal train/val/test holdouts with zero data leakage.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

from src.feature_engineering.scaler import StateScaler
from src.sequence_builder.sequence_generator import create_sliding_sequences
from src.state_builder.aggregator import STATE_FEATURE_COLS


class NetworkStateDataset(Dataset):
    """
    PyTorch Dataset wrapping sliding sequences of network state vectors.
    """

    def __init__(
        self,
        X: np.ndarray,
        Y_state: np.ndarray,
        Y_risk: np.ndarray,
        Y_stage: np.ndarray,
        Y_horizon: np.ndarray,
        timestamps: np.ndarray
    ):
        self.X = torch.from_numpy(X)
        self.Y_state = torch.from_numpy(Y_state)
        self.Y_risk = torch.from_numpy(Y_risk)
        self.Y_stage = torch.from_numpy(Y_stage)
        self.Y_horizon = torch.from_numpy(Y_horizon)
        self.timestamps = timestamps

    def __len__(self) -> int:
        return len(self.X)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        return {
            "x_seq": self.X[idx],
            "target_state": self.Y_state[idx],
            "target_risk": self.Y_risk[idx],
            "target_stage": self.Y_stage[idx],
            "target_horizon": self.Y_horizon[idx],
            "timestamp": str(self.timestamps[idx])
        }


def prepare_temporal_dataloaders(
    state_df: pd.DataFrame,
    lookback_steps: int = 30,
    forecast_horizon: int = 5,
    batch_size: int = 32,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    scaler_save_path: str = "models/state_scaler.joblib"
) -> Tuple[DataLoader, DataLoader, DataLoader, StateScaler, Dict[str, Any]]:
    """
    Splits state records chronologically, fits scaler strictly on train split,
    generates lookback sequences, and returns PyTorch DataLoaders.

    Args:
        state_df: 1-minute state DataFrame.
        lookback_steps: Input sequence length L.
        forecast_horizon: Future rollout steps K.
        batch_size: Training batch size.
        train_ratio: Fraction of timeline allocated to training.
        val_ratio: Fraction of timeline allocated to validation.
        scaler_save_path: Destination for fitted scaler.

    Returns:
        Tuple of (train_loader, val_loader, test_loader, fitted_scaler, split_metadata)
    """
    total_len = len(state_df)
    train_end = int(total_len * train_ratio)
    val_end = int(total_len * (train_ratio + val_ratio))

    df_train = state_df.iloc[:train_end].copy()
    df_val = state_df.iloc[train_end:val_end].copy()
    df_test = state_df.iloc[val_end:].copy()

    print(f"[Dataset] Temporal Split: Train={len(df_train)}, Val={len(df_val)}, Test={len(df_test)}")

    # 1. Fit scaler strictly on train split (prevent temporal leakage!)
    scaler = StateScaler(feature_cols=STATE_FEATURE_COLS)
    scaler.fit(df_train)
    scaler.save(scaler_save_path)

    # 2. Normalize full dataframe using train-fitted scaler
    norm_states = scaler.transform(state_df)
    risk_arr = state_df["risk_score"].values
    stage_arr = state_df["stage_id"].values
    timestamps = state_df["timestamp"]

    # 3. Create full sequence set
    X, Y_state, Y_risk, Y_stage, Y_horizon, ref_ts = create_sliding_sequences(
        state_matrix=norm_states,
        risk_vector=risk_arr,
        stage_vector=stage_arr,
        timestamps=timestamps,
        lookback_steps=lookback_steps,
        forecast_horizon=forecast_horizon
    )

    # 4. Map sequence indices according to chronological split
    num_seq = len(X)
    n_train = int(num_seq * train_ratio)
    n_val = int(num_seq * val_ratio)

    ds_train = NetworkStateDataset(
        X[:n_train], Y_state[:n_train], Y_risk[:n_train], Y_stage[:n_train], Y_horizon[:n_train], ref_ts[:n_train]
    )
    ds_val = NetworkStateDataset(
        X[n_train:n_train + n_val], Y_state[n_train:n_train + n_val], Y_risk[n_train:n_train + n_val],
        Y_stage[n_train:n_train + n_val], Y_horizon[n_train:n_train + n_val], ref_ts[n_train:n_train + n_val]
    )
    ds_test = NetworkStateDataset(
        X[n_train + n_val:], Y_state[n_train + n_val:], Y_risk[n_train + n_val:],
        Y_stage[n_train + n_val:], Y_horizon[n_train + n_val:], ref_ts[n_train + n_val:]
    )

    train_loader = DataLoader(ds_train, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(ds_val, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(ds_test, batch_size=batch_size, shuffle=False)

    metadata = {
        "total_states": total_len,
        "total_sequences": num_seq,
        "train_samples": len(ds_train),
        "val_samples": len(ds_val),
        "test_samples": len(ds_test),
        "sequence_shape": list(X.shape[1:]),
        "batch_size": batch_size
    }

    return train_loader, val_loader, test_loader, scaler, metadata
