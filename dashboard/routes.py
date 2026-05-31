from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from dashboard.monitor import scan_devices
from database.db import db
import json, os

dashboard_bp = Blueprint("dashboard", __name__)

# Path for persisting devices (use a simple JSON file or swap for DB)
DEVICES_FILE = os.path.join(os.path.dirname(__file__), "devices.json")


def load_devices():
    if os.path.exists(DEVICES_FILE):
        with open(DEVICES_FILE) as f:
            return json.load(f)
    # Defaults
    return [
        {"name": "Google DNS",     "ip": "8.8.8.8"},
        {"name": "Cloudflare DNS", "ip": "1.1.1.1"},
        {"name": "Local Router",   "ip": "192.168.1.1"},
    ]


def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=2)


@dashboard_bp.route("/")
@login_required
def dashboard():
    from dashboard.monitor import ping_device
    from datetime import datetime

    devices = load_devices()
    results = []
    for d in devices:
        status = ping_device(d["ip"])
        results.append({
            "name": d["name"],
            "ip":   d["ip"],
            "status": status,
            "response_time": 12 if status == "ONLINE" else 0,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })

    total_devices   = len(results)
    online_devices  = sum(1 for d in results if d["status"] == "ONLINE")
    offline_devices = total_devices - online_devices
    online_times    = [d["response_time"] for d in results if d["status"] == "ONLINE"]
    avg_response    = round(sum(online_times) / len(online_times)) if online_times else 0

    return render_template(
        "index.html",
        results=results,
        total_devices=total_devices,
        online_devices=online_devices,
        offline_devices=offline_devices,
        avg_response=avg_response,
        username=current_user.username,
        user_role=current_user.role,
    )


@dashboard_bp.route("/add_device", methods=["POST"])
@login_required
def add_device():
    name = request.form.get("name", "").strip()
    ip   = request.form.get("ip",   "").strip()

    if not name or not ip:
        flash("Device name and IP are required.", "error")
        return redirect(url_for("dashboard.dashboard"))

    devices = load_devices()

    # Check for duplicate IP
    if any(d["ip"] == ip for d in devices):
        flash(f"A device with IP {ip} already exists.", "error")
        return redirect(url_for("dashboard.dashboard"))

    devices.append({"name": name, "ip": ip})
    save_devices(devices)

    flash(f"Device '{name}' added successfully.", "success")
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    # Fetch history from DB if you have a PingLog model,
    # otherwise pass empty list (replace with real query)
    history = []
    try:
        from database.models import PingLog
        history = PingLog.query.order_by(PingLog.id.desc()).limit(200).all()
        history = [(r.id, r.device_name, r.ip, r.status, r.response_time, r.timestamp)
                   for r in history]
    except Exception:
        pass

    return render_template(
        "analytics.html",
        history=history,
        username=getattr(current_user, "username", ""),
        user_role=getattr(current_user, "role", "viewer"),
    )


# ---- REST API ----

@dashboard_bp.route("/api/status")
@login_required
def api_status():
    from dashboard.monitor import ping_device
    from datetime import datetime
    devices = load_devices()
    results = []
    for d in devices:
        status = ping_device(d["ip"])
        results.append({
            "name":          d["name"],
            "ip":            d["ip"],
            "status":        status,
            "response_time": 12 if status == "ONLINE" else None,
            "timestamp":     datetime.now().isoformat(),
        })
    return jsonify(results)


@dashboard_bp.route("/api/devices")
@login_required
def api_devices():
    return jsonify(load_devices())


@dashboard_bp.route("/api/uptime")
@login_required
def api_uptime():
    from dashboard.monitor import ping_device
    devices = load_devices()
    results = []
    for d in devices:
        status = ping_device(d["ip"])
        results.append({
            "name":   d["name"],
            "ip":     d["ip"],
            "online": status == "ONLINE",
        })
    online = sum(1 for r in results if r["online"])
    pct    = round((online / len(results)) * 100) if results else 0
    return jsonify({"uptime_pct": pct, "devices": results})