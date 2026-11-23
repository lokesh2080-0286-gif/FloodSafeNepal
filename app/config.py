import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env", override=True)

# ThingsBoard connection settings
THINGSBOARD_HOST = os.getenv(
    "THINGSBOARD_HOST",
    "demo.thingsboard.io"
)

THINGSBOARD_PORT = int(
    os.getenv("THINGSBOARD_PORT", "8883")
)

# Device access tokens
DEVICES = {
    "FloodSafe_Node_01": os.getenv("NODE_01_TOKEN"),
    "FloodSafe_Node_02": os.getenv("NODE_02_TOKEN"),
    "FloodSafe_Node_03": os.getenv("NODE_03_TOKEN"),
}


def validate_config():
    """Check configuration without displaying secret tokens."""

    missing = [
        device for device, token in DEVICES.items()
        if not token or not token.strip()
    ]

    if missing:
        raise ValueError(
            f"Missing access tokens for: {', '.join(missing)}"
        )

    print("ThingsBoard configuration loaded successfully.")
    print(f"Host: {THINGSBOARD_HOST}")
    print(f"Port: {THINGSBOARD_PORT}")
    print(f"Configured devices: {len(DEVICES)}")


if __name__ == "__main__":
    validate_config()
