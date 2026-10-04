import json
import time
from pathlib import Path

bridge_path = Path("results/traffic_bridge.json")
audit_path = Path("results/audit_log.json")

test_pkt2 = {
    "packet_id": f"PKT-{int(time.time() * 1000)}",
    "timestamp": "2026-10-05 01:57:00.000",
    "epoch_time": time.time(),
    "status": "pending",
    "processed": False,
    "target_network": "🏥 Smart Healthcare & Hospital (IoMT)",
    "target_device": "Automated Smart Infusion Pump (10.0.4.18)",
    "gateway_ip": "10.0.4.1",
    "attacker_ip": "198.51.100.99",
    "scenario": "Credential Brute-Force",
    "intensity_level": "MEDIUM THREAT",
    "is_threat": True,
    "is_adversarial_evasion": False,
    "evasion_tactics": [],
    "features": {
        "Rate": 650.0,
        "Srate": 650.0,
        "Drate": 0.0,
        "AVG": 180.0,
        "Tot sum": 7200.0,
        "Tot size": 7200.0,
        "Min": 20.0,
        "Max": 64.0,
        "Std": 10.0,
        "Variance": 100.0,
        "Covariance": 50.0,
        "ack_count": 0.0,
        "syn_count": 15.0,
        "fin_count": 0.0,
        "rst_count": 5.0,
        "ack_flag_number": 0.0,
        "syn_flag_number": 1.0,
        "psh_flag_number": 0.0,
        "cwr_flag_number": 1.0,
        "ece_flag_number": 1.0,
        "Telnet": 1.0,
        "SSH": 1.0,
        "HTTP": 0.0,
        "HTTPS": 0.0,
        "DNS": 0.0,
        "TCP": 1.0,
        "UDP": 0.0,
        "ICMP": 0.0,
        "Protocol Type": 6.0,
        "IPv": 1.0,
        "LLC": 1.0,
        "flow_duration": 0.05,
        "Duration": 0.05,
        "IAT": 0.0005,
        "Header_Length": 20.0,
        "Weight": 250.0,
        "Number": 250.0,
        "Magnitue": 55.0,
        "Radius": 5.0,
        "ARP": 0.0,
        "DHCP": 0.0
    }
}

with open(bridge_path, "w", encoding="utf-8") as f:
    json.dump(test_pkt2, f, indent=2)

print("Second attack injected. Waiting 4 seconds for auto-pickup...")
time.sleep(4)

with open(audit_path, "r", encoding="utf-8") as f:
    audit_data = json.load(f)
    print(f"Total audit entries now: {len(audit_data)}")
    for idx, e in enumerate(audit_data):
        print(f"[{idx+1}] {e['Time']} | {e['Traffic Type']} | {e['Target Node']} | {e['Verdict']}")
