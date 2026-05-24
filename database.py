import sqlite3

# =========================
# INITIALIZE DATABASE
# =========================

def initialize_database():

    conn = sqlite3.connect(
        "network_monitor.db"
    )

    cursor = conn.cursor()

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS monitoring_logs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT,

            ip TEXT,

            status TEXT,

            response_time REAL,

            timestamp TEXT
        )

    """)

    conn.commit()

    conn.close()

# =========================
# SAVE RESULTS
# =========================

def save_results(results):

    conn = sqlite3.connect(
        "network_monitor.db"
    )

    cursor = conn.cursor()

    for device in results:

        cursor.execute("""

            INSERT INTO monitoring_logs (

                name,
                ip,
                status,
                response_time,
                timestamp

            )

            VALUES (?, ?, ?, ?, ?)

        """, (

            device["name"],
            device["ip"],
            device["status"],
            device["response_time"],
            device["timestamp"]

        ))

    conn.commit()

    conn.close()

# =========================
# FETCH HISTORY
# =========================

def fetch_history(limit=50):

    conn = sqlite3.connect(
        "network_monitor.db"
    )

    cursor = conn.cursor()

    cursor.execute("""

        SELECT *
        FROM monitoring_logs
        ORDER BY id DESC
        LIMIT ?

    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    return rows