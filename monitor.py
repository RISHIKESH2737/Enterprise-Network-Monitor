print("Script Started")

import time
import csv
import subprocess
import platform
import json
import os

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# Detect OS
WINDOWS = platform.system().lower() == "windows"
# Store previous device states
device_states = {}

# Create logs folder
os.makedirs("logs", exist_ok=True)
LOG_FILE = "logs/network_log.txt"
CSV_FILE = "logs/network_report.csv"

# Load devices from JSON
with open("devices.json", "r") as file:
    devices = json.load(file)
    print(devices)

# Ping function
def ping_device(device):

    ip = device["ip"]
    name = device["name"]

    param = "-n" if WINDOWS else "-c"

    command = ["ping", param, "1", ip]

    # Start timer
    start_time = time.time()

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Calculate response time
    response_time = round((time.time() - start_time) * 1000, 2)

    # Current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Determine status
    if result.returncode == 0:
        status = "ONLINE"
    else:
        status = "OFFLINE"

    return {
        "Device": name,
        "IP": ip,
        "Status": status,
        "Response Time": f"{response_time} ms",
        "Timestamp": timestamp
    }


# =========================
# WRITE LOG FILE
# =========================

def write_log(results):

    with open(LOG_FILE, "a") as file:

        for result in results:

            log_entry = (
                f"{result['Timestamp']} | "
                f"{result['Device']} | "
                f"{result['IP']} | "
                f"{result['Status']} | "
                f"{result['Response Time']}\n"
            )

            file.write(log_entry)
# =========================
# WRITE CSV REPORT
# =========================

def write_csv(results):

    file_exists = os.path.isfile(CSV_FILE)

    with open(CSV_FILE, "a", newline="") as csvfile:

        fieldnames = [
            "Device",
            "IP",
            "Status",
            "Response Time",
            "Timestamp"
        ]

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        # Write headers only once
        if not file_exists:
            writer.writeheader()

        writer.writerows(results)
# =========================
# CONTINUOUS MONITORING LOOP
# =========================

while True:

    # Multi-threaded device scanning
    with ThreadPoolExecutor(max_workers=10) as executor:

        results = list(
            executor.map(ping_device, devices)
        )

    # Clear terminal screen
    os.system("cls" if WINDOWS else "clear")

    # Dashboard title
    print("\n" + "=" * 60)
    print(Fore.CYAN + " ENTERPRISE NETWORK DEVICE MONITOR ")
    print("=" * 60)

    # Display professional table
    print(tabulate(
        results,
        headers="keys",
        tablefmt="grid"
    ))

    # Save logs
    write_log(results)

    # Save CSV report
    write_csv(results)

    print(Fore.GREEN + "\nLogs saved successfully.")

    # =========================
    # SMART ALERT SYSTEM
    # =========================

    for result in results:

        device_name = result["Device"]
        current_status = result["Status"]

        # Previous status
        previous_status = device_states.get(device_name)

        # Device went OFFLINE
        if previous_status == "ONLINE" and current_status == "OFFLINE":

            print(
                Fore.RED +
                "\n[ALERT] DEVICE OFFLINE: "
                f"{device_name} ({result['IP']})"
            )

        # Device recovered
        elif previous_status == "OFFLINE" and current_status == "ONLINE":

            print(
                Fore.GREEN +
                "\n[RECOVERY] DEVICE BACK ONLINE: "
                f"{device_name} ({result['IP']})"
            )

        # Save latest state
        device_states[device_name] = current_status

    print(Fore.YELLOW + "\nNext scan in 30 seconds...")

    # Wait before next scan
    time.sleep(30)