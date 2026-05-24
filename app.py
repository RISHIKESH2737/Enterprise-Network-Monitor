from datetime import datetime

from database import (
    initialize_database,
    save_results,
    fetch_history
)

from flask import (
    Flask,
    render_template
)

from flask_socketio import (
    SocketIO
)

import json
import subprocess
import platform
import time
import threading

from concurrent.futures import ThreadPoolExecutor

# =========================
# CREATE APP
# =========================

app = Flask(__name__)

socketio = SocketIO(app)

# =========================
# INITIALIZE DATABASE
# =========================

initialize_database()

# =========================
# DETECT OS
# =========================

WINDOWS = platform.system().lower() == "windows"

# =========================
# LOAD DEVICES
# =========================

with open("devices.json", "r") as file:

    devices = json.load(file)

# =========================
# PING DEVICE
# =========================

def ping_device(device):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    ip = device["ip"]

    name = device["name"]

    param = "-n" if WINDOWS else "-c"

    command = ["ping", param, "1", ip]

    start_time = time.time()

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    response_time = round(
        (time.time() - start_time) * 1000,
        2
    )

    if result.returncode == 0:

        status = "ONLINE"

    else:

        status = "OFFLINE"

        response_time = 0

    return {

        "name": name,
        "ip": ip,
        "status": status,
        "response_time": response_time,
        "timestamp": timestamp
    }

# =========================
# GENERATE RESULTS
# =========================

def generate_results():

    with ThreadPoolExecutor(
        max_workers=10
    ) as executor:

        results = list(
            executor.map(
                ping_device,
                devices
            )
        )

    total_devices = len(results)

    online_devices = len(
        [
            d for d in results
            if d["status"] == "ONLINE"
        ]
    )

    offline_devices = len(
        [
            d for d in results
            if d["status"] == "OFFLINE"
        ]
    )

    avg_response = round(

        sum(
            d["response_time"]
            for d in results
        ) / len(results),

        2
    )

    save_results(results)

    return {

        "results": results,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": offline_devices,
        "avg_response": avg_response
    }

# =========================
# LIVE BACKGROUND MONITOR
# =========================

def background_monitor():

    while True:

        data = generate_results()

        socketio.emit(
            "network_update",
            data
        )

        time.sleep(10)

# =========================
# START BACKGROUND THREAD
# =========================

thread = threading.Thread(
    target=background_monitor
)

thread.daemon = True

thread.start()

# =========================
# DASHBOARD ROUTE
# =========================

@app.route("/")
def dashboard():

    data = generate_results()

    return render_template(
        "dashboard.html",
        results=data["results"],
        total_devices=data["total_devices"],
        online_devices=data["online_devices"],
        offline_devices=data["offline_devices"],
        avg_response=data["avg_response"]
    )

# =========================
# ANALYTICS ROUTE
# =========================

@app.route("/analytics")
def analytics():

    history = fetch_history()

    return render_template(
        "analytics.html",
        history=history
    )

# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    socketio.run(
        app,
        debug=True
    )