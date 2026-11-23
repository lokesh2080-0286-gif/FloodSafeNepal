
import json
import threading

import paho.mqtt.client as mqtt

from app.config import (
    THINGSBOARD_HOST,
    THINGSBOARD_PORT,
    DEVICES,
)


def publish_telemetry(device_name, reading):
    token = DEVICES.get(device_name)

    if not token:
        raise ValueError(f"No token configured for {device_name}")

    connected = threading.Event()
    connection_error = []

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"{device_name}_client"
    )

    client.username_pw_set(token)
    client.tls_set()

    def on_connect(client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"{device_name}: Connected to ThingsBoard.")
            connected.set()
        else:
            connection_error.append(str(reason_code))
            connected.set()

    client.on_connect = on_connect

    try:
        client.connect(THINGSBOARD_HOST, THINGSBOARD_PORT, 60)
        client.loop_start()

        if not connected.wait(timeout=15):
            raise TimeoutError("MQTT connection timed out.")

        if connection_error:
            raise ConnectionError(connection_error[0])

        payload = {
            "ts": int(
                __import__("datetime").datetime.fromisoformat(
                    reading["timestamp"]
                ).timestamp() * 1000
            ),
            "values": {
                "ph": reading["ph"],
                "turbidity": reading["turbidity"],
                "tds": reading["tds"],
                "temperature": reading["temperature"],
                "flow_rate": reading["flow_rate"]
            }
        }

        result = client.publish(
            "v1/devices/me/telemetry",
            json.dumps(payload),
            qos=1
        )

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Publish failed: {result.rc}")

        result.wait_for_publish(timeout=15)

        if not result.is_published():
            raise TimeoutError("Telemetry PUBACK was not confirmed.")

        print(f"{device_name}: Telemetry PUBACK confirmed.")
        return True

    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    print("FloodSafe Nepal - MQTT Connection Test")
    print("--------------------------------------")

    from app.database import get_connection

    with get_connection() as conn:
        row = conn.execute("""
            SELECT *
            FROM sensor_readings
            WHERE device_name = ?
            ORDER BY id DESC
            LIMIT 1
        """, ("FloodSafe_Node_01",)).fetchone()

    if row is None:
        raise RuntimeError("No saved reading found for Node 01.")

    reading = dict(row)

    publish_telemetry("FloodSafe_Node_01", reading)

