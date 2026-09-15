"""
Multi-Task Training Pipeline for Network World Model.
Balances state prediction (MSE), risk estimation (BCE), and stage classification (CE)
with early checkpointing on validation performance.
"""

from pathlib import Path
from typing import Dict, Any, Tuple
import json
import yaml
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau

from src.models.world_model import LSTMWorldModel
from src.sequence_builder.dataset import prepare_temporal_dataloaders


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def train_world_model(
    state_parquet_path: str | Path = "data/state_vectors/Tuesday-WorkingHours_state_1min.parquet",
    config_path: str | Path = "config/config.yaml",
    save_model_path: str | Path = "models/lstm_world_model_best.pt",
    history_path: str | Path = "models/training_history.json"
) -> Tuple[LSTMWorldModel, Dict[str, Any]]:
    """
    Trains the multi-task LSTM World Model on 1-minute state sequences.
    """
    cfg = load_config(str(config_path))
    m_cfg = cfg.get("model", {})
    w_cfg = cfg.get("windowing", {})
    s_cfg = cfg.get("sequence", {})

    lookback_steps = s_cfg.get("lookback_steps", 30)
    forecast_horizon = s_cfg.get("forecast_horizon", 5)
    batch_size = m_cfg.get("batch_size", 32)
    epochs = m_cfg.get("epochs", 40)
    lr = m_cfg.get("learning_rate", 0.001)

    loss_weights = m_cfg.get("loss_weights", {
        "state_prediction": 1.0,
        "risk_prediction": 1.0,
        "stage_prediction": 0.5
    })
    w_state = loss_weights.get("state_prediction", 1.0)
    w_risk = loss_weights.get("risk_prediction", 1.0)
    w_stage = loss_weights.get("stage_prediction", 0.5)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Training] Using compute device: {device}")

    # 1. Load State Table & Build Temporal DataLoaders
    df_states = pd.read_parquet(state_parquet_path)
    train_loader, val_loader, test_loader, scaler, split_meta = prepare_temporal_dataloaders(
        state_df=df_states,
        lookback_steps=lookback_steps,
        forecast_horizon=forecast_horizon,
        batch_size=batch_size,
        train_ratio=0.70,
        val_ratio=0.15
    )

    input_dim = split_meta["sequence_shape"][1]  # 25

    # 2. Instantiate World Model
    model = LSTMWorldModel(
        input_dim=input_dim,
        hidden_dim=m_cfg.get("hidden_dim", 128),
        latent_dim=m_cfg.get("latent_dim", 64),
        num_layers=m_cfg.get("num_layers", 2),
        num_stages=5,
        dropout=m_cfg.get("dropout", 0.2)
    ).to(device)

    # 3. Loss Functions & Optimizer
    criterion_state = nn.MSELoss()
    criterion_risk = nn.BCELoss()
    criterion_stage = nn.CrossEntropyLoss()

    optimizer = Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=5)

    history = {
        "train_loss": [], "val_loss": [],
        "train_state_loss": [], "train_risk_loss": [], "train_stage_loss": [],
        "val_state_loss": [], "val_risk_loss": [], "val_stage_loss": []
    }

    best_val_loss = float("inf")
    best_epoch = 0

    print("\n" + "=" * 65)
    print("STARTING MULTI-TASK WORLD MODEL TRAINING")
    print("=" * 65)

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        t_state_loss, t_risk_loss, t_stage_loss = 0.0, 0.0, 0.0

        for batch in train_loader:
            x = batch["x_seq"].to(device)
            y_state = batch["target_state"].to(device)
            y_risk = batch["target_risk"].to(device)
            y_stage = batch["target_stage"].to(device)

            optimizer.zero_grad()
            out = model(x)

            l_state = criterion_state(out["next_state"], y_state)
            l_risk = criterion_risk(out["risk"], y_risk)
            l_stage = criterion_stage(out["stage_logits"], y_stage)

            total_loss = (w_state * l_state) + (w_risk * l_risk) + (w_stage * l_stage)

            total_loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            train_loss += total_loss.item()
            t_state_loss += l_state.item()
            t_risk_loss += l_risk.item()
            t_stage_loss += l_stage.item()

        n_train = len(train_loader)
        avg_train = train_loss / n_train
        avg_t_state = t_state_loss / n_train
        avg_t_risk = t_risk_loss / n_train
        avg_t_stage = t_stage_loss / n_train

        # Validation Pass
        model.eval()
        val_loss = 0.0
        v_state_loss, v_risk_loss, v_stage_loss = 0.0, 0.0, 0.0

        with torch.no_grad():
            for batch in val_loader:
                x = batch["x_seq"].to(device)
                y_state = batch["target_state"].to(device)
                y_risk = batch["target_risk"].to(device)
                y_stage = batch["target_stage"].to(device)

                out = model(x)
                l_state = criterion_state(out["next_state"], y_state)
                l_risk = criterion_risk(out["risk"], y_risk)
                l_stage = criterion_stage(out["stage_logits"], y_stage)

                total_val = (w_state * l_state) + (w_risk * l_risk) + (w_stage * l_stage)

                val_loss += total_val.item()
                v_state_loss += l_state.item()
                v_risk_loss += l_risk.item()
                v_stage_loss += l_stage.item()

        n_val = len(val_loader)
        avg_val = val_loss / n_val
        avg_v_state = v_state_loss / n_val
        avg_v_risk = v_risk_loss / n_val
        avg_v_stage = v_stage_loss / n_val

        scheduler.step(avg_val)

        history["train_loss"].append(round(avg_train, 5))
        history["val_loss"].append(round(avg_val, 5))
        history["train_state_loss"].append(round(avg_t_state, 5))
        history["train_risk_loss"].append(round(avg_t_risk, 5))
        history["train_stage_loss"].append(round(avg_t_stage, 5))
        history["val_state_loss"].append(round(avg_v_state, 5))
        history["val_risk_loss"].append(round(avg_v_risk, 5))
        history["val_stage_loss"].append(round(avg_v_stage, 5))

        # Checkpoint Best Model
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            best_epoch = epoch
            save_path = Path(save_model_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_val_loss": best_val_loss,
                "config": m_cfg,
                "input_dim": input_dim
            }, save_path)
            marker = "*"
        else:
            marker = " "

        if epoch % 5 == 0 or epoch == 1 or marker == "*":
            print(f"Epoch [{epoch:02d}/{epochs:02d}] {marker} Train Loss: {avg_train:.4f} (State: {avg_t_state:.3f}, Risk: {avg_t_risk:.3f}) | Val Loss: {avg_val:.4f} (Risk: {avg_v_risk:.3f})")

    print("\n" + "=" * 65)
    print(f"[Training Complete] Best Checkpoint at Epoch {best_epoch:02d} with Val Loss: {best_val_loss:.4f}")
    print(f"Model saved to: {save_model_path}")

    # Save training history
    hist_file = Path(history_path)
    hist_file.parent.mkdir(parents=True, exist_ok=True)
    with open(hist_file, "w") as f:
        json.dump({
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "epochs": epochs,
            "history": history
        }, f, indent=2)

    return model, history


if __name__ == "__main__":
    train_world_model()
