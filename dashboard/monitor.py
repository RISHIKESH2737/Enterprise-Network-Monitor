import platform
import subprocess
import time
import json
import os
import re
from datetime import datetime

# devices.json sits at the project root (one level above this file)
DEVICES_FILE = os.path.join(os.path.dirname(__file__), "..", "devices.json")

DEFAULT_DEVICES = [
    {"name": "Google DNS",     "ip": "8.8.8.8"},
    {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
    {"name": "Local Router",   "ip": "192.168.1.1"},
]


def load_devices():
    """Return device list from devices.json, or defaults."""
    path = os.path.abspath(DEVICES_FILE)
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return list(DEFAULT_DEVICES)


def save_devices(devices):
    """Persist device list to devices.json."""
    path = os.path.abspath(DEVICES_FILE)
    with open(path, "w") as f:
        json.dump(devices, f, indent=2)


def _parse_rtt(output):
    """Extract average RTT (ms) from ping stdout. Returns int or None."""
    # Linux / macOS: "rtt min/avg/max/mdev = 10.1/12.3/14.5/1.0 ms"
    m = re.search(r'(?:rtt|round-trip)[^=]+=\s*[\d.]+/([\d.]+)', output)
    if m:
        return round(float(m.group(1)))
    # Windows: "Average = 12ms"
    m = re.search(r'Average\s*=\s*(\d+)\s*ms', output, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def ping_device(ip):
    """
    Ping ip once.
    Returns: ("ONLINE", response_ms:int) or ("OFFLINE", None)
    """
    is_windows = platform.system().lower() == "windows"
    # -n 1  (Windows)  /  -c 1 -W 1  (Linux/macOS)
    if is_windows:
        cmd = ["ping", "-n", "1", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]

    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
    except subprocess.TimeoutExpired:
        return "OFFLINE", None

    elapsed_ms = round((time.time() - start) * 1000)

    if result.returncode == 0:
        rtt = _parse_rtt(result.stdout)
        return "ONLINE", rtt if rtt is not None else elapsed_ms
    return "OFFLINE", None


def scan_devices():
    """
    Scan all devices. Returns list of dicts — kept for any legacy callers.
    """
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