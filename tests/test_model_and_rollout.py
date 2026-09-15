"""
Unit Tests for Phase 5 (LSTM World Model) and Phase 6 (K-Step Rollout Engine).
"""

import sys
from pathlib import Path

# Ensure project root is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
import torch
import torch.nn as nn

from src.models.world_model import LSTMWorldModel
from src.feature_engineering.scaler import StateScaler
from src.forecasting.rollout_engine import KStepSimulator
from src.state_builder.aggregator import STATE_FEATURE_COLS


def test_world_model_forward():
    B = 8
    L = 30
    F = len(STATE_FEATURE_COLS)  # 25

    model = LSTMWorldModel(
        input_dim=F,
        hidden_dim=64,
        latent_dim=32,
        num_layers=1,
        num_stages=5
    )

    dummy_input = torch.randn(B, L, F)
    out = model(dummy_input)

    assert "next_state" in out
    assert "risk" in out
    assert "stage_logits" in out
    assert "latent_z" in out

    assert out["next_state"].shape == (B, F)
    assert out["risk"].shape == (B, 1)
    assert out["stage_logits"].shape == (B, 5)
    assert out["latent_z"].shape == (B, 32)

    # Check risk probability bounds [0, 1]
    assert (out["risk"] >= 0.0).all() and (out["risk"] <= 1.0).all()


def test_multi_task_backward():
    F = len(STATE_FEATURE_COLS)
    model = LSTMWorldModel(input_dim=F, hidden_dim=32, latent_dim=16, num_layers=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    x = torch.randn(4, 30, F)
    y_state = torch.randn(4, F)
    y_risk = torch.rand(4, 1)
    y_stage = torch.randint(0, 5, (4,))

    out = model(x)
    l_state = nn.MSELoss()(out["next_state"], y_state)
    l_risk = nn.BCELoss()(out["risk"], y_risk)
    l_stage = nn.CrossEntropyLoss()(out["stage_logits"], y_stage)

    total_loss = l_state + l_risk + l_stage
    optimizer.zero_grad()
    total_loss.backward()

    # Check gradients exist
    for p in model.parameters():
        if p.requires_grad:
            assert p.grad is not None


def test_k_step_simulation():
    F = len(STATE_FEATURE_COLS)
    model = LSTMWorldModel(input_dim=F, hidden_dim=32, latent_dim=16, num_layers=1)

    # Fit a dummy scaler
    dummy_df = pd.DataFrame(np.random.rand(10, F) * 100, columns=STATE_FEATURE_COLS)
    scaler = StateScaler(feature_cols=STATE_FEATURE_COLS).fit(dummy_df)

    simulator = KStepSimulator(model=model, scaler=scaler, device="cpu")

    # History sequence of 30 steps
    history = np.random.randn(30, F).astype(np.float32)

    res = simulator.simulate(history_sequence=history, k_steps=5, risk_threshold=0.50)

    assert res["forecast_horizon_k"] == 5
    assert len(res["risk_trajectory"]) == 5
    assert len(res["stage_trajectory"]) == 5
    assert len(res["forecast_timeline"]) == 5
    assert "early_warning" in res

    first_step = res["forecast_timeline"][0]
    assert "predicted_risk_pct" in first_step
    assert "physical_metrics" in first_step
    assert "flow_count" in first_step["physical_metrics"]


if __name__ == "__main__":
    print("Running Model & Rollout Unit Tests...")
    test_world_model_forward()
    print("  [OK] Multi-Task World Model forward pass test passed")
    test_multi_task_backward()
    print("  [OK] Multi-Task loss backward propagation test passed")
    test_k_step_simulation()
    print("  [OK] K-Step Autoregressive Rollout Simulation test passed")
    print("\nALL PHASE 5 & 6 UNIT TESTS PASSED! [OK]")
