"""
Configuration Module for Lightweight IoT Intrusion Detection System (IDS).

Defines paths, hyperparameters, category mappings for CICIoT2023,
and model selection settings. Acts as the single source of truth.
"""

from pathlib import Path

# ==============================================================================
# 1. Project Directory Paths
# ==============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
MODELS_DIR = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
PLOTS_DIR = RESULTS_DIR / "plots"

# Result scorecard file paths
SCORECARD_CSV = RESULTS_DIR / "scorecard.csv"
SCORECARD_BINARY_CSV = RESULTS_DIR / "scorecard_binary.csv"
SCORECARD_MULTICLASS_CSV = RESULTS_DIR / "scorecard_multiclass.csv"
LIVE_PREDICTIONS_JSONL = RESULTS_DIR / "live_predictions.jsonl"

# Ensure all primary directories exist
for directory in [DATA_RAW_DIR, DATA_PROCESSED_DIR, MODELS_DIR, RESULTS_DIR, PLOTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# 2. General Data & Pipeline Settings
# ==============================================================================
RANDOM_STATE = 42
TEST_SIZE = 0.20
DEV_SAMPLE_FRACTION = 0.05  # Fraction of raw data loaded for development/fast runs
LABEL_COLUMN = "label"

# Feature selection sizes to benchmark (compact feature spaces for IoT devices)
K_VALUES = [5, 10, 15, 20]

# Correlation threshold for removing redundant features in feature selection
CORRELATION_THRESHOLD = 0.85

# Columns known to cause data leakage or identifier bias
LEAKAGE_COLUMNS = [
    "Timestamp", "Flow_ID", "Src_IP", "Dst_IP", "Source IP",
    "Destination IP", "Src_Port", "Dst_Port", "SimillarHTTP",
    "Unnamed: 0", "id"
]

# ==============================================================================
# 3. CICIoT2023 Category Mapping (Official 33 Attacks -> 7 Categories + Benign)
# ==============================================================================
CATEGORY_MAP = {
    # Benign class
    "BenignTraffic": "Benign",

    # DDoS Attacks
    "DDoS-RSTFINFlood": "DDoS",
    "DDoS-PSHACK_Flood": "DDoS",
    "DDoS-SYN_Flood": "DDoS",
    "DDoS-UDP_Flood": "DDoS",
    "DDoS-TCP_Flood": "DDoS",
    "DDoS-ICMP_Flood": "DDoS",
    "DDoS-SynonymousIP_Flood": "DDoS",
    "DDoS-ACK_Fragmentation": "DDoS",
    "DDoS-UDP_Fragmentation": "DDoS",
    "DDoS-ICMP_Fragmentation": "DDoS",
    "DDoS-SlowLoris": "DDoS",
    "DDoS-HTTP_Flood": "DDoS",

    # DoS Attacks
    "DoS-UDP_Flood": "DoS",
    "DoS-TCP_Flood": "DoS",
    "DoS-SYN_Flood": "DoS",
    "DoS-HTTP_Flood": "DoS",

    # Reconnaissance / Scans
    "Recon-PingSweep": "Recon",
    "Recon-OSScan": "Recon",
    "Recon-PortScan": "Recon",
    "VulnerabilityScan": "Recon",
    "Recon-HostDiscovery": "Recon",

    # Web-based Attacks
    "SqlInjection": "Web-based",
    "CommandInjection": "Web-based",
    "XSS": "Web-based",
    "Backdoor_Malware": "Web-based",
    "BrowserHijacking": "Web-based",
    "Uploading_Attack": "Web-based",

    # Brute Force Attacks
    "DictionaryBruteForce": "Brute Force",

    # Spoofing Attacks
    "MITM-ArpSpoofing": "Spoofing",
    "DNS_Spoofing": "Spoofing",

    # Mirai Botnet Attacks
    "Mirai-greeth_flood": "Mirai",
    "Mirai-udpplain": "Mirai",
    "Mirai-greip_flood": "Mirai",
}

# Ordered class names for multiclass classification
ALL_CATEGORIES = [
    "Benign",
    "DDoS",
    "DoS",
    "Recon",
    "Web-based",
    "Brute Force",
    "Spoofing",
    "Mirai"
]
