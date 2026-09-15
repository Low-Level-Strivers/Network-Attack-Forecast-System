"""
Feature Engineering Scaler Module.
Normalizes state feature vectors S(t) and persists scaler for inference and rollout inverse-transform.
"""

from pathlib import Path
from typing import List, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, MinMaxScaler

from src.state_builder.aggregator import STATE_FEATURE_COLS


class StateScaler:
    """
    Scaler dedicated to 1-minute network state vectors S(t).
    Uses RobustScaler (resistant to traffic burst outliers) followed by optional min-max bounding.
    """

    def __init__(self, feature_cols: List[str] = None):
        self.feature_cols = feature_cols or STATE_FEATURE_COLS
        self.scaler = RobustScaler()
        self.is_fitted = False

    def fit(self, df: pd.DataFrame) -> "StateScaler":
        """Fits scaler on training state records."""
        features = df[self.feature_cols].values
        self.scaler.fit(features)
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """Transforms state DataFrame to normalized numpy matrix."""
        if not self.is_fitted:
            raise RuntimeError("StateScaler must be fitted before transforming.")
        features = df[self.feature_cols].values
        return self.scaler.transform(features)

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        """Fits on state records and transforms in one step."""
        return self.fit(df).transform(df)

    def inverse_transform(self, scaled_matrix: np.ndarray) -> np.ndarray:
        """Converts normalized predictions back into physical network metric values."""
        if not self.is_fitted:
            raise RuntimeError("StateScaler must be fitted before inverse transforming.")
        return self.scaler.inverse_transform(scaled_matrix)

    def save(self, filepath: str | Path = "models/state_scaler.joblib"):
        """Serializes fitted scaler to disk."""
        out_path = Path(filepath)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, out_path)
        print(f"[Scaler] Saved fitted StateScaler to {out_path}")

    @classmethod
    def load(cls, filepath: str | Path = "models/state_scaler.joblib") -> "StateScaler":
        """Loads fitted scaler from disk."""
        in_path = Path(filepath)
        if not in_path.exists():
            raise FileNotFoundError(f"Scaler checkpoint not found at: {in_path}")
        return joblib.load(in_path)
