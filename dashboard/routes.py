from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user
from dashboard.monitor import ping_device, load_devices, save_devices
from datetime import datetime
import csv, io

dashboard_bp = Blueprint("dashboard", __name__)


def _get_uptime(device_name, ip, days=7):
    """Return uptime % for a device over the last N days."""
    try:
        from database.models import PingLog
        from sqlalchemy import func
        total  = PingLog.query.filter_by(ip=ip).count()
        online = PingLog.query.filter_by(ip=ip, status="ONLINE").count()
        if total == 0:
            return None
        return round((online / total) * 100, 1)
    except Exception:
        return None


@dashboard_bp.route("/")
@login_required
def dashboard():
    devices = load_devices()
    results = []

    for d in devices:
        status, response_time = ping_device(d["ip"])
        results.append({
            "name":          d["name"],
            "ip":            d["ip"],
            "status":        status,
            "response_time": response_time if response_time is not None else 0,
            "timestamp":     datetime.now().strftime("%H:%M:%S"),
            "uptime":        _get_uptime(d["name"], d["ip"]),
        })

    total_devices   = len(results)
    online_devices  = sum(1 for d in results if d["status"] == "ONLINE")
    offline_devices = total_devices - online_devices
    online_times    = [d["response_time"] for d in results
                       if d["status"] == "ONLINE" and d["response_time"]]
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
    if any(d["ip"] == ip for d in devices):
        flash(f"A device with IP {ip} already exists.", "error")
        return redirect(url_for("dashboard.dashboard"))

    devices.append({"name": name, "ip": ip})
    save_devices(devices)
    flash(f"Device '{name}' added successfully.", "success")
    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/delete_device", methods=["POST"])
@login_required
def delete_device():
    ip = request.form.get("ip", "").strip()
    if not ip:
        flash("No IP provided.", "error")
        return redirect(url_for("dashboard.dashboard"))

    devices = load_devices()
    new_devices = [d for d in devices if d["ip"] != ip]

    if len(new_devices) == len(devices):
        flash("Device not found.", "error")
    else:
        save_devices(new_devices)
        flash("Device removed.", "success")

    return redirect(url_for("dashboard.dashboard"))


@dashboard_bp.route("/analytics")
@login_required
def analytics():
    history = []
    try:
        from database.models import PingLog
        rows = PingLog.query.order_by(PingLog.id.desc()).limit(500).all()
        history = [
            (r.id, r.device_name, r.ip, r.status, r.response_time, r.timestamp)
            for r in rows
        ]
    except Exception:
        pass

    return render_template(
        "analytics.html",
        history=history,
        username=current_user.username,
        user_role=current_user.role,
    )


@dashboard_bp.route("/export_csv")
@login_required
def export_csv():
    """Download all ping logs as a CSV file."""
    try:
        from database.models import PingLog
        rows = PingLog.query.order_by(PingLog.id.desc()).all()
    except Exception:
        rows = []

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["ID", "Device", "IP", "Status", "Response (ms)", "Timestamp"])
        for r in rows:
            writer.writerow([r.id, r.device_name, r.ip, r.status,
                             r.response_time or "", r.timestamp])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"network_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ── REST API ──────────────────────────────────────────────

@dashboard_bp.route("/api/status")
@login_required
def api_status():
    devices = load_devices()
    results = []
    for d in devices:
        status, response_time = ping_device(d["ip"])
        results.append({
            "name":          d["name"],
            "ip":            d["ip"],
            "status":        status,
            "response_time": response_time,
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
    devices = load_devices()
    results = []
    for d in devices:
        status, _ = ping_device(d["ip"])
        results.append({
            "name":   d["name"],
            "ip":     d["ip"],
            "online": status == "ONLINE",
            "uptime": _get_uptime(d["name"], d["ip"]),
        })
    online = sum(1 for r in results if r["online"])
    pct    = round((online / len(results)) * 100) if results else 0
    return jsonify({"uptime_pct": pct, "devices": results})