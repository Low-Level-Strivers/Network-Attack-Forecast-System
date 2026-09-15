"""
Temporal Sequence Generator Module.
Generates sliding lookback windows X in R^(N x L x F) and multi-task target matrices.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


def create_sliding_sequences(
    state_matrix: np.ndarray,
    risk_vector: np.ndarray,
    stage_vector: np.ndarray,
    timestamps: pd.Series,
    lookback_steps: int = 30,
    forecast_horizon: int = 5
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Constructs sliding lookback sequences and multi-task targets.

    For each valid index t:
        Input sequence: S(t - lookback + 1) ... S(t)
        Target Next State: S(t + 1)
        Target Next Risk: Risk(t + 1)
        Target Next Stage: Stage(t + 1)
        Target Horizon: S(t + 1) ... S(t + forecast_horizon)

    Args:
        state_matrix: Normalized state array of shape (T, num_features).
        risk_vector: Risk score array of shape (T,).
        stage_vector: Stage ID array of shape (T,).
        timestamps: Series of datetime timestamps of length T.
        lookback_steps: History window size (L).
        forecast_horizon: Future rollout steps (K).

    Returns:
        Tuple of (X, Y_state, Y_risk, Y_stage, Y_horizon, ref_timestamps)
    """
    total_steps, num_features = state_matrix.shape
    min_required = lookback_steps + forecast_horizon

    if total_steps < min_required:
        raise ValueError(
            f"State series length ({total_steps}) is shorter than required lookback + horizon ({min_required})"
        )

    num_samples = total_steps - lookback_steps - forecast_horizon + 1

    X = np.zeros((num_samples, lookback_steps, num_features), dtype=np.float32)
    Y_state = np.zeros((num_samples, num_features), dtype=np.float32)
    Y_risk = np.zeros((num_samples, 1), dtype=np.float32)
    Y_stage = np.zeros(num_samples, dtype=np.int64)
    Y_horizon = np.zeros((num_samples, forecast_horizon, num_features), dtype=np.float32)
    ref_timestamps = []

    for i in range(num_samples):
        # Window end is index of current state S(t)
        t_current = i + lookback_steps - 1
        t_next = t_current + 1
        t_horizon_end = t_current + forecast_horizon + 1

        # S(t - lookback + 1) ... S(t)
        X[i] = state_matrix[i:i + lookback_steps]

        # S(t + 1)
        Y_state[i] = state_matrix[t_next]

        # Risk(t + 1)
        Y_risk[i, 0] = risk_vector[t_next]

        # Stage(t + 1)
        Y_stage[i] = stage_vector[t_next]

        # S(t + 1) ... S(t + K)
        Y_horizon[i] = state_matrix[t_next:t_horizon_end]

        ref_timestamps.append(timestamps.iloc[t_current])

    return X, Y_state, Y_risk, Y_stage, Y_horizon, np.array(ref_timestamps)
