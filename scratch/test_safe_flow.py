import json
import time
from pathlib import Path

bridge_path = Path("results/traffic_bridge.json")
audit_path = Path("results/audit_log.json")

test_pkt3 = {
    "packet_id": f"PKT-{int(time.time() * 1000)}",
    "timestamp": "2026-10-05 01:58:00.000",
    "epoch_time": time.time(),
    "status": "pending",
    "processed": False,
    "target_network": "🏥 Smart Healthcare & Hospital (IoMT)",
    "target_device": "Central Nursing Station Console (10.0.4.5)",
    "gateway_ip": "10.0.4.1",
    "attacker_ip": "10.0.4.30",
    "scenario": "Routine Telemetry Heartbeat",
    "intensity_level": "BENIGN (SAFE)",
    "is_threat": False,
    "is_adversarial_evasion": False,
    "evasion_tactics": [],
    "features": {
        "Rate": 22.0,
        "Srate": 20.0,
        "Drate": 15.0,
        "AVG": 850.0,
        "Tot sum": 17000.0,
        "Tot size": 17000.0,
        "Min": 64.0,
        "Max": 1400.0,
        "Std": 150.0,
        "Variance": 22500.0,
        "Covariance": 10000.0,
        "ack_count": 20.0,
        "syn_count": 1.0,
        "fin_count": 1.0,
        "rst_count": 0.0,
        "ack_flag_number": 1.0,
        "syn_flag_number": 0.0,
        "psh_flag_number": 1.0,
        "cwr_flag_number": 0.0,
        "ece_flag_number": 0.0,
        "Telnet": 0.0,
        "SSH": 0.0,
        "HTTP": 0.0,
        "HTTPS": 1.0,
        "DNS": 0.0,
        "TCP": 1.0,
        "UDP": 0.0,
        "ICMP": 0.0,
        "Protocol Type": 6.0,
        "IPv": 1.0,
        "LLC": 1.0,
        "flow_duration": 5.0,
        "Duration": 5.0,
        "IAT": 0.04,
        "Header_Length": 40.0,
        "Weight": 15.0,
        "Number": 15.0,
        "Magnitue": 860.0,
        "Radius": 75.0,
        "ARP": 0.0,
        "DHCP": 0.0
    }
}

with open(bridge_path, "w", encoding="utf-8") as f:
    json.dump(test_pkt3, f, indent=2)

print("Safe telemetry injected. Waiting 4 seconds for auto-pickup...")
time.sleep(4)

with open(audit_path, "r", encoding="utf-8") as f:
    audit_data = json.load(f)
    print("Total audit entries now:", len(audit_data))
    print("Latest entry verdict:", audit_data[0].get("Verdict"))
    print("Latest entry type:", audit_data[0].get("Traffic Type"))
