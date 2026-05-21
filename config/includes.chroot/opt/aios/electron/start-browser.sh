#!/bin/bash
# Koii AI Browser Launcher Script

set -e

# Set environment variables
export AIOS_DATA_DIR="${AIOS_DATA_DIR:-/var/lib/aios/data}"
export ELECTRON_ENABLE_LOGGING=1
export DISPLAY="${DISPLAY:-:0}"

# Change to electron directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing browser dependencies..."
    npm install --production
fi

# Start the Electron browser
exec npm start

# Made with Bob
