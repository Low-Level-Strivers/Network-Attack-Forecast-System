<div align="center">

# 🛡️ Network Attack Forecast System

### AI-Powered Network Attack Forecast · World Model

*Learn Network Behaviour → Forecast Future States → Explain Risk → Enable Early Defence*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1%2B-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-SOC%20Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-8%20Suites-6366F1)](tests/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE%20ATT%26CK-Mapped-E11D48)](https://attack.mitre.org)

</div>

---

## 📖 Overview

![Network-Attack-Forecasting](/assets/Attack-Forecasting-2.png)
**Conventional Intrusion Detection Systems (IDS)** are fundamentally **reactive** — they classify individual packets or flows *after* an attack has already begun. By the time an alert fires, damage is often done.

This project introduces a **Temporal Network World Model** — an AI system that *learns* how networks behave over time and *predicts* future attack states minutes before they materialise, giving Security Operations Center (SOC) analysts actionable lead time to respond.

### Core Innovation Pipeline

| Step | Component | What It Does |
|------|-----------|--------------|
| 1️⃣ | **Network State Builder** | Aggregates raw flows into 1-minute discrete state vectors *S(t)* |
| 2️⃣ | **LSTM World Model** | Learns internal network dynamics *P(S_{t+1} \| S_{≤t})* |
| 3️⃣ | **K-Step Rollout Engine** | Autoregressively simulates *S(t+1)…S(t+K)* future states |
| 4️⃣ | **Multi-Task Heads** | Predicts attack probability, stage, and MITRE tactic simultaneously |
| 5️⃣ | **XAI Attribution** | Explains *why* risk is escalating using Integrated Gradients |
| 6️⃣ | **SOC Dashboard** | Presents predictions with actionable lead time to analysts |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        NETWORK DATA                             │
│              CIC-IDS2017 / PCAP / Live CSV Upload               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PREPROCESSING PIPELINE                      │
│   NaN/Inf Sanitization → Timestamp Parsing → Feature Selection  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                 1-MINUTE NETWORK STATE BUILDER                   │
│           25 Behavioural Features → State Vector S(t)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              TEMPORAL SEQUENCE GENERATOR (L=30)                 │
│              S(t-29) … S(t-1) … S(t)  →  [30 × 25]             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LSTM WORLD MODEL (PyTorch)                    │
│  LSTM Encoder → Latent z(t) → 3 Multi-Task Prediction Heads    │
│                                                                 │
│   ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │  Next-State    │  │ Risk Score   │  │  Attack Stage    │  │
│   │  Head (MSE)    │  │ Head (BCE)   │  │  Head (CE Loss)  │  │
│   └────────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               K-STEP AUTOREGRESSIVE ROLLOUT                     │
│          Simulates: Ŝ(t+1), Ŝ(t+2), … Ŝ(t+K)                 │
│          Risk Trajectory + Prediction Lead Time                 │
└──────────┬────────────────────────────┬────────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────┐         ┌──────────────────────────────────┐
│  MITRE ATT&CK    │         │     XAI ATTRIBUTION              │
│  Tactic Mapping  │         │  Integrated Gradients (Captum)   │
│  + Mitigations   │         │  25-Feature Risk Attribution     │
└──────────┬───────┘         └──────────┬───────────────────────┘
           │                            │
           └────────────┬───────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│               SOC DASHBOARD (Streamlit)                         │
│  Real-Time Forecasts · MITRE Timeline · XAI Charts · Logs      │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 🔮 Predictive Forecasting
- **K-Step Autoregressive Rollout** — simulates up to K future network states without requiring ground truth data
- **Prediction Lead Time** — quantifies how many minutes in advance the model detects an incoming threat
- **Risk Trajectory Visualization** — plots risk escalation curves across the forecast horizon

### 🧠 LSTM World Model
- **Multi-Task Architecture** — one encoder, three concurrent prediction heads (state, risk, stage)
- **Latent Dynamics Representation** *z(t)* — compressed encoding of current network behavioural state
- **Configurable Hyperparameters** — hidden dim, layers, dropout, learning rate all in `config.yaml`

### 🎯 MITRE ATT&CK Integration
Automatically maps predicted attack stages to official MITRE ATT&CK tactics:

| Stage | Tactic ID | Tactic Name | Example Technique |
|-------|-----------|-------------|-------------------|
| 0 | — | Normal Baseline | Normal Operations |
| 1 | TA0043 / TA0007 | Reconnaissance / Discovery | T1046 – Network Service Scanning |
| 2 | TA0006 | Credential Access | T1110.001 – Brute Force |
| 3 | TA0040 | Impact | T1498 – Network DoS |
| 4 | TA0001 | Initial Access / Exploitation | T1190 – Exploit Public-Facing App |

### 🔍 Explainable AI (XAI)
- **Integrated Gradients** (via Captum) for mathematical attribution of the LSTM's risk predictions
- **25-Dimensional Feature Attribution** — identifies which network behaviours (SYN bursts, port scans, byte rates) are driving predicted risk
- Horizontal attribution charts rendered directly in the SOC Dashboard

### 📊 SOC Dashboard
- Live CSV upload with **stage-by-stage processing pipeline** visualization
- **State stream explorer** — browse all S(t) vectors across the session
- **Historical operation log** — persistent session-level forecasting audit trail
- **MITRE progression timeline** — visual attack kill chain with defensive mitigations

---

## 📁 Project Structure

```
Network-Attack-Forecast-System/
│
├── 📂 config/
│   └── config.yaml                  # Central: windowing, features, model, thresholds
│
├── 📂 data/
│   ├── raw/                         # CIC-IDS2017 CSV / PCAP files (gitignored)
│   ├── processed/                   # Cleaned flow tables (gitignored)
│   └── state_vectors/               # 1-minute S(t) Parquet/CSV (gitignored)
│
├── 📂 dashboard/
│   ├── app.py                       # Streamlit SOC console (930 lines)
│   └── theme.py                     # UI components, charts, semantic cards
│
├── 📂 models/                       # Trained checkpoints (gitignored)
│   └── lstm_world_model_best.pt     # Best model weights (after training)
│
├── 📂 notebooks/                    # EDA and exploratory analysis
│
├── 📂 src/
│   ├── ingestion/
│   │   └── loader.py                # CIC-IDS2017 dataset loader & schema validator
│   │
│   ├── preprocessing/
│   │   ├── cleaner.py               # NaN/Inf sanitization
│   │   └── timestamp_parser.py      # Timestamp parsing & temporal sorting
│   │
│   ├── feature_engineering/
│   │   └── scaler.py                # MinMax/StandardScaler wrapper (StateScaler)
│   │
│   ├── state_builder/
│   │   └── aggregator.py            # 1-minute window aggregator → S(t)
│   │
│   ├── sequence_builder/
│   │   └── builder.py               # Sliding lookback sequence generator [L×F]
│   │
│   ├── models/
│   │   ├── world_model.py           # LSTMWorldModel (PyTorch nn.Module)
│   │   └── trainer.py               # Training loop, multi-task loss, checkpointing
│   │
│   ├── forecasting/
│   │   ├── rollout_engine.py        # KStepSimulator – autoregressive rollout
│   │   ├── demo_rollout.py          # Rollout demo script
│   │   └── demo_security_intelligence.py  # Security intelligence demo
│   │
│   ├── mitre/
│   │   └── mapper.py                # MitreMapper – stage → ATT&CK tactic/technique
│   │
│   ├── explainability/
│   │   └── attributor.py            # RiskAttributor – Integrated Gradients (Captum)
│   │
│   ├── evaluation/
│   │   └── metrics.py               # Lead time metrics, MSE/F1 benchmarks
│   │
│   └── storage/
│       └── operation_logger.py      # Session-persistent operation audit logger
│
├── 📂 tests/
│   ├── test_foundation.py           # Core module smoke tests
│   ├── test_preprocessing.py        # Cleaner & timestamp parser tests
│   ├── test_state_and_sequence.py   # State builder & sequence tests
│   ├── test_model_and_rollout.py    # LSTM & K-step rollout tests
│   ├── test_mitre_and_xai.py        # MITRE mapper & attribution tests
│   ├── test_trajectory_xai_and_mitre.py  # Trajectory integration tests
│   ├── test_evaluation.py           # Evaluation metrics tests
│   └── test_operation_logger.py     # Operation logger tests
│
├── run_all_tests.py                 # Master test runner
├── requirements.txt                 # Python dependencies
├── .gitignore                       # Excludes data/, models/, __pycache__
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- Git
- 8 GB RAM recommended (16 GB for full CIC-IDS2017 dataset)
- CUDA-capable GPU optional (CPU inference supported)

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/Network-Attack-Forecast-System.git
cd Network-Attack-Forecast-System
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Prepare Dataset

Download the **CIC-IDS2017** dataset from the [Canadian Institute for Cybersecurity](https://www.unb.ca/cic/datasets/ids-2017.html) and place CSV files in `data/raw/`:

```
data/raw/
├── Monday-WorkingHours.pcap_ISCX.csv
├── Tuesday-WorkingHours.pcap_ISCX.csv
├── Wednesday-WorkingHours.pcap_ISCX.csv
├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
└── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

> **Note:** Data files are gitignored — they must be obtained separately.

### 5. Train the World Model

```bash
# Run training (uses config/config.yaml for hyperparameters)
python -m src.models.trainer
```

Trained checkpoints are saved to `models/lstm_world_model_best.pt` and `models/state_scaler.joblib`.

### 6. Launch the SOC Dashboard

```bash
python -m streamlit run dashboard/app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## ⚙️ Configuration

All system parameters are centrally managed in [`config/config.yaml`](config/config.yaml):

```yaml
sequence:
  lookback_steps: 30        # History window L observed by the LSTM encoder
  forecast_horizon: 5       # K future states to simulate

model:
  hidden_dim: 128           # LSTM hidden state dimension
  latent_dim: 64            # Compressed dynamics representation z(t)
  num_layers: 2             # Stacked LSTM layers
  dropout: 0.2              # Regularization dropout rate
  learning_rate: 0.001
  epochs: 50

thresholds:
  low_risk: 0.25            # Risk score < 0.25 → CLEAN
  medium_risk: 0.50         # Risk score 0.25–0.50 → ELEVATED
  high_risk: 0.75           # Risk score 0.50–0.75 → HIGH
  lead_time_trigger_risk: 0.60  # Threshold that triggers lead time alert
```

### 25 Behavioural State Features

The 1-minute state vector *S(t)* is constructed from these network flow statistics:

| # | Feature | Description |
|---|---------|-------------|
| 1 | `flow_count` | Total network flows per window |
| 2 | `unique_dst_ports` | Destination port diversity (scan indicator) |
| 3 | `unique_src_ports` | Source port diversity |
| 4 | `port_diversity_ratio` | Dst/Src port ratio |
| 5 | `total_fwd_packets` | Forward direction packet volume |
| 6 | `total_bwd_packets` | Backward direction packet volume |
| 7 | `packet_rate` | Packets per second |
| 8 | `total_fwd_bytes` | Forward bytes transferred |
| 9 | `total_bwd_bytes` | Backward bytes transferred |
| 10 | `byte_rate` | Bandwidth utilization (bytes/sec) |
| 11 | `mean_flow_duration` | Average connection duration |
| 12 | `mean_packet_length` | Average payload size |
| 13 | `std_packet_length` | Payload size variance |
| 14 | `mean_flow_iat` | Mean inter-arrival time |
| 15 | `std_flow_iat` | IAT variance (timing irregularity indicator) |
| 16 | `fwd_packet_rate` | Forward packet velocity |
| 17 | `bwd_packet_rate` | Backward packet velocity |
| 18 | `syn_flag_count` | SYN flag activity (connection attempts) |
| 19 | `ack_flag_count` | ACK flag volume |
| 20 | `rst_flag_count` | RST connection aborts |
| 21 | `fin_flag_count` | FIN connection terminations |
| 22 | `psh_flag_count` | PSH data push activity |
| 23 | `down_up_ratio_mean` | Downlink/Uplink traffic asymmetry |
| 24 | `active_mean` | Mean active traffic interval |
| 25 | `idle_mean` | Mean idle wait interval |

---

## 🧪 Testing

Run the complete test suite:

```bash
# All 8 test suites via master runner
python run_all_tests.py

# Individual suite via pytest
pytest tests/test_model_and_rollout.py -v
pytest tests/test_mitre_and_xai.py -v
pytest tests/ -v
```

| Test Suite | Coverage Area |
|------------|---------------|
| `test_foundation.py` | Core module imports & smoke tests |
| `test_preprocessing.py` | Data cleaner & timestamp parser |
| `test_state_and_sequence.py` | State builder & sliding window sequences |
| `test_model_and_rollout.py` | LSTM forward pass & K-step rollout |
| `test_mitre_and_xai.py` | MITRE mapper & XAI attribution |
| `test_trajectory_xai_and_mitre.py` | Full trajectory + attribution pipeline |
| `test_evaluation.py` | Lead time metrics & accuracy benchmarks |
| `test_operation_logger.py` | Session operation logger |

---

## 📦 Dependencies

| Category | Package | Purpose |
|----------|---------|---------|
| **Data** | `polars`, `pandas`, `numpy`, `pyarrow` | High-performance flow data processing |
| **Deep Learning** | `torch` (PyTorch 2.1+) | LSTM world model training & inference |
| **ML** | `scikit-learn`, `joblib` | Scaler, utilities, model persistence |
| **XAI** | `captum`, `shap` | Integrated Gradients, SHAP attribution |
| **Dashboard** | `streamlit` | SOC console & visualization |
| **API** | `fastapi`, `uvicorn`, `pydantic` | REST API serving layer |
| **Config** | `pyyaml`, `tqdm` | Config management, progress bars |
| **Testing** | `pytest` | Automated test suite |

---

## 🗺️ Roadmap

- [x] **Phase 0** — Project Foundation & Repository Governance
- [x] **Phase 1** — Data Ingestion (CIC-IDS2017 Loader)
- [x] **Phase 2** — Cleaning & Timestamp Validation
- [x] **Phase 3** — Behavioural Feature Selection (25 Features)
- [x] **Phase 4** — 1-Minute Network State Builder *S(t)*
- [x] **Phase 5** — State Normalization & Baseline Calibration
- [x] **Phase 6** — Temporal Sequence Generator (*L=30*)
- [x] **Phase 7** — LSTM World Model (Next-State Dynamics)
- [x] **Phase 8** — Multi-Task Heads (Risk & Stage)
- [x] **Phase 9** — K-Step Autoregressive Rollout Engine
- [x] **Phase 10** — MITRE ATT&CK Semantic Mapping
- [x] **Phase 11** — Explainability (XAI via Captum/Integrated Gradients)
- [x] **Phase 12** — Evaluation (Prediction Lead Time & Accuracy)
- [x] **Phase 13** — Security Operations Center (SOC) Dashboard
- [ ] **Phase 14** — End-to-End Pipeline Integration & Demo
- [ ] **Phase 15** — FastAPI REST Inference Endpoint
- [ ] **Phase 16** — PCAP Live Stream Ingestion
- [ ] **Phase 17** — Docker Containerization

---

## 📊 Dataset

This system is designed for the **CIC-IDS2017 Intrusion Detection Evaluation Dataset** published by the Canadian Institute for Cybersecurity.

- **Download:** https://www.unb.ca/cic/datasets/ids-2017.html
- **Attack types covered:** DoS, DDoS, PortScan, FTP/SSH Brute Force, Web Attacks, Botnet, Infiltration
- **Format:** CSV flow records with 80+ features generated by CICFlowMeter

> The dataset is **not included** in this repository due to size constraints (~8 GB). Place downloaded CSVs in `data/raw/` before training.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Commit your changes**: `git commit -m 'feat: add your feature description'`
4. **Push to the branch**: `git push origin feature/your-feature-name`
5. **Open a Pull Request**

### Development Guidelines
- Follow the existing module structure in `src/`
- Add corresponding tests in `tests/` for any new functionality
- Ensure `python run_all_tests.py` passes before submitting a PR
- Keep hyperparameters in `config/config.yaml` — avoid hardcoding values

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgements

- **CIC-IDS2017 Dataset** — Canadian Institute for Cybersecurity, University of New Brunswick
- **MITRE ATT&CK Framework** — MITRE Corporation (https://attack.mitre.org)
- **Captum** — Facebook AI Research (Integrated Gradients implementation)
- **PyTorch** — Meta AI (LSTM world model backbone)

---

<div align="center">

**Built with 🛡️ for proactive attack forecast**

*If this project helps your research or work, please consider giving it a ⭐*

</div>
