#!/bin/bash

cd "$(dirname "$0")"
source .venv/bin/activate

echo "Starting FloodSafe Nepal..."
echo "Generating sensor readings..."

python -m app.simulator

echo "Sending readings to ThingsBoard..."

python -m app.sync_manager

echo "FloodSafe Nepal run completed!"
