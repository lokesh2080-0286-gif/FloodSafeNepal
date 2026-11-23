import logging
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "floodsafe.db"

MAX_PENDING_READINGS = 10000

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "database.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")

    return connection


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ph REAL NOT NULL,
                turbidity REAL NOT NULL,
                tds REAL NOT NULL,
                temperature REAL NOT NULL,
                flow_rate REAL NOT NULL,
                synced INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_sync
            ON sensor_readings(synced, timestamp)
        """)

    print("SQLite database initialized successfully.")
    print(f"Database location: {DB_PATH}")


def save_reading(reading):
    """Save a reading only if the pending buffer has capacity."""

    with get_connection() as conn:
        # Lock the database for a safe capacity check and insert.
        conn.execute("BEGIN IMMEDIATE")

        pending = conn.execute("""
            SELECT COUNT(*)
            FROM sensor_readings
            WHERE synced = 0
        """).fetchone()[0]

        if pending >= MAX_PENDING_READINGS:
            logging.warning(
                "Buffer full: rejected new reading from %s. "
                "Pending readings: %s, maximum: %s",
                reading["device_name"],
                pending,
                MAX_PENDING_READINGS
            )

            print(
                f"WARNING: Buffer full. Reading from "
                f"{reading['device_name']} was not saved."
            )

            return False

        conn.execute("""
            INSERT INTO sensor_readings (
                device_name,
                timestamp,
                ph,
                turbidity,
                tds,
                temperature,
                flow_rate
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            reading["device_name"],
            reading["timestamp"],
            reading["ph"],
            reading["turbidity"],
            reading["tds"],
            reading["temperature"],
            reading["flow_rate"]
        ))

        logging.info(
            "Reading saved for %s. Pending before insert: %s",
            reading["device_name"],
            pending
        )

        return True


if __name__ == "__main__":
    initialize_database()
