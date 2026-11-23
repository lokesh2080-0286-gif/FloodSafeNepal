import logging

from app.database import get_connection
from app.mqtt_client import publish_telemetry

BATCH_SIZE = 50

logging.basicConfig(
    filename="logs/sync.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def get_pending_readings(limit=BATCH_SIZE):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT *
            FROM sensor_readings
            WHERE synced = 0
            ORDER BY timestamp ASC, id ASC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


def count_pending_readings():
    with get_connection() as conn:
        return conn.execute("""
            SELECT COUNT(*)
            FROM sensor_readings
            WHERE synced = 0
        """).fetchone()[0]


def mark_as_synced(reading_id):
    with get_connection() as conn:
        conn.execute("""
            UPDATE sensor_readings
            SET synced = 1
            WHERE id = ? AND synced = 0
        """, (reading_id,))


def sync_pending_readings():
    print("FloodSafe Nepal - SQLite to MQTT Batch Sync")
    print("-------------------------------------------")

    initial_pending = count_pending_readings()
    print(f"Pending readings: {initial_pending}")
    print(f"Batch size: {BATCH_SIZE}")

    successful = 0
    batch_number = 0
    failed = False

    while True:
        pending = get_pending_readings(BATCH_SIZE)

        if not pending:
            break

        batch_number += 1
        print(f"\nProcessing batch {batch_number}")
        print(f"Readings in this batch: {len(pending)}")

        for reading in pending:
            device_name = reading["device_name"]

            try:
                confirmed = publish_telemetry(device_name, reading)

                if not confirmed:
                    raise RuntimeError(
                        "MQTT delivery was not confirmed."
                    )

                mark_as_synced(reading["id"])
                successful += 1

                logging.info(
                    "Reading ID %s synced for %s",
                    reading["id"],
                    device_name
                )

                print(
                    f"Reading ID {reading['id']} successfully synced."
                )

            except Exception as error:
                logging.error(
                    "Sync failed for reading ID %s (%s): %s",
                    reading["id"],
                    device_name,
                    error
                )

                print(f"Sync failed for {device_name}: {error}")
                print("Remaining readings are stored locally.")

                failed = True
                break

        if failed:
            break

    remaining = count_pending_readings()

    print("\n-------------------------------------------")
    print(f"Total successfully synced: {successful}")
    print(f"Remaining pending: {remaining}")
    print(f"Batches processed: {batch_number}")

    logging.info(
        "Sync completed: successful=%s, pending=%s, batches=%s",
        successful,
        remaining,
        batch_number
    )

    return remaining == 0


if __name__ == "__main__":
    sync_pending_readings()
