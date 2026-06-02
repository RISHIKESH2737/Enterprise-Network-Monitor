"""
scanner.py — Background monitoring thread
Pings all devices every SCAN_INTERVAL seconds, saves to PingLog, emits SocketIO update.
"""
import threading
import time
from datetime import datetime

SCAN_INTERVAL = 60  # seconds


def _do_scan(app, socketio):
    from dashboard.monitor import load_devices, ping_device
    from database.models import PingLog
    from database.db import db

    with app.app_context():
        # FIX: ensure tables exist before any INSERT (handles hot-reload race)
        db.create_all()

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
                "response_time": response_time if response_time else 0,
                "timestamp":     datetime.now().strftime("%H:%M:%S"),
            })

        db.session.commit()

        online  = sum(1 for r in results if r["status"] == "ONLINE")
        offline = len(results) - online
        times   = [r["response_time"] for r in results
                   if r["status"] == "ONLINE" and r["response_time"]]
        avg     = round(sum(times) / len(times)) if times else 0

        socketio.emit("scan_update", {
            "results":         results,
            "total_devices":   len(results),
            "online_devices":  online,
            "offline_devices": offline,
            "avg_response":    avg,
        })


def _loop(app, socketio):
    # FIX: wait 2 seconds before first scan so Flask fully starts
    time.sleep(2)
    while True:
        try:
            _do_scan(app, socketio)
        except Exception as e:
            print(f"[Scanner] Error: {e}")
        time.sleep(SCAN_INTERVAL)


def start_scanner(app, socketio):
    t = threading.Thread(target=_loop, args=(app, socketio), daemon=True)
    t.start()
    print(f"[Scanner] Background scanner started (interval={SCAN_INTERVAL}s)")