
import random
import time

from datetime import datetime, timezone
from app.database import save_reading


# Three virtual monitoring nodes.
# Coordinates are illustrative, not actual sensor locations.

NODES = {
    "FloodSafe_Node_01": {
        "latitude": 27.95,
        "longitude": 85.30
    },
    "FloodSafe_Node_02": {
        "latitude": 27.98,
        "longitude": 85.32
    },
    "FloodSafe_Node_03": {
        "latitude": 28.01,
        "longitude": 85.34
    }
}


# Simulated environmental conditions.
SCENARIO_RANGES = {
    "normal": {
        "ph": (6.8, 7.6),
        "turbidity": (2, 8),
        "tds": (120, 250),
        "flow_rate": (8, 18)
    },

    "rise": {
        "ph": (6.5, 7.1),
        "turbidity": (10, 50),
        "tds": (220, 350),
        "flow_rate": (5, 12)
    },

    "peak": {
        "ph": (6.2, 6.7),
        "turbidity": (55, 120),
        "tds": (300, 450),
        "flow_rate": (3, 8)
    },

    "recovery": {
        "ph": (6.6, 7.3),
        "turbidity": (8, 25),
        "tds": (180, 300),
        "flow_rate": (7, 14)
    }
}


def generate_reading(device_name, contamination=False, stage=None):
    """Generate five simulated water-quality readings."""

    node = NODES[device_name]

    # Maintain compatibility with the previous contamination argument.
    if stage is None:
        stage = "peak" if contamination else "normal"

    if stage not in SCENARIO_RANGES:
        raise ValueError(f"Unknown scenario stage: {stage}")

    conditions = SCENARIO_RANGES[stage]

    ph = round(random.uniform(*conditions["ph"]), 2)

    turbidity = round(
        random.uniform(*conditions["turbidity"]), 2
    )

    tds = round(random.uniform(*conditions["tds"]), 2)

    temperature = round(random.uniform(16, 24), 2)

    flow_rate = round(
        random.uniform(*conditions["flow_rate"]), 2
    )

    return {
        "device_name": device_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ph": ph,
        "turbidity": turbidity,
        "tds": tds,
        "temperature": temperature,
        "flow_rate": flow_rate,
        "latitude": node["latitude"],
        "longitude": node["longitude"]
    }


def generate_all_nodes(contamination=False, stage=None):
    """Generate readings for all nodes and save them locally."""

    saved_readings = []

    if stage is None:
        stage = "peak" if contamination else "normal"

    print(f"\nScenario stage: {stage.upper()}")
    print("------------------------------------------")

    for device_name in NODES:

        reading = generate_reading(
            device_name,
            stage=stage
        )

        saved = save_reading(reading)

        if saved:
            saved_readings.append(reading)

            print(
                f'{device_name} | '
                f'pH: {reading["ph"]} | '
                f'Turbidity: {reading["turbidity"]} NTU | '
                f'TDS: {reading["tds"]} ppm | '
                f'Temperature: {reading["temperature"]} C | '
                f'Flow: {reading["flow_rate"]} L/min | SAVED'
            )

        else:
            print(
                f"{device_name} | "
                "Reading rejected: buffer full."
            )

    print(
        f"\nReadings saved: {len(saved_readings)} "
        f"out of {len(NODES)}"
    )

    return saved_readings


def run_contamination_scenario():
    """Simulate rainfall, contamination and recovery."""

    stages = ["normal", "rise", "peak", "recovery"]

    print("\nFloodSafe Nepal - Rainfall and Contamination Simulation")
    print("======================================================")

    for stage in stages:

        generate_all_nodes(stage=stage)

        if stage != "recovery":
            time.sleep(2)


if __name__ == "__main__":

    print("FloodSafe Nepal - Virtual Sensor Simulator")
    print("------------------------------------------")

    generate_all_nodes(stage="normal")

