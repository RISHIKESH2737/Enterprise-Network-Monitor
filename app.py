from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for
)

from flask_socketio import SocketIO

from concurrent.futures import ThreadPoolExecutor

from datetime import datetime

from database import (
    initialize_database,
    save_results,
    fetch_history
)

import json
import subprocess
import platform
import threading
import time
import os

# =========================
# CREATE FLASK APP
# =========================

app = Flask(__name__)

app.config["SECRET_KEY"] = "network-monitor-secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

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
# SAVE DEVICES
# =========================

def save_devices():

    with open("devices.json", "w") as file:

        json.dump(
            devices,
            file,
            indent=4
        )

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

    command = [
        "ping",
        param,
        "1",
        ip
    ]

    start_time = time.time()

    try:

        result = subprocess.run(

            command,

            stdout=subprocess.PIPE,

            stderr=subprocess.PIPE,

            text=True,

            timeout=3

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

    except Exception:

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

    with ThreadPoolExecutor(max_workers=20) as executor:

        results = list(

            executor.map(

                ping_device,

                devices

            )

        )

    total_devices = len(results)

    online_devices = len([

        d for d in results

        if d["status"] == "ONLINE"

    ])

    offline_devices = len([

        d for d in results

        if d["status"] == "OFFLINE"

    ])

    online_response_times = [

        d["response_time"]

        for d in results

        if d["status"] == "ONLINE"

    ]

    if online_response_times:

        avg_response = round(

            sum(online_response_times)
            / len(online_response_times),

            2

        )

    else:

        avg_response = 0

    # SAVE TO DATABASE

    save_results(results)

    return {

        "results": results,

        "total_devices": total_devices,

        "online_devices": online_devices,

        "offline_devices": offline_devices,

        "avg_response": avg_response

    }

# =========================
# BACKGROUND MONITOR
# =========================

def background_monitor():

    while True:

        try:

            data = generate_results()

            socketio.emit(

                "network_update",

                data

            )

        except Exception as e:

            print("Background Error:", e)

        time.sleep(10)

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
# ANALYTICS PAGE
# =========================

@app.route("/analytics")
def analytics():

    history = fetch_history()

    return render_template(

        "analytics.html",

        history=history

    )

# =========================
# ADD DEVICE
# =========================

@app.route("/add_device", methods=["POST"])
def add_device():

    name = request.form.get("name")

    ip = request.form.get("ip")

    if name and ip:

        devices.append({

            "name": name,

            "ip": ip

        })

        save_devices()

    return redirect(url_for("dashboard"))

# =========================
# DELETE DEVICE
# =========================

@app.route("/delete_device/<ip>")
def delete_device(ip):

    global devices

    devices = [

        d for d in devices

        if d["ip"] != ip

    ]

    save_devices()

    return redirect(url_for("dashboard"))

# =========================
# START BACKGROUND THREAD
# =========================

def start_background_thread():

    monitor_thread = threading.Thread(

        target=background_monitor

    )

    monitor_thread.daemon = True

    monitor_thread.start()

# Prevent duplicate threads in Flask debug mode

if os.environ.get("WERKZEUG_RUN_MAIN") == "true":

    start_background_thread()

# =========================
# RUN APP
# =========================

if __name__ == "__main__":

    socketio.run(

        app,

        debug=True,

        host="0.0.0.0",

        port=5000

    )