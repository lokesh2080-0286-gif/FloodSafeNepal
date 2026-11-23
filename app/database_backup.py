import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "floodsafe.db"


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


if __name__ == "__main__":
    initialize_database()
