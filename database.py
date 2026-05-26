import sqlite3

DATABASE_NAME = "network_monitor.db"

# =========================
# INITIALIZE DATABASE
# =========================

def initialize_database():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    # =========================
    # MONITORING LOGS
    # =========================

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
        DATABASE_NAME
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

def fetch_history(limit=100):

    conn = sqlite3.connect(
        DATABASE_NAME
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

# =========================
# DEVICE UPTIME STATS
# =========================

def get_device_uptime():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            name,
            ip,

            COUNT(*) as total_checks,

            SUM(
                CASE
                    WHEN status='ONLINE'
                    THEN 1
                    ELSE 0
                END
            ) as online_count,

            SUM(
                CASE
                    WHEN status='OFFLINE'
                    THEN 1
                    ELSE 0
                END
            ) as offline_count,

            AVG(response_time) as avg_response

        FROM monitoring_logs

        GROUP BY ip

    """)

    rows = cursor.fetchall()

    conn.close()

    results = []

    for row in rows:

        total = row[2]

        online = row[3]

        offline = row[4]

        uptime = 0

        if total > 0:

            uptime = round(

                (online / total) * 100,

                2

            )

        results.append({

            "name": row[0],

            "ip": row[1],

            "total_checks": total,

            "online_count": online,

            "offline_count": offline,

            "avg_response": round(
                row[5] or 0,
                2
            ),

            "uptime": uptime

        })

    return results

# =========================
# RESPONSE TIME CHART DATA
# =========================

def get_response_chart_data(limit=30):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            timestamp,
            response_time

        FROM monitoring_logs

        WHERE status='ONLINE'

        ORDER BY id DESC

        LIMIT ?

    """, (limit,))

    rows = cursor.fetchall()

    conn.close()

    rows.reverse()

    labels = [
        row[0]
        for row in rows
    ]

    values = [
        row[1]
        for row in rows
    ]

    return {

        "labels": labels,

        "values": values

    }

# =========================
# ONLINE vs OFFLINE STATS
# =========================

def get_status_distribution():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM monitoring_logs

        WHERE status='ONLINE'

    """)

    online = cursor.fetchone()[0]

    cursor.execute("""

        SELECT COUNT(*)

        FROM monitoring_logs

        WHERE status='OFFLINE'

    """)

    offline = cursor.fetchone()[0]

    conn.close()

    return {

        "online": online,

        "offline": offline

    }