"""
K-Step Autoregressive Simulation Engine.
Recursively rolls out future network states S(t+1)...S(t+K), estimates risk trajectory,
predicts attack stages, and calculates actionable prediction lead time.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import torch

from src.models.world_model import LSTMWorldModel
from src.feature_engineering.scaler import StateScaler
from src.state_builder.aggregator import STATE_FEATURE_COLS

STAGE_NAMES = {
    0: "Normal (Benign)",
    1: "Reconnaissance (Scanning)",
    2: "Credential Access (Brute Force)",
    3: "Denial of Service (DoS/DDoS)",
    4: "Exploitation / Infiltration"
}


class KStepSimulator:
    """
    Simulation engine performing multi-step future state forecasting.
    """

    def __init__(
        self,
        model: LSTMWorldModel,
        scaler: StateScaler,
        device: str | torch.device = "cpu"
    ):
        self.model = model
        self.scaler = scaler
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()

    @classmethod
    def load_from_checkpoint(
        cls,
        model_path: str | Path = "models/lstm_world_model_best.pt",
        scaler_path: str | Path = "models/state_scaler.joblib",
        device: str | torch.device = "cpu"
    ) -> "KStepSimulator":
        """Factory method loading trained model checkpoint and scaler."""
        ckpt = torch.load(model_path, map_location=device)
        m_cfg = ckpt.get("config", {})
        input_dim = ckpt.get("input_dim", 25)

        model = LSTMWorldModel(
            input_dim=input_dim,
            hidden_dim=m_cfg.get("hidden_dim", 128),
            latent_dim=m_cfg.get("latent_dim", 64),
            num_layers=m_cfg.get("num_layers", 2),
            num_stages=5,
            dropout=0.0
        )
        model.load_state_dict(ckpt["model_state_dict"])
        scaler = StateScaler.load(scaler_path)

        return cls(model=model, scaler=scaler, device=device)

    def simulate(
        self,
        history_sequence: np.ndarray,
        k_steps: int = 5,
        risk_threshold: float = 0.50
    ) -> Dict[str, Any]:
        """
        Performs K-step autoregressive future simulation.

        Args:
            history_sequence: Observed past window S(t-29)...S(t) of shape [lookback, features].
            k_steps: Number of future minutes to forecast (K).
            risk_threshold: Risk score threshold that triggers an early warning.

        Returns:
            Dictionary with trajectory metrics, physical states, and early warning details.
        """
        # Ensure 3D shape: [1, lookback, features]
        if history_sequence.ndim == 2:
            current_window = history_sequence[np.newaxis, :, :].copy()
        else:
            current_window = history_sequence.copy()

        norm_trajectory = []
        risk_trajectory = []
        stage_id_trajectory = []
        stage_name_trajectory = []

        with torch.no_grad():
            for step in range(1, k_steps + 1):
                x_tensor = torch.tensor(current_window, dtype=torch.float32, device=self.device)
                out = self.model(x_tensor)

                pred_state = out["next_state"].cpu().numpy()[0]  # [features]
                pred_risk = float(out["risk"].cpu().numpy()[0, 0])
                pred_stage_id = int(torch.argmax(out["stage_logits"], dim=-1).cpu().numpy()[0])

                norm_trajectory.append(pred_state)
                risk_trajectory.append(round(pred_risk, 4))
                stage_id_trajectory.append(pred_stage_id)
                stage_name_trajectory.append(STAGE_NAMES.get(pred_stage_id, "Unknown"))

                # Autoregressive slide: append S_hat(t+step) to the end of window
                # Shift left by 1 and insert new predicted state at final position
                current_window = np.roll(current_window, shift=-1, axis=1)
                current_window[0, -1, :] = pred_state

        norm_states_arr = np.array(norm_trajectory)
        physical_states_arr = self.scaler.inverse_transform(norm_states_arr)

        # Early warning & Prediction Lead Time Analysis
        early_warning = False
        lead_time_minutes = None
        for step_idx, r in enumerate(risk_trajectory):
            if r >= risk_threshold:
                early_warning = True
                lead_time_minutes = step_idx + 1
                break

        # Extract primary physical indicators for dashboard display
        # Feature indices
        idx_flow_count = STATE_FEATURE_COLS.index("flow_count")
        idx_unique_ports = STATE_FEATURE_COLS.index("unique_dst_ports")
        idx_packet_rate = STATE_FEATURE_COLS.index("packet_rate")
        idx_syn_count = STATE_FEATURE_COLS.index("syn_flag_count")

        forecast_timeline = []
        for step in range(k_steps):
            forecast_timeline.append({
                "step": f"t+{step + 1}",
                "minutes_ahead": step + 1,
                "predicted_risk_pct": round(risk_trajectory[step] * 100, 1),
                "predicted_stage_id": stage_id_trajectory[step],
                "predicted_stage_name": stage_name_trajectory[step],
                "physical_metrics": {
                    "flow_count": int(max(0, round(physical_states_arr[step, idx_flow_count]))),
                    "unique_dst_ports": int(max(0, round(physical_states_arr[step, idx_unique_ports]))),
                    "packet_rate": round(max(0, physical_states_arr[step, idx_packet_rate]), 1),
                    "syn_flag_count": int(max(0, round(physical_states_arr[step, idx_syn_count])))
                }
            })

        return {
            "forecast_horizon_k": k_steps,
            "early_warning": early_warning,
            "prediction_lead_time_minutes": lead_time_minutes,
            "risk_trajectory": risk_trajectory,
            "stage_trajectory": stage_name_trajectory,
            "forecast_timeline": forecast_timeline,
            "normalized_future_states": norm_states_arr.tolist(),
        }
