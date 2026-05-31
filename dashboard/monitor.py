import platform
import subprocess
import time
import json
import os
from datetime import datetime

DEVICES_FILE = os.path.join(os.path.dirname(__file__), "..", "devices.json")

# Fallback defaults if devices.json doesn't exist yet
DEFAULT_DEVICES = [
    {"name": "Google DNS",     "ip": "8.8.8.8"},
    {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
    {"name": "Local Router",   "ip": "192.168.1.1"},
]


def load_devices():
    """Load devices from devices.json, fall back to defaults."""
    path = os.path.abspath(DEVICES_FILE)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_DEVICES


def ping_device(ip):
    """
    Ping a device once and return (status, response_time_ms).
    Returns ("ONLINE", ms) or ("OFFLINE", None).
    """
    param = "-n" if platform.system().lower() == "windows" else "-c"

    start = time.time()

    result = subprocess.run(
        ["ping", param, "1", "-W", "1", ip],
        capture_output=True,
        text=True
    )

    elapsed_ms = round((time.time() - start) * 1000)

    if result.returncode == 0:
        # Try to extract real RTT from ping output
        rtt = _parse_rtt(result.stdout)
        return "ONLINE", rtt if rtt else elapsed_ms
    else:
        return "OFFLINE", None


def _parse_rtt(output):
    """Extract RTT from ping stdout. Returns int ms or None."""
    import re
    # Linux: "rtt min/avg/max/mdev = 12.3/12.3/12.3/0.0 ms"
    match = re.search(r'rtt[^=]+=\s*([\d.]+)/([\d.]+)', output)
    if match:
        return round(float(match.group(2)))  # avg
    # Windows: "Average = 12ms"
    match = re.search(r'Average\s*=\s*(\d+)ms', output)
    if match:
        return int(match.group(1))
    # macOS: "round-trip min/avg/max/stddev = 12.3/12.3/12.3/0.0 ms"
    match = re.search(r'round-trip[^=]+=\s*([\d.]+)/([\d.]+)', output)
    if match:
        return round(float(match.group(2)))
    return None


def scan_devices():
    """Scan all devices and return results list."""
    results = []
    for device in load_devices():
        status, response_time = ping_device(device["ip"])
        results.append({
            "name":          device["name"],
            "ip":            device["ip"],
            "status":        status,
            "response_time": response_time,
            "timestamp":     datetime.now().strftime("%H:%M:%S"),
        })
    return results