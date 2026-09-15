"""
1-Minute Network State Aggregator Module.
Constructs discrete macro-behavioural network state vectors S(t) in R^25
from flow records, and aligns multi-task ground truth targets.
"""

from typing import Dict, Any, Tuple, List
import numpy as np
import pandas as pd

# Stage mapping dictionary aligning with MITRE tactical stages
STAGE_MAPPING = {
    "BENIGN": 0,
    "PORTSCAN": 1,
    "FTP-PATATOR": 2,
    "SSH-PATATOR": 2,
    "BRUTE FORCE": 2,
    "DOS": 3,
    "DDOS": 3,
    "BOTNET": 4,
    "INFILTRATION": 4,
    "WEB ATTACK": 4,
}

STATE_FEATURE_COLS = [
    "flow_count",
    "unique_dst_ports",
    "unique_src_ports",
    "port_diversity_ratio",
    "total_fwd_packets",
    "total_bwd_packets",
    "packet_rate",
    "total_fwd_bytes",
    "total_bwd_bytes",
    "byte_rate",
    "mean_flow_duration",
    "mean_packet_length",
    "std_packet_length",
    "mean_flow_iat",
    "std_flow_iat",
    "fwd_packet_rate",
    "bwd_packet_rate",
    "syn_flag_count",
    "ack_flag_count",
    "rst_flag_count",
    "fin_flag_count",
    "psh_flag_count",
    "down_up_ratio_mean",
    "active_mean",
    "idle_mean",
]


def resolve_dominant_stage(series: pd.Series) -> int:
    """Finds the dominant attack stage in a minute window."""
    attacks = [s.strip().upper() for s in series if s.strip().upper() != "BENIGN"]
    if not attacks:
        return 0
    # Most common attack in this window
    most_common = max(set(attacks), key=attacks.count)
    for key, stage_id in STAGE_MAPPING.items():
        if key in most_common:
            return stage_id
    return 1  # Default to Recon / Anomaly


def construct_network_states(
    df: pd.DataFrame,
    window_col: str = "minute_window",
    reindex_continuous: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Aggregates flow records into 1-minute discrete state vectors S(t).

    Args:
        df: Cleaned and chronologically sorted flow DataFrame.
        window_col: Column containing floored minute timestamp.
        reindex_continuous: Whether to fill idle minutes to maintain continuous grid.

    Returns:
        Tuple of (state DataFrame with S(t) features + targets, aggregation metadata)
    """
    if window_col not in df.columns:
        raise KeyError(f"Window column '{window_col}' not found.")

    # 1. Group by minute_window and calculate base aggregates
    grouped = df.groupby(window_col)

    states = pd.DataFrame(index=grouped.indices.keys())
    states.index.name = "timestamp"

    # Aggregations
    states["flow_count"] = grouped["Flow Duration"].count()
    states["unique_dst_ports"] = grouped["Destination Port"].nunique()
    states["unique_src_ports"] = grouped["Source Port"].nunique()
    states["total_fwd_packets"] = grouped["Total Fwd Packets"].sum()
    states["total_bwd_packets"] = grouped["Total Backward Packets"].sum()
    states["total_fwd_bytes"] = grouped["Total Length of Fwd Packets"].sum()
    states["total_bwd_bytes"] = grouped["Total Length of Bwd Packets"].sum()
    states["mean_flow_duration"] = grouped["Flow Duration"].mean()
    states["mean_packet_length"] = grouped["Packet Length Mean"].mean()
    states["std_packet_length"] = grouped["Packet Length Std"].mean()
    states["mean_flow_iat"] = grouped["Flow IAT Mean"].mean()
    states["std_flow_iat"] = grouped["Flow IAT Std"].mean()
    states["fwd_packet_rate"] = grouped["Fwd Packets/s"].mean()
    states["bwd_packet_rate"] = grouped["Bwd Packets/s"].mean()
    states["syn_flag_count"] = grouped["SYN Flag Count"].sum()
    states["ack_flag_count"] = grouped["ACK Flag Count"].sum()
    states["rst_flag_count"] = grouped["RST Flag Count"].sum()
    states["fin_flag_count"] = grouped["FIN Flag Count"].sum()
    states["psh_flag_count"] = grouped["PSH Flag Count"].sum()
    states["down_up_ratio_mean"] = grouped["Down/Up Ratio"].mean()
    states["active_mean"] = grouped["Active Mean"].mean()
    states["idle_mean"] = grouped["Idle Mean"].mean()

    # Derived Macro-Behavioural Features
    states["port_diversity_ratio"] = states["unique_dst_ports"] / np.maximum(states["flow_count"], 1)
    states["packet_rate"] = (states["total_fwd_packets"] + states["total_bwd_packets"]) / 60.0
    states["byte_rate"] = (states["total_fwd_bytes"] + states["total_bwd_bytes"]) / 60.0

    # Ground Truth Annotations
    states["attack_flow_count"] = grouped["is_attack"].sum()
    states["risk_score"] = states["attack_flow_count"] / np.maximum(states["flow_count"], 1)
    states["is_attack_state"] = (states["attack_flow_count"] > 0).astype(int)
    states["stage_id"] = grouped["Label"].apply(resolve_dominant_stage)

    # Sort index chronologically
    states = states.sort_index()

    # 2. Continuous 1-Minute Grid Reindexing (Zero Temporal Distortion)
    observed_windows = len(states)
    if reindex_continuous and observed_windows > 1:
        full_idx = pd.date_range(start=states.index.min(), end=states.index.max(), freq="1min")
        states = states.reindex(full_idx)
        # Fill idle minutes with 0 flows and 0 rates
        states["flow_count"] = states["flow_count"].fillna(0)
        states["attack_flow_count"] = states["attack_flow_count"].fillna(0)
        states["risk_score"] = states["risk_score"].fillna(0.0)
        states["is_attack_state"] = states["is_attack_state"].fillna(0).astype(int)
        states["stage_id"] = states["stage_id"].fillna(0).astype(int)
        # Fill all remaining feature columns with 0
        states = states.fillna(0.0)
        states.index.name = "timestamp"

    total_states = len(states)
    attack_states = int(states["is_attack_state"].sum())
    benign_states = total_states - attack_states

    metadata = {
        "observed_windows": observed_windows,
        "total_continuous_states": total_states,
        "idle_minutes_filled": total_states - observed_windows,
        "attack_states_count": attack_states,
        "benign_states_count": benign_states,
        "feature_count": len(STATE_FEATURE_COLS),
        "feature_list": STATE_FEATURE_COLS,
    }

    return states.reset_index(), metadata
