# Attack Forecast System — Master Implementation Plan

This implementation plan aligns the **Network Attack Forecast System** with all requirements specified in [master_prompt.md](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/master_prompt.md).

The updated system transforms the dashboard from a static single-snapshot viewer into a **sequential, live-updating cyber defense platform** that chronologically simulates network state evolution $S(t) \to S(t+1)$, projects $K$-step future trajectories, attributes risk escalation via horizontal Explainable AI (XAI), maps tactical MITRE progression timelines, and logs every operation and generated state into a persistent historical explorer.

---

## User Review Required

> [!IMPORTANT]
> **Sequential Simulation Experience**:
> In Streamlit, sequential simulation will be driven by an interactive **Playback Controller** (▶ Play, ⏸ Pause, ⏭ Step Forward, ⏮ Step Backward, ⏮⏮ Reset, and Update Interval slider: 0.5s - 5.0s). When playing, the system automatically advances network time step-by-step, re-evaluating the $K$-step forecast autoregressively at each step and dynamically updating all charts, metrics, MITRE stages, and XAI explanations.

> [!NOTE]
> **Storage & History**:
> We will introduce a persistent operation logger in `src/storage/operation_logger.py` saving metadata and full state records into `data/operations/`. The Tuesday baseline dataset will be automatically initialized as the first historical operation so the **Operation History & State Explorer** is immediately fully functional even before any new file is uploaded.

---

## Proposed Changes

### Storage & Persistence Layer

#### [NEW] [`src/storage/operation_logger.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/src/storage/operation_logger.py)
- Defines `OperationLogger` to record every CSV upload operation and its generated network states.
- Stores:
  - **Operation Metadata**: Upload ID, File Name, Upload Timestamp, Processing Start/End Times, Total Rows, State Count, Processing Status ("Completed"), Peak Risk Score, Forecast Configuration ($K$ horizon, update interval), and Executive Summary.
  - **State History**: Full state table containing State ID (`S001`, `S002`, ...), Timestamp, State Vector values (25 features), Key Attributes (flows, ports, packet rate, bytes/s, SYN count), Risk Score, Predicted Stage, Top Features, and Forecasted Future Trajectory.
- Provides APIs:
  - `record_operation(...)`
  - `list_operations() -> List[Dict]`
  - `load_operation(operation_id) -> Tuple[Dict, pd.DataFrame]`
  - `ensure_baseline_operation(baseline_states_df)` to ensure default history is always available.

---

### Explainability & MITRE Layer

#### [MODIFY] [`src/explainability/attributor.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/src/explainability/attributor.py)
- Add trajectory attribution support:
  - `attribute_trajectory(...)`: Computes top contributing features and risk drivers for each step across the $K$-step forecast window ($t+1, t+2, \dots, t+K$).
  - Distinguishes feature impact directions:
    - **Risk Escalation (+)**: Features increasing future attack risk.
    - **Risk Mitigation (-)**: Features suppressing or normalizing risk.
    - **Neutral**: Low-impact / steady-state baseline features.
- Formats drivers clearly for executive security analysts:
  - e.g., $t+1$: Risk 32%, Main drivers: Port Diversity, SYN Activity.

#### [MODIFY] [`src/mitre/mapper.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/src/mitre/mapper.py)
- Implement `map_trajectory_progression(current_state_info, forecast_timeline)`:
  - Builds a comprehensive tactical progression timeline connecting **Observed Behaviour at State $S(t)$** to **Predicted Future Stages at $\hat{S}(t+1) \dots \hat{S}(t+K)$**.
  - For each stage, maps:
    - Tactical stage name and ID (e.g. TA0043 Reconnaissance, TA0006 Credential Access, TA0040 Impact/DoS)
    - Prediction confidence rating ("HIGH", "MEDIUM", "LOW")
    - Observed vs. Predicted network behavioral indicators (port diversity, flow velocity, SYN spikes)
    - Relevant MITRE ATT&CK technique code (e.g. T1046, T1110.001, T1498) and name
    - Concrete SOC countermeasures and mitigation steps.

---

### UI & Styling System

#### [MODIFY] [`dashboard/theme.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/dashboard/theme.py)
- Refine SOC Executive Light Design System:
  - Primary: Pure White (`#FFFFFF`), Text: Dark Grey / Black (`#111111`, `#212529`), Borders: Slate Grey (`#DEE2E6`, `#E9ECEF`).
  - Semantic Risk Colors:
    - Normal / Low Risk: Green (`#2B8A3E`, bg `#E6FCF5`, border `#63E6BE`)
    - Medium Risk: Amber / Orange (`#D9480F`, bg `#FFF9DB`, border `#FFE066`)
    - High Risk: Crimson Red (`#C92A2A`, bg `#FFF5F5`, border `#FFA8A8`)
- Horizontal Feature Attribution Chart:
  - Implement `render_horizontal_attribution_chart(attributions)` using Plotly:
    - **HORIZONTAL bars** (as strictly mandated by Section 7).
    - Color-coded by direction (Red for Risk Escalation, Green for Risk Mitigation, Slate for Neutral).
- Sequential Risk Trajectory Chart:
  - Implement `render_sequential_trajectory_chart(observed_history, forecast_timeline, current_step_idx)`:
    - Solid dark line: Observed historical risk leading up to state $S(t)$.
    - Distinct glowing marker on active state $S(t)$.
    - Dashed projected line: $K$-step future forecast $\hat{S}(t+1) \dots \hat{S}(t+K)$.
    - Shaded background risk zones: Normal (<20%), Medium (20-50%), High (>=50%).
- MITRE Progression Timeline Component:
  - Implement `render_mitre_progression_timeline(progression_items)`:
    - Visual chronological chain showing Observed State $\to$ Predicted Stages.
    - Badges for Confidence, Tactic, and Technique.

---

### Dashboard Application

#### [MODIFY] [`dashboard/app.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/dashboard/app.py)
Structure the platform into 6 dedicated modules fulfilling all prompt specifications:

1. **Executive SOC Dashboard (Section 1 & 12)**:
   - Live Sequential Simulation Controller: Play (▶), Pause (⏸), Step Forward (⏭), Step Backward (⏮), Reset (⏮⏮), Update Interval Slider (0.5s - 5.0s), and Horizon $K$ slider (1 - 10).
   - Real-time KPI Cards: Current Attack Risk, Forecasted Risk ($t+1$) with trend indicator, Predicted Attack Stage, Actionable Prediction Lead Time.
   - Dynamic Semantic Early Warning Banner.
   - Sequential Risk Trajectory Curve showing past observed + forecasted future.
   - Dual Panel: Active Network State Telemetry (Flows, Ports, Packet Rate, Bandwidth, TCP Flags) vs. Projected Future Trajectory ($t+1 \dots t+K$).
   - Live State Pipeline Tracker: Horizontal status stream (`S001 ✓`, `S002 ✓`, `👉 S003 [ACTIVE]`, `S004 [t+1]`, ...).

2. **Sequential Simulation & Telemetry (Section 1, 4, 5)**:
   - Full 25-dimensional macro-behavioural state vector inspection of active state $S(t)$.
   - 30-minute historical telemetry trends (flow count, port diversity, packet rate, SYN activity).
   - Interactive state scrubber allowing direct inspection of any moment along the timeline.

3. **MITRE ATT&CK Tactical Progression (Section 6)**:
   - Eliminates empty divisions; fully generated from system predictions.
   - Chronological tactical progression timeline (Current $\to$ Reconnaissance $\to$ Credential Access / Impact).
   - Deep-dive cards for each tactical step: Confidence, Behavioral Signatures, MITRE Technique Details, and SOC Mitigation Playbooks.

4. **Explainable AI / XAI Page (Section 7 & 8)**:
   - Complete explainability interface answering *"Why is the system predicting increasing future attack risk?"*
   - Horizontal feature attribution ranking with semantic colors.
   - Step-by-step future trajectory explainability ($t+1, t+2, \dots, t+K$) displaying predicted risk and main driver features.
   - Executive analyst narrative.

5. **CSV Ingestion & State Construction (Section 2 & 3)**:
   - Professional pre-upload guidance: Supported formats (CIC-IDS2017/2018), expected schema, and visual processing pipeline diagram.
   - File upload area with 1-click sample dataset loader.
   - Live 8-stage progress tracker with real processing metrics:
     1. CSV Validation
     2. Timestamp Parsing
     3. Data Cleaning
     4. Feature Extraction
     5. Time-Window Aggregation
     6. Network State Construction
     7. State Vector Generation
     8. Sequential Forecast Initialization
   - Live state construction preview table showing generated states ($S001, S002, \dots$).

6. **Operation History & State Explorer (Section 9, 10, 11)**:
   - Operations log table listing all processed CSV runs (File name, Upload timestamp, Total rows, State count, Peak risk, Status, Load button).
   - Historical State Explorer: Select any past operation and step through its states, viewing state vectors, risk scores, attack stages, top contributing features, and associated forecasts.

---

## Verification Plan

### Automated Tests
- Create unit tests in [`tests/test_operation_logger.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/tests/test_operation_logger.py) to test:
  - Recording, listing, and retrieving operations and state history.
  - Data integrity of saved state vectors and metadata.
- Create unit tests in [`tests/test_trajectory_xai_and_mitre.py`](file:///c:/Users/saran/OneDrive/Desktop/Network-Attack-Forecast-System/tests/test_trajectory_xai_and_mitre.py) to test:
  - Trajectory attribution across $K$ steps with horizontal formatting.
  - MITRE progression timeline mapping for current and future states.
- Run all existing and new unit tests via Python test runner:
  ```powershell
  python -c "import tests.test_operation_logger, tests.test_trajectory_xai_and_mitre, tests.test_model_and_rollout; print('All tests passed!')"
  ```

### Manual / Browser Verification
- Start the Streamlit application:
  ```powershell
  python -m streamlit run dashboard/app.py --server.port 8501 --server.headless true
  ```
- Launch browser subagent or verify:
  1. Main SOC Dashboard loads cleanly with white executive light theme, no blank divisions, no overlapping text.
  2. Sequential simulation playback controller: Click Play (▶) and verify that network states advance sequentially ($S001 \to S002 \to \dots$), updating all metrics, charts, and forecasts dynamically.
  3. MITRE page renders full tactical progression timeline with confidence and mitigations.
  4. XAI page renders **horizontal** feature attribution bars with semantic risk colors, plus step-by-step future trajectory drivers.
  5. CSV Ingestion page shows professional pre-upload state and 8-stage live progress tracker.
  6. Operation History & State Explorer displays historical runs and enables state inspection.
