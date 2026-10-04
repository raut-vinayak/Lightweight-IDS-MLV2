"""
Live Traffic Capture & Real-Time Inference Module for Lightweight IoT IDS.

Runs on an IDS sensor node / VM in promiscuous mode:
1. Sniffs live packets using Scapy (chosen over pyshark for standalone reliability,
   lack of external tshark daemon dependencies, and low-latency packet dissection).
2. Aggregates network packets into bidirectional/unidirectional flows by 5-tuple:
   (src_ip, dst_ip, src_port, dst_port, protocol) within a sliding time window (default 2s).
3. Dynamically extracts features required by the loaded model artifact (e.g. K=10 binary model).
4. Performs real-time inference, printing formatted live alerts to stdout.
5. Streams predictions as structured JSON lines to results/live_predictions.jsonl.
"""

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import joblib
from src import config

# Import Scapy components with fallback for environments without WinPcap/Npcap
try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class FlowRecord:
    """
    Tracks and aggregates packet statistics for a single network flow over a time window.
    """
    def __init__(self, key: tuple, start_time: float):
        self.key = key  # (src_ip, dst_ip, src_port, dst_port, proto)
        self.start_time = start_time
        self.last_time = start_time
        self.packet_sizes: List[int] = []
        self.header_lengths: List[int] = []
        self.syn_count = 0
        self.fin_count = 0
        self.rst_count = 0
        self.ack_count = 0
        self.psh_count = 0

    def add_packet(self, size: int, header_len: int, flags: str, timestamp: float):
        self.packet_sizes.append(size)
        self.header_lengths.append(header_len)
        self.last_time = timestamp
        if "S" in flags:
            self.syn_count += 1
        if "F" in flags:
            self.fin_count += 1
        if "R" in flags:
            self.rst_count += 1
        if "A" in flags:
            self.ack_count += 1
        if "P" in flags:
            self.psh_count += 1

    def compute_features(self, required_features: List[str]) -> Dict[str, float]:
        """
        Derive feature vector for the flow matching model's expected features.

        Note on live feature computation:
        Features like packet size statistics (Min, Max, AVG, Std), counts (syn, ack, rst),
        rates (Rate, Srate), and protocols (TCP, UDP, ICMP) are calculated directly from
        the live window. Long-term state features (e.g. multi-day Weight) are approximated
        using current flow weight/volume.
        """
        duration = max(0.0001, self.last_time - self.start_time)
        count = len(self.packet_sizes)
        tot_size = float(sum(self.packet_sizes))
        sizes = np.array(self.packet_sizes, dtype=float)

        feat_dict = {
            "flow_duration": duration,
            "Duration": duration,
            "Header_Length": float(sum(self.header_lengths)),
            "Rate": count / duration,
            "Srate": count / duration,
            "Drate": 0.0,
            "Tot sum": tot_size,
            "Tot size": tot_size,
            "Min": float(np.min(sizes)) if count > 0 else 0.0,
            "Max": float(np.max(sizes)) if count > 0 else 0.0,
            "AVG": float(np.mean(sizes)) if count > 0 else 0.0,
            "Std": float(np.std(sizes)) if count > 0 else 0.0,
            "Variance": float(np.var(sizes)) if count > 0 else 0.0,
            "Covariance": float(np.var(sizes) * 0.5) if count > 0 else 0.0,
            "Magnitue": float(np.sqrt(np.mean(sizes**2))) if count > 0 else 0.0,
            "Radius": float(np.std(sizes) * 0.5) if count > 0 else 0.0,
            "Weight": float(count),
            "Number": float(count),
            "IAT": duration / max(1, count - 1),
            "syn_count": float(self.syn_count),
            "fin_count": float(self.fin_count),
            "rst_count": float(self.rst_count),
            "ack_count": float(self.ack_count),
            "urg_count": 0.0,
            "syn_flag_number": 1.0 if self.syn_count > 0 else 0.0,
            "fin_flag_number": 1.0 if self.fin_count > 0 else 0.0,
            "rst_flag_number": 1.0 if self.rst_count > 0 else 0.0,
            "psh_flag_number": 1.0 if self.psh_count > 0 else 0.0,
            "ack_flag_number": 1.0 if self.ack_count > 0 else 0.0,
            "ece_flag_number": 0.0,
            "cwr_flag_number": 0.0,
            "TCP": 1.0 if self.key[4] == 6 else 0.0,
            "UDP": 1.0 if self.key[4] == 17 else 0.0,
            "ICMP": 1.0 if self.key[4] == 1 else 0.0,
            "Protocol Type": float(self.key[4]),
            "HTTP": 1.0 if (self.key[2] == 80 or self.key[3] == 80) else 0.0,
            "HTTPS": 1.0 if (self.key[2] == 443 or self.key[3] == 443) else 0.0,
            "DNS": 1.0 if (self.key[2] == 53 or self.key[3] == 53) else 0.0,
            "Telnet": 1.0 if (self.key[2] == 23 or self.key[3] == 23) else 0.0,
            "SMTP": 1.0 if (self.key[2] == 25 or self.key[3] == 25) else 0.0,
            "SSH": 1.0 if (self.key[2] == 22 or self.key[3] == 22) else 0.0,
            "IRC": 1.0 if (self.key[2] == 6667 or self.key[3] == 6667) else 0.0,
            "DHCP": 1.0 if (self.key[2] in [67, 68] or self.key[3] in [67, 68]) else 0.0,
            "ARP": 0.0,
            "IPv": 1.0,
            "LLC": 1.0
        }

        # Return vector aligned with model's expected features
        aligned = {}
        for req in required_features:
            aligned[req] = feat_dict.get(req, 0.0)
        return aligned


def process_and_predict_flow(
    flow: FlowRecord,
    artifact: Dict[str, Any],
    json_log_path: Path
):
    """
    Run inference on completed flow, print formatted alert, and append JSON log.
    """
    model = artifact["model"]
    features = artifact["features"]
    task = artifact["task"]
    scaler = artifact.get("scaler", None)

    flow_features = flow.compute_features(features)
    df_feat = pd.DataFrame([flow_features])

    # Apply scaler if trained with one
    if scaler is not None and hasattr(scaler, "transform"):
        try:
            df_scaled = pd.DataFrame(scaler.transform(df_feat), columns=features)
        except Exception:
            df_scaled = df_feat
    else:
        df_scaled = df_feat

    start_t = time.perf_counter()
    pred = model.predict(df_scaled)[0]
    latency_ms = (time.perf_counter() - start_t) * 1000.0

    confidence = 100.0
    if hasattr(model, "predict_proba"):
        try:
            confidence = float(np.max(model.predict_proba(df_scaled)[0])) * 100.0
        except Exception:
            pass

    src_ip, dst_ip, src_port, dst_port, proto = flow.key
    proto_name = "TCP" if proto == 6 else ("UDP" if proto == 17 else ("ICMP" if proto == 1 else str(proto)))

    if task == "binary":
        label_str = "ATTACK [1]" if pred == 1 else "BENIGN [0]"
        alert_tag = "[ALERT] " if pred == 1 else "[NORMAL]"
    else:
        label_str = str(pred)
        alert_tag = "[ALERT] " if pred != "Benign" else "[NORMAL]"

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    # Live console alert line (plain ASCII for safe cross-platform terminal output)
    print(
        f"[{timestamp_str}] {alert_tag} | {src_ip}:{src_port} -> {dst_ip}:{dst_port} ({proto_name}) | "
        f"Pred: {label_str:<12} | Conf: {confidence:>5.1f}% | Latency: {latency_ms:.3f} ms"
    )

    # Structured JSON log record
    log_record = {
        "timestamp": timestamp_str,
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": src_port,
        "dst_port": dst_port,
        "protocol": proto_name,
        "prediction": str(pred),
        "confidence_pct": round(confidence, 2),
        "latency_ms": round(latency_ms, 4)
    }

    with open(json_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_record) + "\n")


def simulate_vm_lab_traffic(artifact: Dict[str, Any], json_log_path: Path):
    """
    Simulate VM lab traffic (Benign Ping + Attacker Nmap Port Scan & DoS bursts)
    for validation on platforms where physical packet capture is not available.
    """
    print(f"\n[LiveCapture] Simulating VM Lab Traffic (Attacker: 192.168.1.100, Victim: 192.168.1.50)...")
    print(f"[LiveCapture] Streaming predictions to: {json_log_path}\n")

    traffic_scenarios = [
        # (src_ip, dst_ip, src_port, dst_port, proto, is_attack_type, pkts)
        ("192.168.1.20", "192.168.1.50", 0, 0, 1, "ping", 4),              # Benign ICMP Echo (Ping)
        ("192.168.1.100", "192.168.1.50", 49152, 80, 6, "nmap_syn", 10),    # Attacker Nmap SYN scan port 80
        ("192.168.1.100", "192.168.1.50", 49153, 22, 6, "nmap_syn", 10),    # Attacker Nmap SYN scan port 22
        ("192.168.1.100", "192.168.1.50", 49154, 443, 6, "nmap_syn", 10),   # Attacker Nmap SYN scan port 443
        ("192.168.1.20", "192.168.1.50", 52310, 443, 6, "normal_web", 25),  # Benign HTTPS traffic
        ("192.168.1.100", "192.168.1.50", 55555, 80, 6, "dos_burst", 500),  # Attacker SYN Flood DoS burst
    ]

    for src_ip, dst_ip, sport, dport, proto, scenario, pkt_count in traffic_scenarios:
        now = time.time()
        flow = FlowRecord((src_ip, dst_ip, sport, dport, proto), start_time=now)

        if scenario == "ping":
            for _ in range(pkt_count):
                flow.add_packet(size=64, header_len=20, flags="", timestamp=now + 0.1)
        elif scenario == "nmap_syn":
            for _ in range(pkt_count):
                flow.add_packet(size=44, header_len=20, flags="S", timestamp=now + 0.05)
        elif scenario == "normal_web":
            for _ in range(pkt_count):
                flow.add_packet(size=1460, header_len=32, flags="A", timestamp=now + 0.02)
        elif scenario == "dos_burst":
            for _ in range(pkt_count):
                flow.add_packet(size=60, header_len=20, flags="S", timestamp=now + 0.001)

        process_and_predict_flow(flow, artifact, json_log_path)
        time.sleep(0.3)


def main():
    """
    Entrypoint for live network capture script.
    """
    parser = argparse.ArgumentParser(description="Live Traffic Capture & IDS Inference")
    parser.add_argument("--interface", type=str, default=None, help="Network interface name (e.g. eth0)")
    parser.add_argument("--window", type=float, default=2.0, help="Sliding time window for flow aggregation (sec)")
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(config.MODELS_DIR / "model_binary_DecisionTree_k10.joblib"),
        help="Path to trained model artifact"
    )
    parser.add_argument(
        "--output_json",
        type=str,
        default=str(config.LIVE_PREDICTIONS_JSONL),
        help="Output JSONL log path"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Simulate VM lab traffic (Attacker ping/nmap/flood) for testing"
    )

    args = parser.parse_args()

    model_file = Path(args.model_path)
    if not model_file.exists():
        # Fallback to any available k10 binary model
        fallback_models = list(config.MODELS_DIR.glob("model_binary_*_k10.joblib"))
        if fallback_models:
            model_file = fallback_models[0]
        else:
            print(f"[LiveCapture] Error: No model file found at {args.model_path}. Run main.py first.")
            return

    artifact = joblib.load(model_file)
    json_log = Path(args.output_json)
    json_log.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"LIVE IDS INFERENCE ENGINE (Model: {artifact['model_name']} | K={artifact['k']})")
    print(f"Features: {', '.join(artifact['features'])}")
    print(f"{'='*70}")

    if args.simulate or not SCAPY_AVAILABLE:
        simulate_vm_lab_traffic(artifact, json_log)
    else:
        # Live packet sniffing using Scapy
        print(f"[LiveCapture] Sniffing live packets on interface: {args.interface or 'default'}...")
        active_flows: Dict[tuple, FlowRecord] = {}

        def packet_handler(pkt):
            if IP in pkt:
                ip_src = pkt[IP].src
                ip_dst = pkt[IP].dst
                proto = pkt[IP].proto
                sport = pkt.sport if (TCP in pkt or UDP in pkt) else 0
                dport = pkt.dport if (TCP in pkt or UDP in pkt) else 0
                flags = str(pkt[TCP].flags) if TCP in pkt else ""
                key = (ip_src, ip_dst, sport, dport, proto)
                t_now = time.time()

                if key not in active_flows:
                    active_flows[key] = FlowRecord(key, start_time=t_now)

                flow = active_flows[key]
                flow.add_packet(size=len(pkt), header_len=len(pkt[IP]), flags=flags, timestamp=t_now)

                # If flow exceeded window duration, evaluate and reset
                if (t_now - flow.start_time) >= args.window:
                    process_and_predict_flow(flow, artifact, json_log)
                    del active_flows[key]

        sniff(iface=args.interface, prn=packet_handler, store=False)


if __name__ == "__main__":
    main()
