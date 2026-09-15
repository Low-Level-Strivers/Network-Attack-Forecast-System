"""
End-to-End Security Intelligence Demonstration.
Combines K-Step Rollout Simulation, MITRE ATT&CK Mapping, and Integrated Gradients XAI.
"""

import sys
from pathlib import Path

# Ensure project root in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import numpy as np

from src.forecasting.rollout_engine import KStepSimulator
from src.mitre.mapper import MitreMapper
from src.explainability.attributor import RiskAttributor
from src.feature_engineering.scaler import StateScaler


def render_ascii_bar(pct: float, max_width: int = 20) -> str:
    """Renders a simple ASCII progress bar."""
    filled = int(round((pct / 100.0) * max_width))
    return "#" * filled + "-" * (max_width - filled)


def run_security_intelligence_demo(
    state_parquet: str = "data/state_vectors/Tuesday-WorkingHours_state_1min.parquet",
    sample_idx: int = 72,
    k_steps: int = 5
):
    print("=" * 75)
    print("AI-POWERED PREDICTIVE CYBER DEFENCE: SECURITY INTELLIGENCE CONSOLE")
    print("=" * 75)

    df_states = pd.read_parquet(state_parquet)
    scaler = StateScaler.load("models/state_scaler.joblib")

    simulator = KStepSimulator.load_from_checkpoint(
        model_path="models/lstm_world_model_best.pt",
        scaler_path="models/state_scaler.joblib"
    )

    attributor = RiskAttributor(model=simulator.model)

    # 1. Observed Window
    history_df = df_states.iloc[sample_idx - 30:sample_idx]
    norm_history = scaler.transform(history_df)
    current_time = df_states.iloc[sample_idx - 1]["timestamp"]
    current_risk = df_states.iloc[sample_idx - 1]["risk_score"]

    print(f"\n[1. CURRENT NETWORK OBSERVATION @ {current_time}]")
    print(f"  Total Flows (1 min):    {int(history_df.iloc[-1]['flow_count']):,}")
    print(f"  Unique Dest Ports:      {int(history_df.iloc[-1]['unique_dst_ports'])}")
    print(f"  Packet Rate:            {history_df.iloc[-1]['packet_rate']:.1f} pkts/sec")
    print(f"  SYN Flags:              {int(history_df.iloc[-1]['syn_flag_count'])}")
    print(f"  Current Attack Risk:    {current_risk * 100:.1f}%")

    # 2. K-Step Simulation Rollout
    print(f"\n[2. K-STEP AUTOREGRESSIVE FORECAST (K={k_steps})]")
    rollout = simulator.simulate(norm_history, k_steps=k_steps, risk_threshold=0.05)

    print("-" * 75)
    print(f"{'STEP':<6} | {'TIME HORIZON':<14} | {'PROJECTED RISK':<16} | {'PROJECTED STAGE':<26}")
    print("-" * 75)
    for item in rollout["forecast_timeline"]:
        print(f"{item['step']:<6} | +{item['minutes_ahead']} min ahead    | {item['predicted_risk_pct']:>5.1f}%          | {item['predicted_stage_name']}")
    print("-" * 75)

    # 3. MITRE ATT&CK Mapping on Future State (t+1)
    print(f"\n[3. MITRE ATT&CK TACTICAL ALIGNMENT (for t+1)]")
    t1_stage = rollout["forecast_timeline"][0]["predicted_stage_id"]
    t1_risk = rollout["forecast_timeline"][0]["predicted_risk_pct"] / 100.0
    t1_metrics = rollout["forecast_timeline"][0]["physical_metrics"]

    mitre_intel = MitreMapper.map_stage_to_mitre(
        stage_id=t1_stage,
        risk_score=t1_risk,
        physical_metrics=t1_metrics
    )

    print(f"  Tactic:             {mitre_intel['tactic_name']} ({mitre_intel['tactic_id']})")
    print(f"  Technique:          {mitre_intel['technique_name']} [{mitre_intel['technique_id']}]")
    print(f"  Confidence Level:   {mitre_intel['confidence']}")
    print(f"  Threat Assessment:  {mitre_intel['description']}")
    print("  Recommended Actions:")
    for m in mitre_intel["mitigations"][:3]:
        print(f"    - {m}")

    # 4. Explainability / Integrated Gradients Feature Attribution
    print(f"\n[4. EXPLAINABILITY: WHY IS FUTURE RISK ESCALATING?]")
    xai_res = attributor.attribute_risk(norm_history, num_steps=15, top_k=5)

    print(f"  {xai_res['analyst_narrative']}\n")
    print(f"  {'RANK':<5} | {'FEATURE NAME':<30} | {'IMPACT BAR':<22} | {'CONTRIBUTION'}")
    print("  " + "-" * 70)
    for feat in xai_res["top_contributing_features"]:
        bar = render_ascii_bar(feat["importance_pct"], max_width=20)
        print(f"  #{feat['rank']:<4} | {feat['feature_name']:<30} | [{bar}] | {feat['importance_pct']:>5.1f}% ({feat['direction']})")

    # 5. Early Warning Summary
    print("\n" + "=" * 75)
    if rollout["early_warning"]:
        print(f"  [EARLY WARNING] Attack progression forecasted to reach threat threshold in {rollout['prediction_lead_time_minutes']} min!")
    else:
        print("  [STATUS] System status normal. No imminent threshold breach forecasted.")
    print("=" * 75)


if __name__ == "__main__":
    run_security_intelligence_demo()
