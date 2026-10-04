import json
import time
from pathlib import Path

bridge_path = Path("results/traffic_bridge.json")
audit_path = Path("results/audit_log.json")

print("1. Reading current traffic_bridge.json...")
if bridge_path.exists():
    with open(bridge_path, "r", encoding="utf-8") as f:
        print(f.read())

print("2. Simulating new attack from Attacker Studio (Port 8502)...")
test_pkt = {
    "packet_id": f"PKT-{int(time.time() * 1000)}",
    "timestamp": "2026-10-05 01:55:00.000",
    "epoch_time": time.time(),
    "status": "pending",
    "processed": False,
    "target_network": "🏥 Smart Healthcare & Hospital (IoMT)",
    "target_device": "ICU Patient Vitals & ECG Monitor (10.0.4.12)",
    "gateway_ip": "10.0.4.1",
    "attacker_ip": "198.51.100.77",
    "scenario": "DDoS SYN Flood Blast 🎭 [STEALTH EVASION]",
    "intensity_level": "HEAVY (CRITICAL)",
    "is_threat": True,
    "is_adversarial_evasion": True,
    "evasion_tactics": ["Rate Throttled < 100 pkts/s", "Dummy Payload Padding (+700B)"],
    "features": {
        "Rate": 88.0,
        "Srate": 88.0,
        "Drate": 0.0,
        "AVG": 750.0,
        "Tot sum": 30000.0,
        "Tot size": 30000.0,
        "Min": 20.0,
        "Max": 900.0,
        "Std": 120.0,
        "Variance": 14400.0,
        "Covariance": 6000.0,
        "ack_count": 0.0,
        "syn_count": 85.0,
        "fin_count": 0.0,
        "rst_count": 5.0,
        "ack_flag_number": 0.0,
        "syn_flag_number": 1.0,
        "psh_flag_number": 0.0,
        "cwr_flag_number": 1.0,
        "ece_flag_number": 1.0,
        "Telnet": 0.0,
        "SSH": 0.0,
        "HTTP": 0.0,
        "HTTPS": 0.0,
        "DNS": 0.0,
        "TCP": 1.0,
        "UDP": 0.0,
        "ICMP": 0.0,
        "Protocol Type": 6.0,
        "IPv": 1.0,
        "LLC": 1.0,
        "flow_duration": 0.5,
        "Duration": 0.5,
        "IAT": 0.015,
        "Header_Length": 20.0,
        "Weight": 40.0,
        "Number": 40.0,
        "Magnitue": 55.0,
        "Radius": 5.0,
        "ARP": 0.0,
        "DHCP": 0.0
    }
}

with open(bridge_path, "w", encoding="utf-8") as f:
    json.dump(test_pkt, f, indent=2)

print("Packet written to bridge. Waiting 4 seconds for dashboard fragment auto-pickup...")
time.sleep(4)

print("3. Checking if bridge was processed and marked:")
with open(bridge_path, "r", encoding="utf-8") as f:
    updated_bridge = json.load(f)
    print(f"Bridge status: {updated_bridge.get('status')}, processed: {updated_bridge.get('processed')}")

print("4. Checking audit_log.json:")
if audit_path.exists():
    with open(audit_path, "r", encoding="utf-8") as f:
        audit_data = json.load(f)
        print(f"Total audit entries: {len(audit_data)}")
        if audit_data:
            print("Latest audit entry:", json.dumps(audit_data[0], indent=2))
