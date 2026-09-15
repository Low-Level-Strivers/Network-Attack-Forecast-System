"""
Demonstration script for K-Step Autoregressive Rollout Simulation.
Simulates future network state transitions and risk trajectory on real holdout states.
"""

from pathlib import Path
import json
import pandas as pd
import numpy as np

from src.forecasting.rollout_engine import KStepSimulator
from src.feature_engineering.scaler import StateScaler
from src.state_builder.aggregator import STATE_FEATURE_COLS


def run_demo_simulation(
    state_parquet: str = "data/state_vectors/Tuesday-WorkingHours_state_1min.parquet",
    sample_idx: int = 65,  # Approaching attack transition
    k_steps: int = 5
):
    print("=" * 70)
    print("AI-POWERED PREDICTIVE CYBER DEFENCE - K-STEP ROLLOUT DEMONSTRATION")
    print("=" * 70)

    df_states = pd.read_parquet(state_parquet)
    scaler = StateScaler.load("models/state_scaler.joblib")
    simulator = KStepSimulator.load_from_checkpoint(
        model_path="models/lstm_world_model_best.pt",
        scaler_path="models/state_scaler.joblib",
        device="cpu"
    )

    # Extract 30-minute lookback sequence leading up to sample_idx
    history_df = df_states.iloc[sample_idx - 30:sample_idx]
    norm_history = scaler.transform(history_df)
    current_time = df_states.iloc[sample_idx - 1]["timestamp"]
    current_risk = df_states.iloc[sample_idx - 1]["risk_score"]

    print(f"\n[CURRENT NETWORK STATUS at {current_time}]")
    print(f"  Observed 30-min window: {history_df.iloc[0]['timestamp']} -> {current_time}")
    print(f"  Current Flow Count: {int(history_df.iloc[-1]['flow_count']):,}")
    print(f"  Current Unique Dst Ports: {int(history_df.iloc[-1]['unique_dst_ports'])}")
    print(f"  Current Packet Rate: {history_df.iloc[-1]['packet_rate']:.1f} pkts/sec")
    print(f"  Current Risk Level: {current_risk * 100:.1f}%\n")

    # Run K-step simulation
    print(f"[SIMULATION ENGINE] Forecasting {k_steps} minutes into the future...")
    result = simulator.simulate(norm_history, k_steps=k_steps, risk_threshold=0.50)

    print("\n" + "-" * 70)
    print(f"{'STEP':<8} | {'HORIZON':<10} | {'PREDICTED RISK':<16} | {'ATTACK STAGE':<25}")
    print("-" * 70)
    for item in result["forecast_timeline"]:
        print(f"{item['step']:<8} | +{item['minutes_ahead']} min     | {item['predicted_risk_pct']:>5.1f}%          | {item['predicted_stage_name']}")
    print("-" * 70)

    print("\n[PHYSICAL METRICS FORECAST]")
    for item in result["forecast_timeline"]:
        m = item["physical_metrics"]
        print(f"  [{item['step']}] Flows: {m['flow_count']:>5} | Ports: {m['unique_dst_ports']:>4} | Pkts/s: {m['packet_rate']:>6.1f} | SYN Flags: {m['syn_flag_count']}")

    print("\n[SECURITY INSIGHTS & EARLY WARNING]")
    if result["early_warning"]:
        print(f"  [ALERT] EARLY WARNING TRIGGERED: High attack progression anticipated!")
        print(f"  [LEAD TIME] Actionable Lead Time: {result['prediction_lead_time_minutes']} minutes before threshold breach.")
    else:
        print(f"  [STATUS] Network behaviour projected to remain within normal baseline.")

    return result


if __name__ == "__main__":
    run_demo_simulation()
