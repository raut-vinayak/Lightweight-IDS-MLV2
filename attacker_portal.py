"""
Attacker Portal & Traffic Injection Studio.

Modern Fresh-Theme Offensive Testing Cockpit with Large High-Impact Controls.
Running on Port 8502.
"""

import json
import time
from datetime import datetime
from pathlib import Path
import streamlit as st
import numpy as np
from src import config

# Page configuration
st.set_page_config(
    page_title="Attacker Studio — IoT Cyber Range",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Fresh Light Theme Styling with Large Prominent Elements
st.markdown("""
<style>
    /* Global Base Styling */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-size: 16px;
    }

    /* Force Light Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1.5px solid #e2e8f0 !important;
        padding-top: 1.5rem;
    }

    /* Fresh Crimson Header Banner */
    .attacker-header-fresh {
        background: linear-gradient(135deg, #e11d48 0%, #be123c 50%, #9f1239 100%);
        padding: 28px 34px;
        border-radius: 16px;
        color: #ffffff !important;
        box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.25);
        margin-bottom: 26px;
    }
    .attacker-header-fresh h1 {
        color: #ffffff !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
    }
    .attacker-header-fresh p {
        color: #ffe4e6 !important;
        font-size: 17px !important;
        margin-top: 8px !important;
        line-height: 1.5;
    }

    /* Large Action Trigger Cards */
    .action-card {
        background: #ffffff;
        border: 2px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px 20px;
        text-align: center;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        margin-bottom: 12px;
    }
    .action-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 22px rgba(0, 0, 0, 0.08);
    }
    .action-card-safe {
        border-top: 6px solid #10b981;
    }
    .action-card-small {
        border-top: 6px solid #f59e0b;
    }
    .action-card-medium {
        border-top: 6px solid #f97316;
    }
    .action-card-heavy {
        border-top: 6px solid #ef4444;
    }

    .card-title {
        font-size: 19px;
        font-weight: 800;
        margin-bottom: 6px;
    }
    .card-desc {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 14px;
        min-height: 38px;
    }

    /* Big Prominent Buttons */
    .stButton > button {
        width: 100% !important;
        min-height: 56px !important;
        font-size: 17px !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12) !important;
    }

    /* Large Confirmation Banners */
    .confirm-banner-threat {
        background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
        border: 2px solid #f43f5e;
        border-left: 10px solid #e11d48;
        padding: 22px 28px;
        border-radius: 14px;
        color: #9f1239;
        margin-top: 18px;
        box-shadow: 0 6px 18px rgba(225, 29, 72, 0.12);
    }
    .confirm-banner-threat h3 {
        color: #9f1239 !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin: 0 0 10px 0 !important;
    }

    .confirm-banner-safe {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 2px solid #34d399;
        border-left: 10px solid #10b981;
        padding: 22px 28px;
        border-radius: 14px;
        color: #065f46;
        margin-top: 18px;
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.12);
    }
    .confirm-banner-safe h3 {
        color: #065f46 !important;
        font-size: 24px !important;
        font-weight: 800 !important;
        margin: 0 0 10px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

BRIDGE_FILE = config.RESULTS_DIR / "traffic_bridge.json"

TARGET_NETWORKS = {
    "🏥 Smart Healthcare & Hospital (IoMT)": {
        "gateway": "10.0.4.1",
        "devices": [
            "ICU Patient Vitals & ECG Monitor (10.0.4.12)",
            "Automated Smart Infusion Pump (10.0.4.18)",
            "Central Nursing Station Console (10.0.4.5)",
            "Hospital Mobile Diagnostic Tablet (10.0.4.30)"
        ]
    },
    "🏠 Smart Home & Living": {
        "gateway": "192.168.1.1",
        "devices": [
            "Smart Security Camera (192.168.1.101)",
            "Voice Assistant Smart Speaker (192.168.1.102)",
            "Smart Door Lock & Thermostat (192.168.1.103)",
            "Home Smart TV 4K (192.168.1.104)"
        ]
    },
    "🏭 Industrial IoT (IIoT) & Smart Factory": {
        "gateway": "172.16.20.1",
        "devices": [
            "Assembly Line Master PLC Controller (172.16.20.10)",
            "Robotic Welding Arm Sensor Node (172.16.20.15)",
            "Factory Floor Thermal Sensor Array (172.16.20.25)",
            "SCADA Supervision Server (172.16.20.5)"
        ]
    },
    "📹 Smart CCTV Surveillance Grid": {
        "gateway": "192.168.50.1",
        "devices": [
            "Perimeter PTZ IP Camera 01 (192.168.50.21)",
            "Entrance 4K IP Camera 02 (192.168.50.22)",
            "Central NVR Storage Server (192.168.50.5)"
        ]
    },
    "🚗 Smart City & Connected Traffic": {
        "gateway": "10.88.1.1",
        "devices": [
            "Major Intersection Traffic Light Controller (10.88.1.10)",
            "Highway Doppler Speed Radar (10.88.1.15)",
            "Emergency Vehicle Preemption Beacon (10.88.1.25)"
        ]
    }
}


def transmit_packet(payload: dict):
    """Write packet payload to bridge file for real-time pickup by Defender SOC."""
    BRIDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload["status"] = "pending"
    payload["processed"] = False
    with open(BRIDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def generate_payload(net_name: str, dev_name: str, gw_ip: str, scenario: str, level: str, rate: float, size: float, is_attack: bool, evasion: bool = False) -> dict:
    """Generate structured packet payload with authentic CICIoT2023 flow features and optional adversarial evasion."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if not is_attack:
        features = {
            "Rate": 25.0,
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
        evasion_tactics = []
    else:
        # If evasion is enabled, throttle rate to bypass simple rate thresholds and pad packet size
        actual_rate = 88.0 if evasion else float(rate)
        actual_size = 750.0 if evasion else float(size)
        evasion_tactics = ["Rate Throttled < 100 pkts/s", "Dummy Payload Padding (+700B)", "SYN Flag Stealth Masking"] if evasion else []

        features = {
            "Rate": actual_rate,
            "Srate": actual_rate,
            "Drate": 0.0,
            "AVG": actual_size,
            "Tot sum": float(actual_size * 40),
            "Tot size": float(actual_size * 40),
            "Min": 20.0,
            "Max": 64.0 if not evasion else 900.0,
            "Std": 10.0 if not evasion else 120.0,
            "Variance": 100.0 if not evasion else 14400.0,
            "Covariance": 50.0 if not evasion else 6000.0,
            "ack_count": 0.0,
            "syn_count": 85.0 if "SYN" in scenario or "Blast" in scenario else 15.0,
            "fin_count": 0.0,
            "rst_count": 5.0,
            "ack_flag_number": 0.0,
            "syn_flag_number": 1.0,
            "psh_flag_number": 0.0,
            "cwr_flag_number": 1.0,
            "ece_flag_number": 1.0,
            "Telnet": 1.0 if "Telnet" in scenario or "Mirai" in scenario or "Brute" in scenario else 0.0,
            "SSH": 1.0 if "Brute" in scenario else 0.0,
            "HTTP": 1.0 if "HTTP" in scenario else 0.0,
            "HTTPS": 0.0,
            "DNS": 1.0 if "DNS" in scenario else 0.0,
            "TCP": 0.0 if "UDP" in scenario else 1.0,
            "UDP": 1.0 if "UDP" in scenario else 0.0,
            "ICMP": 1.0 if "ICMP" in scenario or "Ping" in scenario else 0.0,
            "Protocol Type": 17.0 if "UDP" in scenario else (1.0 if "ICMP" in scenario else 6.0),
            "IPv": 1.0,
            "LLC": 1.0,
            "flow_duration": 0.5 if evasion else 0.05,
            "Duration": 0.5 if evasion else 0.05,
            "IAT": 0.015 if evasion else 0.0005,
            "Header_Length": 20.0,
            "Weight": 40.0 if evasion else 250.0,
            "Number": 40.0 if evasion else 250.0,
            "Magnitue": 55.0,
            "Radius": 5.0,
            "ARP": 1.0 if "Spoofing" in scenario else 0.0,
            "DHCP": 0.0
        }

    return {
        "packet_id": f"PKT-{int(time.time() * 1000)}",
        "timestamp": now_str,
        "epoch_time": time.time(),
        "status": "pending",
        "processed": False,
        "target_network": net_name,
        "target_device": dev_name,
        "gateway_ip": gw_ip,
        "attacker_ip": f"198.51.100.{np.random.randint(15, 240)}",
        "scenario": scenario + (" 🎭 [STEALTH EVASION]" if (is_attack and evasion) else ""),
        "intensity_level": level,
        "is_threat": is_attack,
        "is_adversarial_evasion": bool(is_attack and evasion),
        "evasion_tactics": evasion_tactics,
        "features": features
    }


def main():
    st.markdown("""
    <div class="attacker-header-fresh">
        <h1>🎯 Attacker Studio & Traffic Injection Cockpit</h1>
        <p>
            Port 8502 • Standalone Offensive Testing Portal. Select target IoT infrastructure, choose attack vectors, test adversarial stealth evasion, and transmit live packets to test Defender SOC (Port 8501).
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 1. Target Infrastructure & Victim Endpoint
    st.markdown("### 1️⃣ Target IoT Infrastructure & Victim Endpoint")
    t_c1, t_c2 = st.columns([1, 1])

    with t_c1:
        chosen_net = st.selectbox("Select Target Infrastructure:", list(TARGET_NETWORKS.keys()), index=0)
        net_info = TARGET_NETWORKS[chosen_net]

    with t_c2:
        chosen_device = st.selectbox("Select Victim Device Node:", net_info["devices"], index=0)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # 2. Instant One-Click Traffic Buttons with Big Cards
    st.markdown("### 2️⃣ Traffic Injection Triggers")

    # Adversarial Evasion Toggle
    evasion_mode = st.toggle(
        "🎭 **Enable Stealth Adversarial Evasion** (Throttles packet rate < 100 pkts/s & pads payload to 750B to mimic normal telemetry)",
        value=False
    )
    if evasion_mode:
        st.warning("⚠️ **Adversarial Stealth Active:** Malicious packets will disguise their transmission speed and size to test if the Defender SOC's Decision Tree can still unmask the threat!")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)

    # Card 1: Safe Routine Traffic
    with b_col1:
        st.markdown("""
        <div class="action-card action-card-safe">
            <div class="card-title" style="color: #059669;">🟢 SAFE TELEMETRY</div>
            <div class="card-desc">Standard heartbeat sensor telemetry (~25 pkts/s, valid payload).</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 TRANSMIT SAFE", key="btn_safe", type="secondary"):
            payload = generate_payload(
                net_name=chosen_net,
                dev_name=chosen_device,
                gw_ip=net_info["gateway"],
                scenario="Routine Normal Telemetry",
                level="BENIGN (SAFE)",
                rate=25.0,
                size=850.0,
                is_attack=False,
                evasion=False
            )
            transmit_packet(payload)
            st.session_state.last_sent = payload

    # Card 2: Small / Probe Level Attack
    with b_col2:
        st.markdown("""
        <div class="action-card action-card-small">
            <div class="card-title" style="color: #d97706;">🟡 STEALTH PROBE</div>
            <div class="card-desc">Nmap port sweep / host scan with low packet rate (~450 pkts/s).</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 LAUNCH PROBE", key="btn_small", type="secondary"):
            payload = generate_payload(
                net_name=chosen_net,
                dev_name=chosen_device,
                gw_ip=net_info["gateway"],
                scenario="Nmap Stealth Port Scan",
                level="SMALL (LOW RATE)",
                rate=450.0,
                size=48.0,
                is_attack=True,
                evasion=evasion_mode
            )
            transmit_packet(payload)
            st.session_state.last_sent = payload

    # Card 3: Medium Threat Attack
    with b_col3:
        st.markdown("""
        <div class="action-card action-card-medium">
            <div class="card-title" style="color: #ea580c;">🟠 MEDIUM THREAT</div>
            <div class="card-desc">Credential brute-force on Telnet/SSH with persistent packets.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 LAUNCH BRUTE", key="btn_medium", type="secondary"):
            payload = generate_payload(
                net_name=chosen_net,
                dev_name=chosen_device,
                gw_ip=net_info["gateway"],
                scenario="Credential Brute-Force",
                level="MEDIUM THREAT",
                rate=650.0,
                size=180.0,
                is_attack=True,
                evasion=evasion_mode
            )
            transmit_packet(payload)
            st.session_state.last_sent = payload

    # Card 4: Heavy Critical Blast Attack
    with b_col4:
        st.markdown("""
        <div class="action-card action-card-heavy">
            <div class="card-title" style="color: #dc2626;">🔴 CRITICAL BLAST</div>
            <div class="card-desc">Massive DDoS SYN flood / Mirai botnet burst (~2500 pkts/s).</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💥 FIRE BLAST", key="btn_heavy", type="primary"):
            payload = generate_payload(
                net_name=chosen_net,
                dev_name=chosen_device,
                gw_ip=net_info["gateway"],
                scenario="DDoS SYN Flood Blast",
                level="HEAVY (CRITICAL)",
                rate=2500.0,
                size=54.0,
                is_attack=True,
                evasion=evasion_mode
            )
            transmit_packet(payload)
            st.session_state.last_sent = payload

    # Status confirmation banner (Big, Clear & Readable)
    if "last_sent" in st.session_state:
        p = st.session_state.last_sent
        if p["is_threat"]:
            st.markdown(f"""
            <div class="confirm-banner-threat">
                <h3>🚨 [{p['intensity_level']}] MALICIOUS ATTACK TRANSMITTED!</h3>
                <div style="font-size: 16px; line-height: 1.8;">
                    <b>Attack Vector:</b> <code>{p['scenario']}</code> &nbsp;|&nbsp; 
                    <b>Target Device:</b> <code>{p['target_device']}</code> &nbsp;|&nbsp;
                    <b>Spoofed Source:</b> <code>{p['attacker_ip']}</code><br>
                    <b>Packet Flow Rate:</b> <b>{p['features']['Rate']} pkts/s</b> &nbsp;|&nbsp; 
                    <b>Payload Size:</b> <b>{p['features']['AVG']} Bytes</b><br>
                    <span style="font-size: 15px; font-weight: 700; color: #be123c;">
                        ⚡ Transmitted across network bridge. Switch to the Defender SOC (Port 8501) to verify instant interception!
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="confirm-banner-safe">
                <h3>🟢 [SAFE] NORMAL BENIGN TELEMETRY TRANSMITTED!</h3>
                <div style="font-size: 16px; line-height: 1.8;">
                    <b>Traffic Profile:</b> <code>{p['scenario']}</code> &nbsp;|&nbsp; 
                    <b>Target Node:</b> <code>{p['target_device']}</code> &nbsp;|&nbsp;
                    <b>Source IP:</b> <code>{p['attacker_ip']}</code><br>
                    <b>Packet Rate:</b> <b>{p['features']['Rate']} pkts/s</b> &nbsp;|&nbsp; 
                    <b>Average Payload:</b> <b>{p['features']['AVG']} Bytes</b> (Standard benign parameters)<br>
                    <span style="font-size: 15px; font-weight: 700; color: #15803d;">
                        ✅ Verified normal IoT telemetry forwarded cleanly without raising alarms.
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # 3. Continuous Traffic Simulator (Live Stress Test)
    st.markdown("### 3️⃣ Automated Continuous Live Traffic Streamer")
    st.write("Simulate continuous multi-packet network traffic over time:")

    stream_col1, stream_col2 = st.columns([1, 1])

    with stream_col1:
        stream_mode = st.radio(
            "Select Continuous Stream Profile:",
            [
                "Mixed Real-World Stream (Safe ➔ Safe ➔ Attack ➔ Safe)",
                "Continuous Heavy Attack Flood (Stress Test)",
                "Continuous Safe Normal Telemetry"
            ]
        )

    with stream_col2:
        num_bursts = st.slider("Packet Bursts to Transmit:", min_value=3, max_value=12, value=5)
        start_stream_btn = st.button("⚡ START CONTINUOUS PACKET BURST", type="primary", use_container_width=True)

    if start_stream_btn:
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(num_bursts):
            if "Mixed" in stream_mode:
                is_att = (i % 3 == 2)
                scen = "DDoS SYN Flood" if is_att else "Routine Sensor Telemetry"
                lvl = "HEAVY ATTACK" if is_att else "BENIGN"
                r = 2400.0 if is_att else 25.0
                s = 54.0 if is_att else 850.0
            elif "Heavy" in stream_mode:
                is_att = True
                scen = "Massive Mirai Blast"
                lvl = "CRITICAL BLAST"
                r = 2800.0
                s = 48.0
            else:
                is_att = False
                scen = "Routine Telemetry Heartbeat"
                lvl = "BENIGN (SAFE)"
                r = 20.0
                s = 850.0

            pkt = generate_payload(chosen_net, chosen_device, net_info["gateway"], scen, lvl, r, s, is_att)
            transmit_packet(pkt)
            progress_bar.progress((i + 1) / num_bursts)
            status_text.write(f"Injected burst {i+1}/{num_bursts}: **{scen}** ➔ `{chosen_device}`")
            time.sleep(1.2)

        st.success(f"Successfully transmitted burst sequence of {num_bursts} packets!")


if __name__ == "__main__":
    main()
