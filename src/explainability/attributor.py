"""
Explainability & Attribution Module for Network World Model.
Implements Integrated Gradients (Path Integrals) to attribute future risk escalation
to specific network behaviour dimensions (Port Diversity, SYN bursts, IAT variances).
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import torch

from src.models.world_model import LSTMWorldModel
from src.state_builder.aggregator import STATE_FEATURE_COLS

FEATURE_DISPLAY_NAMES = {
    "flow_count": "Flow Volume",
    "unique_dst_ports": "Destination Port Diversity",
    "unique_src_ports": "Source Port Count",
    "port_diversity_ratio": "Port Diversity Ratio",
    "total_fwd_packets": "Forward Packets Volume",
    "total_bwd_packets": "Backward Packets Volume",
    "packet_rate": "Packet Transmission Rate",
    "total_fwd_bytes": "Forward Bytes Transferred",
    "total_bwd_bytes": "Backward Bytes Transferred",
    "byte_rate": "Bandwidth Utilization Rate",
    "mean_flow_duration": "Mean Flow Duration",
    "mean_packet_length": "Mean Packet Payload Size",
    "std_packet_length": "Packet Size Variance",
    "mean_flow_iat": "Inter-Arrival Time (Mean)",
    "std_flow_iat": "Inter-Arrival Time Variance",
    "fwd_packet_rate": "Forward Packet Velocity",
    "bwd_packet_rate": "Backward Packet Velocity",
    "syn_flag_count": "SYN Flag Activity",
    "ack_flag_count": "ACK Flag Activity",
    "rst_flag_count": "RST Connection Aborts",
    "fin_flag_count": "FIN Connection Terminations",
    "psh_flag_count": "PSH Data Push Activity",
    "down_up_ratio_mean": "Downlink/Uplink Asymmetry",
    "active_mean": "Active Traffic Intervals",
    "idle_mean": "Idle Wait Intervals",
}


class RiskAttributor:
    """
    Computes mathematical feature attributions of the LSTM World Model's risk predictions.
    """

    def __init__(
        self,
        model: LSTMWorldModel,
        feature_cols: List[str] = None,
        device: str | torch.device = "cpu"
    ):
        self.model = model
        self.feature_cols = feature_cols or STATE_FEATURE_COLS
        self.device = torch.device(device)
        self.model.to(self.device)
        self.model.eval()

    def attribute_risk(
        self,
        input_sequence: np.ndarray,
        num_steps: int = 20,
        baseline: np.ndarray = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Calculates Integrated Gradients attribution for future risk score.

        Args:
            input_sequence: Observed past window S(t-29)...S(t) [30, 25] or [1, 30, 25].
            num_steps: Number of Riemann integration steps along the straight line path.
            baseline: Baseline reference input (default: all zeros / benign baseline).
            top_k: Number of top contributing features to highlight.

        Returns:
            Dictionary with feature attribution scores, percentages, and narrative explanation.
        """
        # Ensure 3D: [1, lookback, features]
        if input_sequence.ndim == 2:
            x_input = input_sequence[np.newaxis, :, :].copy()
        else:
            x_input = input_sequence.copy()

        if baseline is None:
            baseline = np.zeros_like(x_input)
        elif baseline.ndim == 2:
            baseline = baseline[np.newaxis, :, :].copy()

        diff = x_input - baseline
        total_gradients = np.zeros_like(x_input)

        # Approximate path integral: integral_0^1 grad(baseline + alpha * diff) d_alpha
        alphas = np.linspace(0.0, 1.0, num=num_steps, endpoint=True)

        for alpha in alphas:
            interpolated = baseline + alpha * diff
            x_tensor = torch.tensor(
                interpolated,
                dtype=torch.float32,
                device=self.device,
                requires_grad=True
            )

            # Forward pass to risk head
            out = self.model(x_tensor)
            risk_score = out["risk"]  # [1, 1]

            # Compute gradients with respect to input state sequence
            self.model.zero_grad()
            risk_score.backward()

            grad = x_tensor.grad.detach().cpu().numpy()
            total_gradients += grad

        # Integrated Gradients = (x - x') * average_gradient
        avg_gradients = total_gradients / num_steps
        ig_matrix = diff * avg_gradients  # Shape: [1, lookback, features]

        # Aggregate across the 30 temporal steps to get per-feature impact
        # We take the mean across the lookback horizon
        per_feature_scores = np.mean(ig_matrix[0], axis=0)  # [features]

        # Absolute magnitude represents feature importance
        abs_scores = np.abs(per_feature_scores)
        total_magnitude = np.sum(abs_scores) + 1e-9
        importance_pct = (abs_scores / total_magnitude) * 100.0

        # Sort features by importance
        sorted_indices = np.argsort(abs_scores)[::-1]

        attributions = []
        for rank, idx in enumerate(sorted_indices[:top_k], start=1):
            col_name = self.feature_cols[idx]
            raw_score = float(per_feature_scores[idx])
            pct = round(float(importance_pct[idx]), 1)
            direction = "RISK ESCALATION (+)" if raw_score >= 0 else "RISK MITIGATION (-)"

            attributions.append({
                "rank": rank,
                "feature_code": col_name,
                "feature_name": FEATURE_DISPLAY_NAMES.get(col_name, col_name),
                "importance_pct": pct,
                "raw_gradient_score": round(raw_score, 4),
                "direction": direction
            })

        # Generate automated analyst explanation
        top_driver_1 = attributions[0]
        top_driver_2 = attributions[1]
        narrative = (
            f"Future risk trajectory is primarily driven by {top_driver_1['feature_name']} "
            f"({top_driver_1['importance_pct']}%) and {top_driver_2['feature_name']} "
            f"({top_driver_2['importance_pct']}%)."
        )

        return {
            "top_contributing_features": attributions,
            "analyst_narrative": narrative,
            "all_feature_scores": {
                self.feature_cols[i]: round(float(per_feature_scores[i]), 5)
                for i in range(len(self.feature_cols))
            }
        }

    def attribute_trajectory(
        self,
        input_sequence: np.ndarray,
        forecast_timeline: List[Dict[str, Any]],
        num_steps: int = 15,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Attributes risk drivers across both the current state and the multi-step future
        forecast trajectory (t+1, t+2, ... t+K).

        Args:
            input_sequence: Observed past window S(t-29)...S(t).
            forecast_timeline: Multi-step forecast list from KStepSimulator.simulate.
            num_steps: Number of integration steps for Integrated Gradients.
            top_k: Number of top drivers to extract per step.

        Returns:
            Dictionary containing base attribution, per-step trajectory explanations,
            and executive analyst narrative.
        """
        # 1. Base attribution on active state
        base_xai = self.attribute_risk(input_sequence, num_steps=num_steps, top_k=top_k)

        # 2. Trajectory per-step attribution
        trajectory_steps = []
        all_feature_scores = base_xai["all_feature_scores"]

        for item in forecast_timeline:
            step_name = item.get("step", "t+1")
            risk_pct = item.get("predicted_risk_pct", 0.0)
            stage_name = item.get("predicted_stage_name", "Normal")
            norm_state = item.get("normalized_state", None)

            # Determine drivers for this specific step
            step_feature_impacts = []
            for i, col in enumerate(self.feature_cols):
                base_score = all_feature_scores.get(col, 0.0)
                norm_val = norm_state[i] if norm_state is not None and len(norm_state) > i else 0.0
                impact = base_score * (1.0 + max(0.0, float(norm_val)))
                step_feature_impacts.append((col, impact))

            # Sort by absolute impact
            step_feature_impacts.sort(key=lambda x: abs(x[1]), reverse=True)

            top_drivers = []
            step_attributions = []
            for rank, (col, imp) in enumerate(step_feature_impacts[:top_k], start=1):
                feat_name = FEATURE_DISPLAY_NAMES.get(col, col)
                direction = "RISK ESCALATION (+)" if imp >= 0 else "RISK MITIGATION (-)"
                top_drivers.append(feat_name)
                step_attributions.append({
                    "rank": rank,
                    "feature_code": col,
                    "feature_name": feat_name,
                    "direction": direction,
                    "impact_score": round(imp, 4)
                })

            trajectory_steps.append({
                "step": step_name,
                "minutes_ahead": item.get("minutes_ahead", 1),
                "predicted_risk_pct": risk_pct,
                "predicted_stage_name": stage_name,
                "main_drivers": top_drivers[:3],
                "attributions": step_attributions
            })

        # Generate comprehensive trajectory narrative
        top_driver_1 = base_xai["top_contributing_features"][0]["feature_name"]
        top_driver_2 = base_xai["top_contributing_features"][1]["feature_name"]
        max_fut_risk = max([s["predicted_risk_pct"] for s in trajectory_steps]) if trajectory_steps else 0.0

        if max_fut_risk >= 50.0:
            narrative = (
                f"High-risk escalation trajectory projected (peak {max_fut_risk:.1f}%), "
                f"heavily driven by {top_driver_1} and {top_driver_2}. "
                f"Tactical behavior indicates rapid threat acceleration requiring immediate mitigation."
            )
        elif max_fut_risk >= 20.0:
            narrative = (
                f"Moderate threat risk escalation projected (peak {max_fut_risk:.1f}%), "
                f"driven by {top_driver_1} with anomalous probing activity."
            )
        else:
            narrative = (
                f"Network operations remain within nominal baseline bounds (peak risk {max_fut_risk:.1f}%). "
                f"Feature variance remains stabilized by standard operational traffic."
            )

        return {
            "current_state_attribution": base_xai,
            "top_contributing_features": base_xai["top_contributing_features"],
            "trajectory_steps": trajectory_steps,
            "analyst_narrative": narrative,
            "all_feature_scores": all_feature_scores
        }

