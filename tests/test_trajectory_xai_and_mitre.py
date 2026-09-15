"""
Unit tests for trajectory-level explainability (XAI) and MITRE tactical progression.
"""

import sys
from pathlib import Path

# Ensure project root in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import torch

from src.mitre.mapper import MitreMapper
from src.explainability.attributor import RiskAttributor
from src.models.world_model import LSTMWorldModel
from src.state_builder.aggregator import STATE_FEATURE_COLS


def test_trajectory_mitre_and_xai():
    F = len(STATE_FEATURE_COLS)
    model = LSTMWorldModel(input_dim=F, hidden_dim=32, latent_dim=16, num_layers=1)
    attributor = RiskAttributor(model=model, feature_cols=STATE_FEATURE_COLS)

    dummy_seq = np.random.randn(30, F).astype(np.float32)

    # Dummy forecast timeline
    forecast_timeline = [
        {
            "step": "t+1",
            "minutes_ahead": 1,
            "predicted_risk_pct": 35.0,
            "predicted_stage_id": 1,
            "predicted_stage_name": "Reconnaissance (Scanning)",
            "physical_metrics": {"flow_count": 500, "unique_dst_ports": 120, "packet_rate": 45.0, "syn_flag_count": 80},
            "normalized_state": np.random.randn(F).astype(np.float32)
        },
        {
            "step": "t+2",
            "minutes_ahead": 2,
            "predicted_risk_pct": 65.0,
            "predicted_stage_id": 2,
            "predicted_stage_name": "Credential Access (Brute Force)",
            "physical_metrics": {"flow_count": 2200, "unique_dst_ports": 4, "packet_rate": 180.0, "syn_flag_count": 150},
            "normalized_state": np.random.randn(F).astype(np.float32)
        }
    ]

    # 1. Test XAI attribute_trajectory
    traj_xai = attributor.attribute_trajectory(dummy_seq, forecast_timeline, num_steps=5, top_k=4)
    assert "current_state_attribution" in traj_xai
    assert "top_contributing_features" in traj_xai
    assert "trajectory_steps" in traj_xai
    assert "analyst_narrative" in traj_xai
    assert len(traj_xai["trajectory_steps"]) == 2

    step1 = traj_xai["trajectory_steps"][0]
    assert step1["step"] == "t+1"
    assert len(step1["main_drivers"]) > 0
    assert len(step1["attributions"]) == 4

    # 2. Test MITRE map_trajectory_progression
    cur_state_info = {
        "stage_id": 0,
        "risk_score": 0.05,
        "physical_metrics": {"flow_count": 100, "unique_dst_ports": 2, "packet_rate": 10.0},
        "timestamp": "08:54"
    }

    progression = MitreMapper.map_trajectory_progression(cur_state_info, forecast_timeline)
    assert len(progression) == 3  # 1 observed + 2 predicted
    assert progression[0]["type"] == "OBSERVED"
    assert progression[1]["type"] == "PREDICTED"
    assert progression[2]["type"] == "PREDICTED"

    assert progression[0]["technique_id"] == "N/A"
    assert "T1046" in progression[1]["technique_id"]
    assert "T1110" in progression[2]["technique_id"]
    assert len(progression[1]["mitigations"]) > 0


if __name__ == "__main__":
    print("Running Trajectory XAI & MITRE Progression Unit Tests...")
    test_trajectory_mitre_and_xai()
    print("  [OK] Trajectory XAI & MITRE Progression tests passed successfully!")
