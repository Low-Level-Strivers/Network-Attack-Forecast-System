"""
Predictive Cyber Defence: AI Network World Model SOC Console.
Sequential K-Step Forecasting, Persistent Operation Logging, Explainable AI (XAI),
MITRE ATT&CK Tactical Progression, and Historical State Exploration.
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import io
import time
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np

from dashboard.theme import (
    apply_light_theme,
    safe_html,
    render_semantic_card,
    render_semantic_alert,
    render_horizontal_attribution_chart,
    render_sequential_trajectory_chart,
    render_mitre_progression_timeline,
    render_state_stream,
    render_processing_pipeline
)
from src.ingestion.loader import sanitize_column_names
from src.preprocessing.cleaner import clean_flow_data
from src.preprocessing.timestamp_parser import parse_and_sort_timestamps
from src.state_builder.aggregator import construct_network_states, STATE_FEATURE_COLS
from src.forecasting.rollout_engine import KStepSimulator
from src.mitre.mapper import MitreMapper
from src.explainability.attributor import RiskAttributor, FEATURE_DISPLAY_NAMES
from src.feature_engineering.scaler import StateScaler
from src.storage.operation_logger import OperationLogger

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Predictive Cyber Defence | SOC Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply High-Contrast Executive Light Styling
apply_light_theme()

# Initialize Persistent Storage Logger
operation_logger = OperationLogger()


# ==========================================================
# CACHED MODEL & ENGINE LOADERS
# ==========================================================
@st.cache_resource
def load_forecast_engine():
    model_path = Path("models/lstm_world_model_best.pt")
    scaler_path = Path("models/state_scaler.joblib")
    if not model_path.exists() or not scaler_path.exists():
        st.error("Model checkpoints or scaler not found. Please verify setup.")
        st.stop()

    simulator = KStepSimulator.load_from_checkpoint(model_path, scaler_path, device="cpu")
    attributor = RiskAttributor(model=simulator.model)
    scaler = StateScaler.load(scaler_path)
    return simulator, attributor, scaler


simulator, attributor, scaler = load_forecast_engine()


# ==========================================================
# DYNAMIC CSV INGESTION & STATE CONSTRUCTION ENGINE
# ==========================================================
def process_dynamic_csv_with_stages(file_bytes: bytes, file_name: str, progress_callback=None) -> Tuple[pd.DataFrame, int]:
    """
    Ingests, cleans, parses, and aggregates an uploaded flow CSV into
    1-minute discrete state vectors S(t) with stage-by-stage tracking.
    """
    if progress_callback:
        progress_callback(0, "Processing")  # 1. Validation

    df_raw = pd.read_csv(io.BytesIO(file_bytes), low_memory=False)
    num_raw_rows = len(df_raw)

    if progress_callback:
        progress_callback(0, "Completed")
        progress_callback(1, "Processing")  # 2. Timestamp Parsing

    # Check if already state-vector aggregated
    if "flow_count" in df_raw.columns and "packet_rate" in df_raw.columns:
        if "timestamp" not in df_raw.columns:
            df_raw["timestamp"] = pd.date_range(start="2026-09-14 09:00:00", periods=len(df_raw), freq="1min")
        if "risk_score" not in df_raw.columns:
            df_raw["risk_score"] = 0.0
        if "is_attack_state" not in df_raw.columns:
            df_raw["is_attack_state"] = (df_raw["risk_score"] > 0.2).astype(int)
        if "stage_id" not in df_raw.columns:
            df_raw["stage_id"] = 0
        if progress_callback:
            for i in range(1, 8):
                progress_callback(i, "Completed")
        return df_raw, num_raw_rows

    # 1. Sanitize column headers
    df_raw.columns = sanitize_column_names(list(df_raw.columns))

    for col in df_raw.select_dtypes(include=["object"]).columns:
        df_raw[col] = df_raw[col].astype(str).str.strip()

    col_map = {}
    for c in df_raw.columns:
        cl = c.lower().replace("_", " ").strip()
        if cl in ["timestamp", "time", "date", "datetime"]:
            col_map[c] = "Timestamp"
        elif cl in ["label", "class", "attack"]:
            col_map[c] = "Label"
        elif cl in ["destination port", "dst port", "dport"]:
            col_map[c] = "Destination Port"
        elif cl in ["source port", "src port", "sport"]:
            col_map[c] = "Source Port"
        elif cl in ["flow duration", "duration"]:
            col_map[c] = "Flow Duration"
        elif cl in ["total fwd packets", "tot fwd pkts", "fwd packets"]:
            col_map[c] = "Total Fwd Packets"
        elif cl in ["total backward packets", "total bwd packets", "tot bwd pkts", "bwd packets"]:
            col_map[c] = "Total Backward Packets"
        elif cl in ["total length of fwd packets", "totlen fwd pkts"]:
            col_map[c] = "Total Length of Fwd Packets"
        elif cl in ["total length of bwd packets", "totlen bwd pkts"]:
            col_map[c] = "Total Length of Bwd Packets"
        elif cl in ["packet length mean", "pkt len mean"]:
            col_map[c] = "Packet Length Mean"
        elif cl in ["packet length std", "pkt len std"]:
            col_map[c] = "Packet Length Std"
        elif cl in ["flow iat mean"]:
            col_map[c] = "Flow IAT Mean"
        elif cl in ["flow iat std"]:
            col_map[c] = "Flow IAT Std"
        elif cl in ["fwd packets/s", "fwd pkts/s"]:
            col_map[c] = "Fwd Packets/s"
        elif cl in ["bwd packets/s", "bwd pkts/s"]:
            col_map[c] = "Bwd Packets/s"
        elif "syn" in cl and "flag" in cl:
            col_map[c] = "SYN Flag Count"
        elif "ack" in cl and "flag" in cl:
            col_map[c] = "ACK Flag Count"
        elif "rst" in cl and "flag" in cl:
            col_map[c] = "RST Flag Count"
        elif "fin" in cl and "flag" in cl:
            col_map[c] = "FIN Flag Count"
        elif "psh" in cl and "flag" in cl:
            col_map[c] = "PSH Flag Count"
        elif "down/up" in cl or "down up" in cl:
            col_map[c] = "Down/Up Ratio"
        elif "active mean" in cl:
            col_map[c] = "Active Mean"
        elif "idle mean" in cl:
            col_map[c] = "Idle Mean"

    if col_map:
        df_raw = df_raw.rename(columns=col_map)
        df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()].copy()

    if "Timestamp" not in df_raw.columns:
        df_raw["Timestamp"] = pd.date_range(start="2026-09-14 09:00:00", periods=len(df_raw), freq="1s")

    if "Label" not in df_raw.columns:
        df_raw["Label"] = "BENIGN"

    defaults = {
        "Flow Duration": 1000.0,
        "Destination Port": 80,
        "Source Port": 49152,
        "Total Fwd Packets": 1,
        "Total Backward Packets": 1,
        "Total Length of Fwd Packets": 64.0,
        "Total Length of Bwd Packets": 64.0,
        "Packet Length Mean": 64.0,
        "Packet Length Std": 0.0,
        "Flow IAT Mean": 100.0,
        "Flow IAT Std": 0.0,
        "Fwd Packets/s": 1.0,
        "Bwd Packets/s": 1.0,
        "SYN Flag Count": 0,
        "ACK Flag Count": 1,
        "RST Flag Count": 0,
        "FIN Flag Count": 0,
        "PSH Flag Count": 0,
        "Down/Up Ratio": 1.0,
        "Active Mean": 0.0,
        "Idle Mean": 0.0,
    }
    for col, def_val in defaults.items():
        if col not in df_raw.columns:
            df_raw[col] = def_val

    if progress_callback:
        progress_callback(1, "Completed")
        progress_callback(2, "Processing")  # 3. Data Cleaning

    # 2. Clean numeric columns & handle Inf/NaN
    df_clean, _ = clean_flow_data(df_raw, drop_duplicates=True)

    if progress_callback:
        progress_callback(2, "Completed")
        progress_callback(3, "Processing")  # 4. Feature Extraction

    # 3. Parse timestamps & sort chronologically
    df_sorted, _ = parse_and_sort_timestamps(df_clean)

    if progress_callback:
        progress_callback(3, "Completed")
        progress_callback(4, "Processing")  # 5. Time-Window Aggregation
        progress_callback(4, "Completed")
        progress_callback(5, "Processing")  # 6. Network State Construction

    # 4. Construct 1-minute discrete state vectors S(t)
    df_states, _ = construct_network_states(df_sorted, reindex_continuous=True)

    if progress_callback:
        progress_callback(5, "Completed")
        progress_callback(6, "Processing")  # 7. State Vector Generation
        progress_callback(6, "Completed")
        progress_callback(7, "Processing")  # 8. Sequential Forecast Initialization
        progress_callback(7, "Completed")

    return df_states, num_raw_rows


@st.cache_data
def load_default_sample_states() -> pd.DataFrame:
    """Loads baseline states and ensures persistent operation record exists."""
    default_path = Path("data/state_vectors/Tuesday-WorkingHours_state_1min.parquet")
    if default_path.exists():
        df = pd.read_parquet(default_path)
    else:
        raw_path = Path("data/raw/Tuesday-WorkingHours.pcap_ISCX.csv")
        if raw_path.exists():
            with open(raw_path, "rb") as f:
                df, _ = process_dynamic_csv_with_stages(f.read(), raw_path.name)
        else:
            st.error("Baseline dataset not found. Please upload a network traffic CSV.")
            st.stop()

    # Pre-seed baseline in operations logger so history is immediately active
    operation_logger.ensure_baseline_operation(df)
    return df


# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================
if "df_states" not in st.session_state:
    st.session_state.df_states = load_default_sample_states()
    st.session_state.dataset_name = "Tuesday-WorkingHours.pcap_ISCX.csv (445,641 flows)"
    st.session_state.current_idx = 65  # Default to elevated threat transition state
    st.session_state.is_playing = False
    st.session_state.k_horizon = 5
    st.session_state.interval_sec = 1.0

if "is_playing" not in st.session_state:
    st.session_state.is_playing = False


# ==========================================================
# SIDEBAR: PLATFORM MODULE NAVIGATION & CONTROLS
# ==========================================================
with st.sidebar:
    st.markdown("### **PREDICTIVE CYBER DEFENCE**")
    safe_html('<span class="badge-clean">SYSTEM ONLINE</span><p style="font-size: 12px; color: #555555; margin-top: 4px;">Network World Model v0.1.0</p>')
    st.markdown("---")

    st.markdown("#### **PLATFORM MODULES**")
    selected_page = st.radio(
        "Navigation",
        [
            "1. Executive SOC Dashboard",
            "2. Network State Telemetry",
            "3. MITRE ATT&CK Tactical Progression",
            "4. Explainable AI (XAI)",
            "5. CSV Ingestion & State Construction",
            "6. Operation History & State Explorer"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### **SIMULATION CONFIGURATION**")

    st.session_state.k_horizon = st.slider(
        "Forecast Horizon (K Steps)",
        min_value=1,
        max_value=10,
        value=int(st.session_state.k_horizon),
        step=1,
        help="Number of future minutes to forecast autoregressively"
    )

    st.session_state.interval_sec = st.slider(
        "Simulation Update Interval (sec)",
        min_value=0.5,
        max_value=5.0,
        value=float(st.session_state.interval_sec),
        step=0.5,
        help="Time between sequential state advances during live playback"
    )

    total_states = len(st.session_state.df_states)

    st.markdown("---")
    st.markdown("#### **QUICK SCENARIO JUMP**")
    scenario = st.selectbox(
        "Select Scenario",
        [
            "Active Brute Force (High Risk ~99%)",
            "Approaching Threat Transition (Elevated)",
            "Clean Operational Baseline (<1%)",
            "Latest Ingested State"
        ],
        index=0
    )

    if st.button("Jump to Scenario State", use_container_width=True):
        if "Brute Force" in scenario:
            st.session_state.current_idx = min(72, total_states)
        elif "Approaching" in scenario:
            st.session_state.current_idx = min(65, total_states)
        elif "Clean" in scenario:
            st.session_state.current_idx = min(40, total_states)
        else:
            st.session_state.current_idx = total_states
        st.session_state.is_playing = False
        st.rerun()

    st.markdown("---")
    st.markdown(
        f"<div style='font-size: 11px; color: #6C757D;'>"
        f"Active Dataset: <strong>{st.session_state.dataset_name}</strong><br>"
        f"Total States: <strong>{total_states}</strong><br>"
        f"Active State Index: <strong>#{st.session_state.current_idx}</strong>"
        f"</div>",
        unsafe_allow_html=True
    )


# ==========================================================
# STATE PREPARATION & SIMULATION EXECUTION
# ==========================================================
df_states = st.session_state.df_states
total_states = len(df_states)
current_idx = min(max(1, st.session_state.current_idx), total_states)
st.session_state.current_idx = current_idx

# Slice 30-minute lookback window leading to current_idx
history_df = df_states.iloc[max(0, current_idx - 30):current_idx].copy()
if len(history_df) < 30:
    pad_count = 30 - len(history_df)
    first_row = history_df.iloc[[0]] if len(history_df) > 0 else df_states.iloc[[0]]
    pad_df = pd.concat([first_row] * pad_count, ignore_index=True)
    history_df = pd.concat([pad_df, history_df], ignore_index=True)

norm_history = scaler.transform(history_df)
current_row = df_states.iloc[max(0, current_idx - 1)]
current_time_str = str(current_row["timestamp"])
current_risk_pct = round(float(current_row.get("risk_score", 0.0)) * 100, 1)

# Execute Live K-Step Autoregressive Simulation
rollout = simulator.simulate(norm_history, k_steps=st.session_state.k_horizon, risk_threshold=0.20)
t1_item = rollout["forecast_timeline"][0]
future_risk_pct = t1_item["predicted_risk_pct"]
future_stage = t1_item["predicted_stage_name"]
lead_time_min = rollout.get("prediction_lead_time_minutes") or 1


# ==========================================================
# REUSABLE SEQUENTIAL PLAYBACK CONTROLLER
# ==========================================================
def render_playback_controller():
    """Renders the interactive sequential playback control toolbar."""
    safe_html(
        f"""
        <div style="background: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 8px; padding: 12px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 13px; font-weight: 700; color: #111111; text-transform: uppercase; letter-spacing: 0.5px;">Sequential Simulation Playback</span>
                <span style="margin-left: 12px; font-size: 12px; color: #495057;">State: <strong>S{current_idx:03d} / S{total_states:03d}</strong> | Time: <strong>{current_time_str}</strong></span>
            </div>
            <div style="font-size: 12px; color: #495057;">
                Update Interval: <strong>{st.session_state.interval_sec:.1f}s</strong> | Horizon K: <strong>+{st.session_state.k_horizon}m</strong>
            </div>
        </div>
        """
    )

    c_play, c_pause, c_step_fwd, c_step_bwd, c_reset, c_slider = st.columns([1.2, 1.2, 1.4, 1.4, 1.2, 4.6])

    with c_play:
        if st.button("▶ Play", use_container_width=True, type="primary" if st.session_state.is_playing else "secondary"):
            st.session_state.is_playing = True
            st.rerun()

    with c_pause:
        if st.button("⏸ Pause", use_container_width=True, type="primary" if not st.session_state.is_playing else "secondary"):
            st.session_state.is_playing = False
            st.rerun()

    with c_step_fwd:
        if st.button("⏭ Step (+1)", use_container_width=True):
            st.session_state.is_playing = False
            st.session_state.current_idx = min(total_states, current_idx + 1)
            st.rerun()

    with c_step_bwd:
        if st.button("⏮ Back (-1)", use_container_width=True):
            st.session_state.is_playing = False
            st.session_state.current_idx = max(1, current_idx - 1)
            st.rerun()

    with c_reset:
        if st.button("⏮⏮ Reset", use_container_width=True):
            st.session_state.is_playing = False
            st.session_state.current_idx = 1
            st.rerun()

    with c_slider:
        slider_val = st.slider(
            "State Timeline Scrubber",
            min_value=1,
            max_value=total_states,
            value=current_idx,
            step=1,
            label_visibility="collapsed"
        )
        if slider_val != current_idx:
            st.session_state.is_playing = False
            st.session_state.current_idx = slider_val
            st.rerun()


# ==========================================================
# PAGE 1: EXECUTIVE SOC DASHBOARD
# ==========================================================
if "Executive" in selected_page:
    st.markdown("## **Predictive Cyber Defence — Executive SOC Dashboard**")
    st.markdown(
        f"<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        f"Sequential Network World Model Simulation & Autoregressive Risk Forecasting."
        f"</p>",
        unsafe_allow_html=True
    )

    # 1. Playback Control Bar
    render_playback_controller()

    # 2. Live State Pipeline Stream
    render_state_stream(
        current_idx=current_idx,
        total_states=total_states,
        state_ids=[f"S{i+1:03d}" for i in range(total_states)],
        timestamps=list(df_states["timestamp"]) if "timestamp" in df_states.columns else None
    )

    st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

    # 3. Dynamic Semantic Early Warning Banner
    render_semantic_alert(future_risk_pct, lead_time_min, future_stage)

    # 4. KPI Semantic Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_semantic_card("CURRENT ATTACK RISK", f"{current_risk_pct:.1f}%", f"Observed at state S{current_idx:03d}", risk_score=current_risk_pct / 100.0)
    with c2:
        diff_risk = future_risk_pct - current_risk_pct
        diff_str = f"+{diff_risk:.1f}% trend" if diff_risk >= 0 else f"{diff_risk:.1f}% trend"
        render_semantic_card("FORECASTED RISK (t+1)", f"{future_risk_pct:.1f}%", diff_str, risk_score=future_risk_pct / 100.0)
    with c3:
        render_semantic_card("PREDICTED ATTACK STAGE", future_stage.split("(")[0].strip(), f"Stage ID: {t1_item['predicted_stage_id']}", risk_score=future_risk_pct / 100.0)
    with c4:
        lead_str = f"+{lead_time_min} MIN" if rollout["early_warning"] else "Baseline Steady"
        render_semantic_card("PREDICTION LEAD TIME", lead_str, "Actionable Warning Margin", risk_score=future_risk_pct / 100.0)

    st.markdown("---")

    # 5. Sequential Risk Trajectory Chart
    st.markdown("### **Sequential Risk Trajectory Timeline (Observed History + K-Step Future Forecast)**")
    st.markdown("<p style='color: #6C757D; font-size: 13px; margin-top: -10px;'>Solid line: Observed historical risk leading to S(t). Prominent marker: Active state S(t). Dashed line: Multi-step future forecast.</p>", unsafe_allow_html=True)

    # Prepare observed history points leading to current_idx
    obs_slice = df_states.iloc[max(0, current_idx - 15):current_idx]
    observed_history_items = []
    for idx_row, row in obs_slice.iterrows():
        s_id = f"S{idx_row+1:03d}"
        r_val = float(row.get("risk_score", 0.0)) * 100.0
        t_str = str(row.get("timestamp", ""))[-8:-3]
        observed_history_items.append({
            "label": s_id,
            "risk_pct": round(r_val, 1),
            "time": t_str
        })

    render_sequential_trajectory_chart(
        observed_history=observed_history_items,
        forecast_timeline=rollout["forecast_timeline"],
        current_idx=current_idx,
        current_time_str=current_time_str
    )

    st.markdown("---")

    # 6. Dual Panel: Active State Telemetry vs. Projected Future Trajectory
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.markdown("### **Active Network State Telemetry S(t)**")
        t1, t2 = st.columns(2)
        with t1:
            render_semantic_card("FLOW COUNT", f"{int(current_row['flow_count']):,}", "Flows in active window")
            render_semantic_card("PACKET RATE", f"{current_row['packet_rate']:.1f}", "Packets / second")
            render_semantic_card("SYN BURSTS", f"{int(current_row['syn_flag_count']):,}", "SYN flag occurrences")
        with t2:
            render_semantic_card("DEST PORT DIVERSITY", f"{int(current_row['unique_dst_ports'])}", "Unique ports contacted")
            render_semantic_card("BANDWIDTH USAGE", f"{current_row['byte_rate'] / 1024:.1f} KB/s", "Throughput velocity")
            render_semantic_card("FLOW IAT MEAN", f"{current_row['mean_flow_iat']:.1f} ms", "Inter-arrival mean")

    with col_right:
        st.markdown("### **Projected Future Trajectory (t+1 ... t+K)**")
        forecast_rows = []
        for item in rollout["forecast_timeline"]:
            pm = item["physical_metrics"]
            forecast_rows.append({
                "Step": item["step"],
                "Horizon": f"+{item['minutes_ahead']}m",
                "Risk": f"{item['predicted_risk_pct']:.1f}%",
                "Stage": item["predicted_stage_name"].split("(")[0].strip(),
                "Flows": f"{pm['flow_count']:,}",
                "Ports": pm["unique_dst_ports"],
                "SYN Flags": pm["syn_flag_count"]
            })
        st.dataframe(pd.DataFrame(forecast_rows), use_container_width=True, hide_index=True)

        st.markdown(
            f"""
            <div style="background: #F8F9FA; border: 1px solid #CED4DA; border-radius: 6px; padding: 12px; margin-top: 10px; font-size: 13px;">
                <strong>Early Warning Intelligence:</strong> {rollout.get('early_warning_message', 'Normal operational baseline.')}
            </div>
            """,
            unsafe_allow_html=True
        )


# ==========================================================
# PAGE 2: NETWORK STATE TELEMETRY
# ==========================================================
elif "Telemetry" in selected_page:
    st.markdown("## **Network State Telemetry & State Vector S(t)**")
    render_playback_controller()

    st.markdown(
        f"<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        f"Detailed 25-dimensional macro-behavioural state vector inspection for state <strong>S{current_idx:03d}</strong> at <strong>{current_time_str}</strong>"
        f"</p>",
        unsafe_allow_html=True
    )

    # 4 Quick Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_semantic_card("TOTAL FLOWS", f"{int(current_row['flow_count']):,}", "Active 1-min interval")
    with c2:
        render_semantic_card("DEST PORT DIVERSITY", f"{int(current_row['unique_dst_ports'])}", "Unique destination ports")
    with c3:
        render_semantic_card("PACKET TRANSMISSION", f"{current_row['packet_rate']:.1f}", "Packets / sec")
    with c4:
        render_semantic_card("BANDWIDTH UTILIZATION", f"{current_row['byte_rate'] / 1024:.1f} KB/s", "Throughput")

    st.markdown("---")
    st.markdown("### **Observed 30-Minute Historical Telemetry Trends**")

    cols_to_plot = [c for c in ["flow_count", "unique_dst_ports", "packet_rate", "syn_flag_count"] if c in history_df.columns]
    trend_df = history_df[["timestamp"] + cols_to_plot].copy()
    trend_df = trend_df.set_index("timestamp")
    st.line_chart(trend_df)

    st.markdown("---")
    st.markdown("### **Complete 25-Dimensional Macro-Behavioural State Vector S(t)**")

    vector_items = []
    for col in STATE_FEATURE_COLS:
        val = current_row.get(col, 0.0)
        vector_items.append({
            "Feature Name": FEATURE_DISPLAY_NAMES.get(col, col),
            "Feature Code": col,
            "Raw Value": f"{val:,.2f}" if abs(val) >= 1 else f"{val:.4f}",
            "Normalized (Standardized)": f"{norm_history[-1, STATE_FEATURE_COLS.index(col)]:.3f}"
        })

    st.dataframe(pd.DataFrame(vector_items), use_container_width=True, hide_index=True)


# ==========================================================
# PAGE 3: MITRE ATT&CK TACTICAL PROGRESSION
# ==========================================================
elif "MITRE" in selected_page:
    st.markdown("## **MITRE ATT&CK Tactical Progression Timeline**")
    render_playback_controller()

    st.markdown(
        f"<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        f"Chronological mapping connecting <strong>Observed Behaviour at S({current_idx})</strong> "
        f"to <strong>Predicted Future Tactical Stages across Horizon +{st.session_state.k_horizon}m</strong>."
        f"</p>",
        unsafe_allow_html=True
    )

    current_state_info = {
        "stage_id": int(current_row.get("stage_id", 0)),
        "risk_score": current_risk_pct / 100.0,
        "physical_metrics": {
            "flow_count": current_row.get("flow_count", 0),
            "unique_dst_ports": current_row.get("unique_dst_ports", 0),
            "packet_rate": current_row.get("packet_rate", 0),
            "syn_flag_count": current_row.get("syn_flag_count", 0)
        },
        "timestamp": current_time_str
    }

    progression_items = MitreMapper.map_trajectory_progression(
        current_state_info=current_state_info,
        forecast_timeline=rollout["forecast_timeline"]
    )

    render_mitre_progression_timeline(progression_items)


# ==========================================================
# PAGE 4: EXPLAINABLE AI (XAI)
# ==========================================================
elif "Explainable" in selected_page:
    st.markdown("## **Explainable AI (XAI): Feature Attribution & Trajectory Drivers**")
    render_playback_controller()

    st.markdown(
        f"<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        f"Integrated Gradients path integrals explaining <em>why</em> the World Model projects future attack risk escalation."
        f"</p>",
        unsafe_allow_html=True
    )

    # Compute trajectory-level attribution
    xai_res = attributor.attribute_trajectory(
        input_sequence=norm_history,
        forecast_timeline=rollout["forecast_timeline"],
        num_steps=15,
        top_k=7
    )

    # Executive Analyst Narrative Card
    safe_html(f"""
    <div class="metric-card metric-card-neutral">
        <div style="font-weight: 700; font-size: 13px; margin-bottom: 6px; color: #495057; text-transform: uppercase;">EXECUTIVE ANALYST ATTRIBUTION SUMMARY</div>
        <p style="font-size: 15px; color: #111111; line-height: 1.5; margin: 0;">{xai_res['analyst_narrative']}</p>
    </div>
    """)

    st.markdown("### **Feature Attribution Ranking (Strictly Horizontal Bars)**")
    st.markdown(
        "<p style='color: #6C757D; font-size: 13px; margin-top: -10px;'>"
        "Color coding: <strong style='color:#C92A2A;'>Red</strong> = Risk Escalation (+), "
        "<strong style='color:#2B8A3E;'>Green</strong> = Risk Mitigation (-), "
        "<strong style='color:#495057;'>Slate</strong> = Neutral."
        "</p>",
        unsafe_allow_html=True
    )

    render_horizontal_attribution_chart(xai_res["top_contributing_features"])

    st.markdown("---")
    st.markdown("### **Step-by-Step Future Trajectory Explainability (Forecast Drivers)**")
    st.markdown(
        "<p style='color: #6C757D; font-size: 13px; margin-top: -10px;'>"
        "Detailed behavioral breakdown showing the primary risk driver features across each step of the future forecast horizon."
        "</p>",
        unsafe_allow_html=True
    )

    # Section 8 Display: Trajectory Step Cards
    t_cols = st.columns(len(xai_res["trajectory_steps"]))
    for i, t_step in enumerate(xai_res["trajectory_steps"]):
        with t_cols[i]:
            r_pct = t_step["predicted_risk_pct"]
            card_class = "metric-card-red" if r_pct >= 50 else ("metric-card-orange" if r_pct >= 20 else "metric-card-green")
            drivers_html = "".join([f"<div style='font-size: 12px; color: #111111; margin-bottom: 2px;'>• {d}</div>" for d in t_step["main_drivers"]])
            step_card_html = f"""
            <div class="metric-card {card_class}">
                <div style="font-weight: 700; font-size: 13px;">Step {t_step['step']} (+{t_step['minutes_ahead']}m)</div>
                <div style="font-size: 24px; font-weight: 800; margin: 4px 0;">{r_pct:.1f}%</div>
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 8px;">{t_step['predicted_stage_name'].split('(')[0].strip()}</div>
                <div style="font-size: 11px; font-weight: 700; color: #495057; text-transform: uppercase; margin-bottom: 4px;">Main Drivers:</div>
                {drivers_html}
            </div>
            """
            safe_html(step_card_html)


# ==========================================================
# PAGE 5: CSV INGESTION & STATE CONSTRUCTION
# ==========================================================
elif "CSV Ingestion" in selected_page:
    st.markdown("## **Network Traffic CSV Ingestion & Live State Construction**")
    st.markdown(
        "<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        "Upload raw NetFlow/CIC-IDS2017 compatible network CSVs to reconstruct chronological discrete states and initialize forecasting."
        "</p>",
        unsafe_allow_html=True
    )

    # 1. Professional Pre-Upload Interface
    st.markdown("### **1. Ingestion Pipeline & Supported Formats**")
    col_info1, col_info2 = st.columns([1, 1])

    with col_info1:
        st.markdown("""
        **Supported Data Specifications:**
        - Standard **CIC-IDS2017 / CIC-IDS2018** network flow CSV exports
        - NetFlow / IPFIX flow records with standard flow duration, ports, packet rates, and TCP flags
        - Pre-computed 1-minute macro-behavioural state vector CSVs or raw packet flow sequences
        - Automatic header sanitization and whitespace cleaning
        """)

    with col_info2:
        st.markdown("""
        **Ingestion & State Construction Pipeline:**
        ```text
        CSV Upload
            ↓
        Parse Traffic & Timestamps
            ↓
        Clean Numeric Records & Flags
            ↓
        Aggregate 1-Minute Discrete Windows
            ↓
        Generate 25D State Vectors S(t)
            ↓
        Initialize Autoregressive Forecasting
        ```
        """)

    st.markdown("---")
    st.markdown("### **2. Ingestion Trigger**")

    c_up1, c_up2 = st.columns([2, 1])
    with c_up1:
        uploaded_file = st.file_uploader(
            "Upload Network Traffic CSV",
            type=["csv"],
            help="Select any CIC-IDS compatible traffic CSV to dynamically parse and forecast"
        )

    with c_up2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Load Tuesday Baseline Dataset (445k Flows)", use_container_width=True):
            st.session_state.df_states = load_default_sample_states()
            st.session_state.dataset_name = "Tuesday-WorkingHours.pcap_ISCX.csv (445,641 flows)"
            st.session_state.current_idx = 65
            st.session_state.is_playing = False
            st.success("Loaded Tuesday Baseline Dataset!")
            st.rerun()

    if uploaded_file is not None:
        st.markdown("---")
        st.markdown("### **3. Live Ingestion Progress (8-Stage Tracker)**")

        progress_container = st.empty()
        stage_statuses = ["Pending"] * 8

        def update_stage(idx, status):
            stage_statuses[idx] = status
            with progress_container:
                render_processing_pipeline(stage_statuses)

        update_stage(0, "Processing")
        file_bytes = uploaded_file.getvalue()

        # Run multi-stage processing
        new_states_df, raw_row_count = process_dynamic_csv_with_stages(
            file_bytes=file_bytes,
            file_name=uploaded_file.name,
            progress_callback=update_stage
        )

        st.success(f"Processing Complete! Successfully constructed {len(new_states_df)} states from {raw_row_count:,} flows.")

        # Persist in OperationLogger
        op_id = operation_logger.record_operation(
            file_name=uploaded_file.name,
            states_df=new_states_df,
            num_raw_rows=raw_row_count,
            k_horizon=st.session_state.k_horizon,
            interval_sec=st.session_state.interval_sec
        )

        st.info(f"Operation successfully logged to persistent history as: `{op_id}`")

        st.markdown("### **4. Constructed Network States Preview**")
        st.dataframe(new_states_df.head(10), use_container_width=True)

        if st.button("Activate This Dataset in Executive SOC Console", type="primary", use_container_width=True):
            st.session_state.df_states = new_states_df
            st.session_state.dataset_name = f"{uploaded_file.name} ({raw_row_count:,} flows)"
            st.session_state.current_idx = 1
            st.session_state.is_playing = False
            st.rerun()


# ==========================================================
# PAGE 6: OPERATION HISTORY & HISTORICAL STATE EXPLORER
# ==========================================================
elif "History" in selected_page:
    st.markdown("## **Operation History & Historical State Explorer**")
    st.markdown(
        "<p style='color: #495057; font-size: 14px; margin-top: -8px;'>"
        "Inspect all previously ingested CSV processing operations, review full state logs, and explore chronological network evolution."
        "</p>",
        unsafe_allow_html=True
    )

    operations = operation_logger.list_operations()

    if not operations:
        st.info("No recorded operations found. Please upload a dataset or initialize baseline.")
    else:
        # 1. Operations Table
        st.markdown("### **1. Ingested Operations Log**")

        op_table = []
        for op in operations:
            op_table.append({
                "Operation ID": op.get("operation_id"),
                "File Name": op.get("file_name"),
                "Upload Timestamp": op.get("upload_time", "")[:19].replace("T", " "),
                "Raw Flows": f"{op.get('num_rows', 0):,}",
                "States Created": op.get("num_states", 0),
                "Peak Risk": f"{op.get('peak_risk_pct', 0.0):.1f}%",
                "Threat Level": op.get("risk_category", "Low"),
                "Status": op.get("processing_status", "Completed")
            })

        st.dataframe(pd.DataFrame(op_table), use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### **2. Historical State Explorer**")

        op_options = [op.get("operation_id") for op in operations]
        selected_op_id = st.selectbox("Select Operation to Inspect", op_options, index=0)

        if selected_op_id:
            op_meta, op_states = operation_logger.load_operation(selected_op_id)

            safe_html(
                f"""
                <div style="background: #F8F9FA; border: 1px solid #DEE2E6; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px;">
                    <div style="font-size: 15px; font-weight: 700; color: #111111;">Operation: {op_meta.get('file_name')}</div>
                    <div style="font-size: 13px; color: #495057; margin-top: 4px;">{op_meta.get('summary')}</div>
                    <div style="font-size: 12px; color: #6C757D; margin-top: 6px;">
                        Processed: <strong>{op_meta.get('num_rows', 0):,} rows</strong> | Generated: <strong>{op_meta.get('num_states', 0)} states</strong> | Peak Risk: <strong>{op_meta.get('peak_risk_pct', 0.0)}% ({op_meta.get('risk_category')})</strong>
                    </div>
                </div>
                """
            )

            col_btn1, col_btn2 = st.columns([2, 1])
            with col_btn2:
                if st.button("Set As Active Dataset in SOC Console", type="primary", use_container_width=True):
                    st.session_state.df_states = op_states
                    st.session_state.dataset_name = f"{op_meta.get('file_name')} (Historical Log)"
                    st.session_state.current_idx = 1
                    st.session_state.is_playing = False
                    st.success(f"Loaded {op_meta.get('file_name')} into SOC Console!")
                    st.rerun()

            # State Scrubber for Historical Operation
            op_total = len(op_states)
            hist_state_num = st.slider(
                "Select State S(t) to Inspect",
                min_value=1,
                max_value=op_total,
                value=1,
                step=1,
                format="State #%d"
            )

            target_row = op_states.iloc[hist_state_num - 1]
            s_id = target_row.get("state_id", f"S{hist_state_num:03d}")
            t_str = str(target_row.get("timestamp", ""))
            r_pct = float(target_row.get("risk_pct", target_row.get("risk_score", 0.0) * 100.0))

            hc1, hc2, hc3, hc4 = st.columns(4)
            with hc1:
                render_semantic_card(f"STATE {s_id}", f"{r_pct:.1f}%", f"Observed at {t_str}", risk_score=r_pct / 100.0)
            with hc2:
                render_semantic_card("FLOWS", f"{int(target_row.get('flow_count', 0)):,}", "1-minute aggregation")
            with hc3:
                render_semantic_card("PORTS", f"{int(target_row.get('unique_dst_ports', 0))}", "Unique destination ports")
            with hc4:
                render_semantic_card("PACKET RATE", f"{float(target_row.get('packet_rate', 0.0)):.1f}", "Packets / sec")

            st.markdown("#### **State Vector Values**")
            cols_to_show = [c for c in STATE_FEATURE_COLS if c in target_row.index]
            state_val_df = pd.DataFrame({
                "Feature": [FEATURE_DISPLAY_NAMES.get(c, c) for c in cols_to_show],
                "Raw Value": [f"{target_row[c]:,.2f}" if abs(target_row[c]) >= 1 else f"{target_row[c]:.4f}" for c in cols_to_show]
            })
            st.dataframe(state_val_df, use_container_width=True, hide_index=True)


# ==========================================================
# SEQUENTIAL PLAYBACK AUTO-ADVANCE LOOP
# ==========================================================
if st.session_state.is_playing:
    if current_idx < total_states:
        time.sleep(float(st.session_state.interval_sec))
        st.session_state.current_idx = current_idx + 1
        st.rerun()
    else:
        st.session_state.is_playing = False
        st.info("Simulation reached the final state of the sequence.")
