from flask import Flask, render_template

import json
import subprocess
import platform
import time

from concurrent.futures import ThreadPoolExecutor

# Create Flask app
app = Flask(__name__)

# Detect OS
WINDOWS = platform.system().lower() == "windows"

# Load devices
with open("devices.json", "r") as file:
    devices = json.load(file)


# =========================
# PING FUNCTION
# =========================

def ping_device(device):

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

    return {
        "name": name,
        "ip": ip,
        "status": status,
        "response_time": response_time
    }


# =========================
# DASHBOARD ROUTE
# =========================

@app.route("/")
def dashboard():

    with ThreadPoolExecutor(max_workers=10) as executor:

        results = list(
            executor.map(
                ping_device,
                devices
            )
        )

    return render_template(
        "dashboard.html",
        results=results
    )


# =========================
# RUN FLASK SERVER
# =========================

if __name__ == "__main__":

    app.run(debug=True)