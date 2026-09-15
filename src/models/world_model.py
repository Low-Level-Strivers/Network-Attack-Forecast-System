"""
Multi-Task PyTorch LSTM World Model Architecture.
Learns internal network dynamics z(t) and predicts next-state transitions,
future attack risk probability, and attack tactical stages concurrently.
"""

from typing import Dict
import torch
import torch.nn as nn


class LSTMWorldModel(nn.Module):
    """
    Multi-Task LSTM Network World Model.

    Inputs:
        x: Tensor of shape [B, L, F] (Lookback sequence of normalized network states)

    Outputs:
        Dictionary containing:
        - next_state: [B, F] (Predicted normalized state S(t+1))
        - risk: [B, 1] (Estimated attack probability in [0, 1])
        - stage_logits: [B, num_stages] (Tactical stage classification logits)
        - latent_z: [B, latent_dim] (Learned network dynamics representation)
    """

    def __init__(
        self,
        input_dim: int = 25,
        hidden_dim: int = 128,
        latent_dim: int = 64,
        num_layers: int = 2,
        num_stages: int = 5,
        dropout: float = 0.2
    ):
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.num_stages = num_stages

        # 1. Temporal LSTM Encoder
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )

        # 2. Latent Dynamics Projector z(t)
        self.to_latent = nn.Sequential(
            nn.Linear(hidden_dim, latent_dim),
            nn.LayerNorm(latent_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )

        # 3. Head 1: Next-State Prediction (State Transition Dynamics)
        self.next_state_head = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(64, input_dim)
        )

        # 4. Head 2: Future Risk Estimation (Severity / Probability)
        self.risk_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )

        # 5. Head 3: Attack Tactical Stage Classification (MITRE Alignment)
        self.stage_head = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(32, num_stages)
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass over sequence of network states.
        """
        # x: [Batch, Lookback, Features]
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Extract final hidden state of the top layer
        final_h = h_n[-1]  # [Batch, hidden_dim]

        # Project to latent state z(t)
        z = self.to_latent(final_h)  # [Batch, latent_dim]

        # Multi-task heads
        pred_next_state = self.next_state_head(z)
        pred_risk = self.risk_head(z)
        pred_stage_logits = self.stage_head(z)

        return {
            "next_state": pred_next_state,
            "risk": pred_risk,
            "stage_logits": pred_stage_logits,
            "latent_z": z
        }
