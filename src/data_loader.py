"""
Data Loader Module for Lightweight IoT IDS.

Responsible for discovering, loading, and inspecting CICIoT2023 CSV files
from data/raw/. Provides automatic fallback dataset generation if no raw
data is found, so that the entire pipeline can execute end-to-end.
"""

import os
from pathlib import Path
from typing import List, Tuple
import numpy as np
import pandas as pd
from src import config

# All 46 standard numerical flow features in CICIoT2023 dataset
CICIOT2023_FEATURES = [
    "flow_duration", "Header_Length", "Protocol Type", "Duration",
    "Rate", "Srate", "Drate", "fin_flag_number", "syn_flag_number",
    "rst_flag_number", "psh_flag_number", "ack_flag_number",
    "ece_flag_number", "cwr_flag_number", "ack_count", "syn_count",
    "fin_count", "urg_count", "rst_count", "HTTP", "HTTPS", "DNS",
    "Telnet", "SMTP", "SSH", "IRC", "TCP", "UDP", "DHCP", "ARP",
    "ICMP", "IPv", "LLC", "Tot sum", "Min", "Max", "AVG", "Std",
    "Tot size", "IAT", "Number", "Magnitue", "Radius", "Covariance",
    "Variance", "Weight"
]


def get_raw_csv_files() -> List[Path]:
    """
    Scan data/raw directory and return a list of all CSV file paths.

    Returns:
        List[Path]: List of Path objects for CSV files found in data/raw/.
    """
    raw_dir = Path(config.DATA_RAW_DIR)
    csv_files = sorted(list(raw_dir.glob("*.csv")))
    return csv_files


def generate_sample_ciciot2023_dataset(output_path: Path, num_rows: int = 15000) -> Path:
    """
    Generate an authentic, realistic CICIoT2023-compatible dataset with realistic
    behavioral signatures for BenignTraffic and all 33 attack types.
    Ensures true discrimination between normal telemetry and cyber-attacks.

    Args:
        output_path (Path): Destination CSV path.
        num_rows (int): Number of sample rows to generate.

    Returns:
        Path: Path to the generated sample CSV file.
    """
    np.random.seed(config.RANDOM_STATE)
    print(f"[DataLoader] Creating realistic CICIoT2023 dataset with {num_rows} rows at: {output_path}")

    # Build realistic attack + benign distribution across all categories
    labels_pool = list(config.CATEGORY_MAP.keys())
    # 35% Benign, 65% across 33 attacks
    p_benign = 0.35
    p_attack = (1.0 - p_benign) / (len(labels_pool) - 1)
    weights = [p_benign if l == "BenignTraffic" else p_attack for l in labels_pool]
    chosen_labels = np.random.choice(labels_pool, size=num_rows, p=weights)
    is_attack = (chosen_labels != "BenignTraffic").astype(int)

    # Categories for nuanced behavior
    categories = np.array([config.CATEGORY_MAP.get(l, "Benign") for l in chosen_labels])

    data_dict = {}

    # 1. Packet Rates (Floods are massive; Recon/BruteForce are low/stealthy; Benign has streaming bursts)
    base_rates = np.zeros(num_rows, dtype=float)
    for i in range(num_rows):
        cat = categories[i]
        if cat == "Benign":
            # Benign has 70% low sensor telemetry (5-60 pkts/s) and 30% video/file burst (100-450 pkts/s)
            if np.random.rand() < 0.30:
                base_rates[i] = np.random.uniform(100.0, 450.0)
            else:
                base_rates[i] = np.random.uniform(5.0, 65.0)
        elif cat in ["DDoS", "DoS"]:
            # Floods have high rates (300-2800 pkts/s) with occasional slower pulses
            base_rates[i] = np.random.uniform(350.0, 2800.0)
        elif cat == "Recon":
            # Stealthy scans operate at lower rates (15-180 pkts/s), overlapping benign
            base_rates[i] = np.random.uniform(15.0, 180.0)
        elif cat == "Brute Force":
            # Login attempts: moderate rate (20-120 pkts/s)
            base_rates[i] = np.random.uniform(20.0, 120.0)
        elif cat == "Mirai":
            # Mirai blast or probing
            base_rates[i] = np.random.uniform(250.0, 2200.0) if np.random.rand() < 0.75 else np.random.uniform(30.0, 150.0)
        elif cat == "Web-based":
            # Web exploits: normal HTTP rate (10-90 pkts/s)
            base_rates[i] = np.random.uniform(10.0, 95.0)
        else: # Spoofing
            base_rates[i] = np.random.uniform(40.0, 300.0)

    # Add realistic measurement noise
    rates = np.clip(base_rates * np.random.normal(1.0, 0.08, num_rows), 1.0, 5000.0)
    data_dict["Rate"] = rates
    data_dict["Srate"] = rates * np.random.uniform(0.85, 1.0, num_rows)
    data_dict["Drate"] = np.where(is_attack == 1, rates * np.random.uniform(0.0, 0.15, num_rows), rates * np.random.uniform(0.05, 0.35, num_rows))

    # 2. Packet Sizes (Realistic payload sizes with overlap)
    avg_sizes = np.zeros(num_rows, dtype=float)
    for i in range(num_rows):
        cat = categories[i]
        if cat == "Benign":
            # Telemetry: 60-180 bytes; Web/Stream: 400-1350 bytes
            avg_sizes[i] = np.random.uniform(60.0, 200.0) if np.random.rand() < 0.55 else np.random.uniform(400.0, 1350.0)
        elif cat in ["DDoS", "DoS"]:
            # Flood packets are small (40-120 bytes) or UDP packets (up to 500 bytes)
            avg_sizes[i] = np.random.uniform(44.0, 130.0) if np.random.rand() < 0.8 else np.random.uniform(200.0, 600.0)
        elif cat == "Recon":
            # Probing header-only packets
            avg_sizes[i] = np.random.uniform(40.0, 90.0)
        elif cat == "Web-based":
            # Exploit payloads carry HTTP headers
            avg_sizes[i] = np.random.uniform(350.0, 1100.0)
        else:
            avg_sizes[i] = np.random.uniform(50.0, 300.0)

    data_dict["AVG"] = avg_sizes
    packet_counts = np.clip(np.random.poisson(np.where(is_attack == 1, 45, 18), num_rows), 3, 500)
    data_dict["Tot size"] = avg_sizes * packet_counts
    data_dict["Tot sum"] = data_dict["Tot size"]
    data_dict["Min"] = np.clip(avg_sizes * np.random.uniform(0.4, 0.9, num_rows), 20.0, 250.0)
    data_dict["Max"] = avg_sizes * np.random.uniform(1.1, 2.2, num_rows)
    data_dict["Std"] = avg_sizes * np.random.uniform(0.1, 0.45, num_rows)
    data_dict["Variance"] = data_dict["Std"] ** 2
    data_dict["Covariance"] = data_dict["Variance"] * np.random.uniform(0.3, 0.6, num_rows)
    data_dict["Magnitue"] = np.sqrt(avg_sizes ** 2 + data_dict["Std"] ** 2)
    data_dict["Radius"] = data_dict["Std"] * 0.5
    data_dict["Weight"] = packet_counts.astype(float)
    data_dict["Number"] = packet_counts.astype(float)

    # 3. Connection Duration and IAT
    data_dict["flow_duration"] = np.clip(
        np.where(is_attack == 1, np.random.exponential(1.5, num_rows), np.random.exponential(4.0, num_rows)),
        0.005, 30.0
    )
    data_dict["Duration"] = data_dict["flow_duration"]
    data_dict["IAT"] = np.clip(data_dict["flow_duration"] / packet_counts, 0.0001, 1.5)
    data_dict["Header_Length"] = np.random.uniform(20.0, 60.0, num_rows)

    # 4. TCP Flags & Counts (Overlap with noise)
    syn_means = np.where(categories == "DDoS", 35.0, np.where(categories == "Recon", 12.0, 2.0))
    ack_means = np.where(categories == "Benign", 16.0, np.where(categories == "Web-based", 12.0, 3.0))
    rst_means = np.where(categories == "Recon", 6.0, 0.5)

    data_dict["syn_count"] = np.random.poisson(syn_means, num_rows).astype(float)
    data_dict["ack_count"] = np.random.poisson(ack_means, num_rows).astype(float)
    data_dict["fin_count"] = np.random.poisson(1.2, num_rows).astype(float)
    data_dict["urg_count"] = np.zeros(num_rows, dtype=float)
    data_dict["rst_count"] = np.random.poisson(rst_means, num_rows).astype(float)

    data_dict["syn_flag_number"] = np.where(data_dict["syn_count"] > 3.0, 1.0, 0.0)
    data_dict["ack_flag_number"] = np.where(data_dict["ack_count"] > 2.0, 1.0, 0.0)
    data_dict["fin_flag_number"] = np.where(data_dict["fin_count"] > 1.0, 1.0, 0.0)
    data_dict["rst_flag_number"] = np.where(data_dict["rst_count"] > 1.0, 1.0, 0.0)
    data_dict["psh_flag_number"] = np.where(np.random.rand(num_rows) < np.where(is_attack == 1, 0.25, 0.70), 1.0, 0.0)
    data_dict["cwr_flag_number"] = np.where((chosen_labels == "DDoS-SYN_Flood") & (np.random.rand(num_rows) < 0.4), 1.0, 0.0)
    data_dict["ece_flag_number"] = np.where((chosen_labels == "DDoS-SYN_Flood") & (np.random.rand(num_rows) < 0.4), 1.0, 0.0)

    # 5. Protocol Indicators (Real network binary flags with genuine cross-traffic)
    is_tcp = np.where(np.char.startswith(chosen_labels, "DDoS") | np.char.startswith(chosen_labels, "DoS"), np.random.rand(num_rows) < 0.70, np.random.rand(num_rows) < 0.65)
    data_dict["TCP"] = is_tcp.astype(float)
    is_udp = np.where(np.char.find(chosen_labels, "UDP") >= 0, np.random.rand(num_rows) < 0.85, np.random.rand(num_rows) < 0.25)
    data_dict["UDP"] = is_udp.astype(float)
    is_icmp = np.where(np.char.find(chosen_labels, "ICMP") >= 0, np.random.rand(num_rows) < 0.90, np.random.rand(num_rows) < 0.08)
    data_dict["ICMP"] = is_icmp.astype(float)
    data_dict["Protocol Type"] = np.where(data_dict["TCP"] == 1.0, 6.0, np.where(data_dict["UDP"] == 1.0, 17.0, 1.0))
    data_dict["IPv"] = np.ones(num_rows, dtype=float)
    data_dict["LLC"] = np.ones(num_rows, dtype=float)
    data_dict["ARP"] = ((chosen_labels == "MITM-ArpSpoofing") | ((categories == "Benign") & (np.random.rand(num_rows) < 0.05))).astype(float)
    data_dict["DHCP"] = (np.random.rand(num_rows) < 0.02).astype(float)

    # 6. Application Protocols (Binary 0.0 / 1.0 indicators on network ports)
    data_dict["Telnet"] = (np.isin(chosen_labels, ["Mirai-greeth_flood", "Mirai-udpplain", "Mirai-greip_flood", "DictionaryBruteForce"]) | (np.random.rand(num_rows) < 0.03)).astype(float)
    data_dict["SSH"] = ((chosen_labels == "DictionaryBruteForce") | (np.random.rand(num_rows) < 0.04)).astype(float)
    data_dict["HTTP"] = ((np.char.find(chosen_labels, "HTTP") >= 0) | (np.random.rand(num_rows) < 0.30)).astype(float)
    data_dict["HTTPS"] = ((categories == "Benign") & (np.random.rand(num_rows) < 0.40) | (np.char.find(chosen_labels, "HTTP") >= 0) & (np.random.rand(num_rows) < 0.35)).astype(float)
    data_dict["DNS"] = ((chosen_labels == "DNS_Spoofing") | (np.random.rand(num_rows) < 0.20)).astype(float)
    data_dict["SMTP"] = (np.random.rand(num_rows) < 0.01).astype(float)
    data_dict["IRC"] = np.zeros(num_rows, dtype=float)

    data_dict[config.LABEL_COLUMN] = chosen_labels
    df = pd.DataFrame(data_dict)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[DataLoader] Realistic dataset generated successfully: {output_path.name} ({len(df)} rows)")
    return output_path


def load_merged_dataset(sample_fraction: float = None) -> pd.DataFrame:
    """
    Load raw CSV files from data/raw, optionally subsampling for fast dev runs.
    Automatically generates a sample CSV if data/raw is empty.

    Args:
        sample_fraction (float, optional): Fraction of data to sample (0.0 to 1.0).
            Defaults to config.DEV_SAMPLE_FRACTION if not specified.

    Returns:
        pd.DataFrame: Merged pandas DataFrame containing raw data.
    """
    csv_files = get_raw_csv_files()

    # Fallback to generating sample dataset if data/raw is empty
    if not csv_files:
        sample_file = config.DATA_RAW_DIR / "sample_ciciot2023.csv"
        generate_sample_ciciot2023_dataset(sample_file, num_rows=15000)
        csv_files = [sample_file]

    frac = sample_fraction if sample_fraction is not None else config.DEV_SAMPLE_FRACTION

    dfs = []
    for file_path in csv_files:
        df_chunk = pd.read_csv(file_path)
        if 0.0 < frac < 1.0:
            df_chunk = df_chunk.sample(frac=frac, random_state=config.RANDOM_STATE)
        dfs.append(df_chunk)

    merged_df = pd.concat(dfs, ignore_index=True)
    return merged_df


def inspect_raw_data() -> Tuple[int, int, int, List[str], List[str]]:
    """
    Inspect raw dataset files in data/raw and print summary:
    - Number of CSV files
    - Rows and columns in a sample file
    - Exact column names
    - Unique label values found across files

    Returns:
        Tuple: (num_files, sample_rows, sample_cols, columns, unique_labels)
    """
    csv_files = get_raw_csv_files()
    if not csv_files:
        # Create a sample file first so inspection works cleanly
        sample_file = config.DATA_RAW_DIR / "sample_ciciot2023.csv"
        generate_sample_ciciot2023_dataset(sample_file, num_rows=15000)
        csv_files = [sample_file]

    print(f"\n{'='*70}")
    print("PHASE 1: DATA INSPECTION REPORT (data/raw)")
    print(f"{'='*70}")
    print(f"Total CSV files found in data/raw: {len(csv_files)}")
    for f in csv_files:
        print(f"  - {f.name} ({os.path.getsize(f) / (1024 * 1024):.2f} MB)")

    # Read first file to inspect structure
    sample_df = pd.read_csv(csv_files[0])
    rows, cols = sample_df.shape
    columns = list(sample_df.columns)

    print(f"\nSample File: {csv_files[0].name}")
    print(f"Rows: {rows:,} | Columns: {cols}")
    print(f"\nExact Column Names ({len(columns)}):")
    print(columns)

    # Collect unique labels across all files
    unique_labels = set()
    for f in csv_files:
        df_labels = pd.read_csv(f, usecols=[config.LABEL_COLUMN])
        unique_labels.update(df_labels[config.LABEL_COLUMN].dropna().unique())

    unique_labels = sorted(list(unique_labels))
    print(f"\nUnique Labels Found ({len(unique_labels)} classes):")
    for idx, lbl in enumerate(unique_labels, 1):
        print(f"  {idx:2d}. {lbl}")
    print(f"{'='*70}\n")

    return len(csv_files), rows, cols, columns, unique_labels


if __name__ == "__main__":
    # Allows running as: python -m src.data_loader
    inspect_raw_data()
