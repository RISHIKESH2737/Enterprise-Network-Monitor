"""
scanner.py  —  Background monitoring thread
Pings all devices every SCAN_INTERVAL seconds and writes results to PingLog.
Start it once from app.py after the app is created.
"""

import threading
import time
from datetime import datetime

SCAN_INTERVAL = 60   # seconds between full scans


def _do_scan(app, socketio):
    """Run inside app context: ping all devices, save logs, emit SocketIO event."""
    from dashboard.monitor import load_devices, ping_device
    from database.models import PingLog
    from database.db import db

    with app.app_context():
        devices = load_devices()
        results = []

        for d in devices:
            status, response_time = ping_device(d["ip"])
            log = PingLog(
                device_name=d["name"],
                ip=d["ip"],
                status=status,
                response_time=response_time,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            db.session.add(log)
            results.append({
                "name":          d["name"],
                "ip":            d["ip"],
                "status":        status,
                "response_time": response_time,
                "timestamp":     datetime.now().strftime("%H:%M:%S"),
            })

        db.session.commit()

        # Broadcast live update to all connected browsers
        online  = sum(1 for r in results if r["status"] == "ONLINE")
        offline = len(results) - online
        times   = [r["response_time"] for r in results
                   if r["status"] == "ONLINE" and r["response_time"]]
        avg     = round(sum(times) / len(times)) if times else 0

        socketio.emit("scan_update", {
            "results":        results,
            "total_devices":  len(results),
            "online_devices": online,
            "offline_devices":offline,
            "avg_response":   avg,
        })


def _loop(app, socketio):
    while True:
        try:
            _do_scan(app, socketio)
        except Exception as e:
            print(f"[Scanner] Error: {e}")
        time.sleep(SCAN_INTERVAL)


def start_scanner(app, socketio):
    """
    Call once after create_app().
    Runs the first scan immediately in the background.
    """
    t = threading.Thread(target=_loop, args=(app, socketio), daemon=True)
    t.start()
    print(f"[Scanner] Background scanner started (interval={SCAN_INTERVAL}s)")