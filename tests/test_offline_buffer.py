import sqlite3

from app import database
from app import sync_manager


def test_reading_remains_pending_when_mqtt_fails(tmp_path, monkeypatch):
    # Use a separate temporary database for this test
    test_db = tmp_path / "test_floodsafe.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    # Create the database table
    database.initialize_database()

    # Insert one unsynced sensor reading
    with database.get_connection() as conn:
        conn.execute("""
            INSERT INTO sensor_readings (
                device_name, timestamp, ph, turbidity,
                tds, temperature, flow_rate, synced
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "FloodSafe_Node_01",
            "2026-11-17T03:00:00",
            7.2,
            5.0,
            180.0,
            21.0,
            12.0,
            0
        ))

    # Simulate an MQTT publishing failure
    def simulate_mqtt_failure(device_name, reading):
        raise OSError("Simulated MQTT connection failure")

    monkeypatch.setattr(
        sync_manager,
        "publish_telemetry",
        simulate_mqtt_failure
    )

    # Attempt synchronization
    result = sync_manager.sync_pending_readings()

    # Verify the reading remains safely stored and unsynced
    with database.get_connection() as conn:
        row = conn.execute("""
            SELECT synced
            FROM sensor_readings
        """).fetchone()

    assert result is False
    assert row["synced"] == 0

    print("PASS: Reading remains stored when MQTT publishing fails.")


def test_reading_is_marked_synced_after_mqtt_success(tmp_path, monkeypatch):
    # Use a separate temporary database
    test_db = tmp_path / "test_success.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    database.initialize_database()

    # Insert one pending reading
    with database.get_connection() as conn:
        conn.execute("""
            INSERT INTO sensor_readings (
                device_name, timestamp, ph, turbidity,
                tds, temperature, flow_rate, synced
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "FloodSafe_Node_01",
            "2026-11-17T03:10:00",
            7.2,
            5.0,
            180.0,
            21.0,
            12.0,
            0
        ))

    # Simulate successful MQTT delivery and PUBACK confirmation
    def simulate_mqtt_success(device_name, reading):
        return True

    monkeypatch.setattr(
        sync_manager,
        "publish_telemetry",
        simulate_mqtt_success
    )

    result = sync_manager.sync_pending_readings()

    # Verify that the reading is now marked as synced
    with database.get_connection() as conn:
        row = conn.execute("""
            SELECT synced
            FROM sensor_readings
        """).fetchone()

    assert result is True
    assert row["synced"] == 1

    print("PASS: Reading marked as synced after MQTT confirmation.")


def test_pending_readings_are_limited_to_batch_size(tmp_path, monkeypatch):
    test_db = tmp_path / "test_batch.db"
    monkeypatch.setattr(database, "DB_PATH", test_db)

    database.initialize_database()

    # Insert 60 pending readings
    with database.get_connection() as conn:
        for i in range(60):
            conn.execute("""
                INSERT INTO sensor_readings (
                    device_name, timestamp, ph, turbidity,
                    tds, temperature, flow_rate, synced
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                "FloodSafe_Node_01",
                "2026-11-17T03:00:00",
                7.2, 5.0, 180.0, 21.0, 12.0
            ))

    # Fetch one batch
    batch = sync_manager.get_pending_readings()

    assert len(batch) == 50
    assert [r["id"] for r in batch] == sorted(
        r["id"] for r in batch
    )

    print("PASS: Batch contains exactly 50 readings in chronological order.")


def test_full_buffer_rejects_new_readings(tmp_path, monkeypatch):
    test_db = tmp_path / "test_buffer_limit.db"

    monkeypatch.setattr(database, "DB_PATH", test_db)
    monkeypatch.setattr(database, "MAX_PENDING_READINGS", 2)

    database.initialize_database()

    def create_reading(timestamp):
        return {
            "device_name": "FloodSafe_Node_01",
            "timestamp": timestamp,
            "ph": 7.2,
            "turbidity": 5.0,
            "tds": 180.0,
            "temperature": 21.0,
            "flow_rate": 12.0
        }

    # First two readings should be accepted
    assert database.save_reading(create_reading("2026-11-17T03:00:00"))
    assert database.save_reading(create_reading("2026-11-17T03:01:00"))

    # Third reading should be rejected
    assert not database.save_reading(create_reading("2026-11-17T03:02:00"))

    with database.get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM sensor_readings"
        ).fetchone()[0]

        pending = conn.execute(
            "SELECT COUNT(*) FROM sensor_readings WHERE synced = 0"
        ).fetchone()[0]

    assert total == 2
    assert pending == 2

    print("PASS: Full buffer rejects new readings without deleting old ones.")
