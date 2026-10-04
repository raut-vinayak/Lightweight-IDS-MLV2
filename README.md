# Lightweight IoT Intrusion Detection System (IDS)

A resource-constrained, machine-learning-powered Intrusion Detection System benchmarked on the **CICIoT2023** dataset. Designed specifically for low-power edge nodes and embedded IoT gateways by exploring the Pareto trade-offs between **detection accuracy (Macro F1)**, **model memory footprint (KB)**, and **real-time inference latency (ms)**.

---

## 📌 Project Overview

Traditional Network Intrusion Detection Systems (NIDS) are often too computationally heavy to run locally on low-cost IoT edge hardware. This project addresses that challenge by:
1. **Feature Pruning**: Extracting compact, nested feature subsets ($K \in [5, 10, 15, 20]$) using **Mutual Information** and **Correlation Redundancy Removal** from the 46 raw CICIoT2023 flow features.
2. **Resource-Constrained Architectures**: Benchmarking 4 lightweight models:
   - `DecisionTree` (Ultra-low latency, tiny footprint)
   - `LogisticRegression` (Linear boundary, minimal memory)
   - `ConstrainedLightGBM` (Shallow boosted trees)
   - `SmallRandomForest` (Compact ensemble)
3. **Dual Task Formulation**:
   - **Binary Task**: Benign Traffic (0) vs. Attack Traffic (1).
   - **Multiclass Task**: Benign + 7 Attack Classes (DDoS, DoS, Recon, Web-based, Brute Force, Spoofing, Mirai) using official CICIoT2023 mappings.
4. **Live Network Sniffing**: Real-time 5-tuple flow aggregation over sliding time windows via Scapy with sub-millisecond inference and structured JSONL logging.
5. **Interactive Streamlit Dashboard**: Clean evaluation GUI for inspection, visual Pareto plots, and live single-sample or batch prediction.

---

## 📂 Repository Structure

```text
CP/
├── data/
│   ├── raw/                 # Raw CICIoT2023 CSV files (or auto-generated sample)
│   └── processed/           # Scaled & clean training splits
├── models/                  # Serialized .joblib model artifacts & metadata
├── results/
│   ├── plots/               # Evaluation charts (Macro F1, Size, Latency, CM)
│   ├── scorecard_binary.csv # Binary benchmark results
│   ├── scorecard_multiclass.csv # Multiclass benchmark results
│   ├── scorecard.csv        # Master combined scorecard
│   └── live_predictions.jsonl # Real-time IDS streaming logs
├── src/
│   ├── __init__.py          # Package initializer
│   ├── config.py            # Central configuration & category mappings
│   ├── data_loader.py       # Dataset discovery, loading & inspection
│   ├── preprocess.py        # Cleaning, leakage prevention & stratified split
│   ├── feature_selection.py # Mutual Information ranking & correlation pruning
│   ├── models.py            # Lightweight model definitions
│   ├── evaluate.py          # Metrics, latency benchmark & model serialization
│   ├── plots.py             # Matplotlib/Seaborn visualization generator
│   └── live_capture.py      # Real-time packet sniffer & flow inference
├── main.py                  # End-to-end pipeline runner
├── dashboard.py             # Streamlit web dashboard
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation & report guide
```

---

## 🚀 Setup & Installation

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14.2)
- Windows / Linux / macOS

### 2. Environment Setup
```bash
# Clone or navigate to the project directory
cd "d:/MACHINE LEARNING/CP"

# Create a virtual environment
python -m venv ml_env

# Activate virtual environment
# On Windows PowerShell:
.\ml_env\Scripts\Activate.ps1
# On Linux/macOS:
source ml_env/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

---

## 🔄 How to Reproduce Results (Step-by-Step)

### Step 1: Verify Dataset & Label Mapping (Phase 1)
Inspect the dataset in `data/raw/` and view all unique attack labels:
```bash
python -m src.data_loader
```
*(If no CSV files are placed in `data/raw/`, the loader automatically generates a clean, synthetic CICIoT2023 sample dataset with all 46 features to allow immediate end-to-end validation.)*

### Step 2: Validate Preprocessing & Stratified Splitting (Phase 2)
Verify cleaning, removal of leakage columns, and stratified train/test proportions:
```bash
python -m src.preprocess
```

### Step 3: Verify Nested Feature Selection (Phase 3)
Inspect the Mutual Information ranking, correlation pruning, and nested subsets for $K \in [5, 10, 15, 20]$:
```bash
python -m src.feature_selection
```

### Step 4: Run Full Model Training & Scorecard Benchmark (Phase 4)
Run both Binary and Multiclass tasks across all 4 models and 4 K-values:
```bash
# Run binary task:
python main.py --task binary --sample_frac 0.50

# Run multiclass task:
python main.py --task multiclass --sample_frac 0.50

# Or run both at once:
python main.py --task both --sample_frac 0.50
```
This saves all trained models into `models/` and scorecard CSVs into `results/`.

### Step 5: Generate Trade-off Plots (Phase 5)
Generate all 4 research trade-off charts from the scorecard CSVs:
```bash
python -m src.plots
```
Saved to `results/plots/`:
- `macro_f1_vs_k.png`: Macro F1 vs. Number of Features (Pareto curve)
- `model_size_vs_k.png`: Model Disk Footprint (KB) on Log Scale
- `latency_vs_k.png`: Inference Latency per Sample (ms)
- `confusion_matrix_k10_multiclass.png`: Heatmap for best K=10 Multiclass model

---

## 🖥️ Running the Dual-Portal Interactive System

The system provides **two distinct, standalone web portals** that communicate in real time over a live traffic bridge:

### 1. Attacker Portal (Port 8502) — The Hacker Cockpit
Launch command:
```bash
streamlit run attacker_portal.py --server.port 8502
```
👉 **URL:** [http://localhost:8502](http://localhost:8502)
- Select target IoT network (Smart Hospital, Home, Factory, CCTV, etc.) and victim device IP.
- Select attack vector (DDoS SYN Flood, Mirai Botnet, Nmap Port Scan, Brute Force, Spoofing, or Normal Benign).
- Tune attack-specific parameters (Packet rate, payload size, protocol flags).
- Click **"🚀 TRANSMIT TRAFFIC TO IOT GATEWAY"** to inject malicious/benign packets over the network bridge.

### 2. Main Defender SOC & Gateway IDS (Port 8501) — The Protector
Launch command:
```bash
streamlit run dashboard.py --server.port 8501
```
👉 **URL:** [http://localhost:8501](http://localhost:8501)
- Intercepts incoming packets transmitted from the Attacker Portal in real time.
- Feeds features into our pre-validated **Autonomous Optimal Lightweight ML Model (Decision Tree K=10, 6.1 KB)**.
- Computes detection in microseconds (`0.010 ms`), displays confidence %, and flags the victim node.
- Executes automated edge firewall mitigation (`iptables -A FORWARD -s <attacker_ip> -j DROP`).
- Real-time event log and complete academic research Pareto evidence tabs.

> **💡 Best Demo Experience:** Open both URLs side-by-side in your browser (Split Screen). Launch an attack on the left (Port 8502) and watch the Defender SOC on the right (Port 8501) intercept and block it instantly!

---

## 🌐 Running Live Detection in a VM Lab (Phase 7)

For deployment in a 3-VM testbed (**Attacker VM**, **Victim VM**, **IDS VM** with promiscuous mode network interface):

### On the IDS VM:
Run live packet sniffing and real-time inference:
```bash
# Run on specified interface (e.g. eth0) with 2.0-second flow aggregation:
python -m src.live_capture --interface eth0 --window 2.0 --model_path models/model_binary_DecisionTree_k10.joblib
```

### Testing without physical VM capture (Simulation Mode):
```bash
python -m src.live_capture --simulate
```
Real-time alerts will stream to the console and append to `results/live_predictions.jsonl`:
```text
[2026-09-30 22:28:12.450] [ALERT] | 192.168.1.100:49152 -> 192.168.1.50:80 (TCP) | Pred: ATTACK [1] | Conf: 72.0% | Latency: 2.000 ms
```

---

## 📊 Summary for Project Report / Presentation

| Task | Recommended Model | Best K | Macro F1 | Model Size (KB) | Inference Latency (ms) | Primary Advantage |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Binary IDS** | **Decision Tree** | **10** | **0.9966** | **5.1 KB** | **0.0129 ms** | Ultra-compact memory, sub-0.015ms latency, deterministic decision rules |
| **Binary IDS (High Cap)** | **ConstrainedLightGBM** | **10** | **0.9969** | **70.4 KB** | **0.0293 ms** | High generalization across complex non-linear flow patterns |
| **Multiclass IDS** | **ConstrainedLightGBM** | **10** | **0.8619** | **543.0 KB** | **0.0281 ms** | Strong discrimination across 8 granular cyber attack categories |
| **Multiclass IDS (Low Footprint)** | **Decision Tree** | **10** | **0.8421** | **9.3 KB** | **0.0102 ms** | 58x smaller footprint than boosting with instantaneous inference |

### 🔍 Explainable AI (XAI) Engine:
The Defender SOC dashboard includes an integrated root-cause forensic engine that highlights the exact triggering rules (e.g. `Rate > 120 pkts/s`, `syn_count > 3`), decision path, and observed feature deviations against safe IoT baselines.

### ⚙️ Pure C-Code Export for IoT Hardware:
The optimal $K=10$ Decision Tree is exported to standalone, zero-dependency C code in [`models/ids_rules.c`](file:///d:/MACHINE%20LEARNING/CP/models/ids_rules.c) and [`models/ids_rules.h`](file:///d:/MACHINE%20LEARNING/CP/models/ids_rules.h) (`predict_ids(features)`), enabling deployment directly on microcontrollers (ESP32, STM32, Arduino) without Python or external libraries.
