# FloodSafe Nepal

## Project Title

FloodSafe Nepal: Post-Flood Smart Water Quality Monitoring and Decision Support System

## Project Description

FloodSafe Nepal is an IoT-based water quality monitoring prototype. It uses Python virtual sensor nodes to generate water quality readings and sends telemetry to ThingsBoard Cloud using MQTT over TLS.

## Technologies Used

- Python 3
- SQLite
- MQTT (Paho MQTT)
- ThingsBoard Cloud
- Pytest

## Project Structure

- app/: Application source code
- data/: SQLite database
- logs/: Application logs
- tests/: Automated tests
- screenshots/: Implementation evidence

## Requirements

Python 3.10 or later.

## Installation

1. Create and activate a virtual environment.
2. Install dependencies:

   pip install -r requirements.txt

3. Create a .env file using .env.example.
4. Add your own ThingsBoard device access tokens to the .env file.

## Running the Project

Run the following commands:

   python -m app.simulator

   python -m app.sync_manager

Or use:

   ./run.sh

## Testing

Run:

   python -m pytest -v tests/test_offline_buffer.py

## Security Note

The actual .env file and device access tokens must not be shared in the submission ZIP or uploaded to GitHub.
