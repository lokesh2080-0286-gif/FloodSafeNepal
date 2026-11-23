
import logging
import time

from app.database import initialize_database
from app.simulator import generate_all_nodes
from app.sync_manager import sync_pending_readings


logging.basicConfig(
    filename="logs/floodsafe.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

GENERATION_INTERVAL = 10
INITIAL_RETRY_DELAY = 5
MAX_RETRY_DELAY = 60


def main():
    initialize_database()

    retry_delay = INITIAL_RETRY_DELAY

    print("======================================")
    print(" FloodSafe Nepal Monitoring System")
    print("======================================")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            print("\nGenerating sensor readings...")

            try:
                readings = generate_all_nodes(contamination=False)

                logging.info(
                    "Generated %s sensor readings",
                    len(readings)
                )

            except Exception as error:
                logging.exception("Sensor generation failed: %s", error)

            print("\nSynchronizing pending readings...")

            try:
                completed = sync_pending_readings()

                if completed:
                    retry_delay = INITIAL_RETRY_DELAY
                    print("\nAll pending readings synchronized.")

                else:
                    print(f"\nRetrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                    continue

            except Exception as error:
                logging.exception("Synchronization error: %s", error)

                print(f"Synchronization unavailable: {error}")
                print(f"Retrying in {retry_delay} seconds...")

                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                continue

            print(f"\nNext collection in {GENERATION_INTERVAL} seconds.")
            time.sleep(GENERATION_INTERVAL)

    except KeyboardInterrupt:
        print("\nFloodSafe Nepal stopped safely.")


if __name__ == "__main__":
    main()

