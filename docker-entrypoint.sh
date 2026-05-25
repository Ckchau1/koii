#!/bin/bash
# AIOS Docker Entrypoint Script
# Handles launching either the Electron browser or the FastAPI server based on environment

set -e

# Configuration
APP_HOME="/app"
LOG_DIR="/app/logs"

# Create necessary directories
mkdir -p "$LOG_DIR"

# Check if DISPLAY is set (indicates X11 forwarding for Electron)
if [ -z "$DISPLAY" ]; then
  echo "=================================================="
  echo "AIOS - Starting FastAPI Server"
  echo "=================================================="
  echo ""
  echo "No DISPLAY variable detected. Running in server mode."
  echo "Web UI available at: http://localhost:8000"
  echo ""
  echo "To use the browser UI:"
  echo "  1. Set DISPLAY environment variable for X11 forwarding"
  echo "  2. Or set LAUNCH_MODE=browser explicitly"
  echo ""
  echo "Starting FastAPI server..."
  echo ""

  # Run FastAPI server
  exec python -m uvicorn src.koii_os.api.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info

else
  echo "=================================================="
  echo "AIOS - Starting Electron Browser"
  echo "=================================================="
  echo "DISPLAY=$DISPLAY"
  echo ""

  # Ensure Xvfb is running if needed
  if [ "$USE_XVFB" == "true" ]; then
    echo "Starting Xvfb for virtual display..."
    Xvfb :99 -screen 0 1280x1024x24 > /dev/null 2>&1 &
    export DISPLAY=:99
  fi

  # Set up environment variables for LLM
  if [ -n "$KOII_LLM_API_URL" ]; then
    export KOII_LLM_API_URL="$KOII_LLM_API_URL"
    echo "LLM API URL: $KOII_LLM_API_URL"
  fi

  if [ -n "$KOII_LLM_API_KEY" ]; then
    echo "LLM API Key: [configured]"
  fi

  # Check if using browser development mode
  if [ "$DEV_MODE" == "true" ]; then
    echo "Running in development mode..."
    BROWSER_ARGS="--development-mode"
  else
    BROWSER_ARGS=""
  fi

  # Prepare to start Electron
  cd "$APP_HOME/src/koii_os/browser/core"

  echo ""
  echo "Starting Electron browser..."
  echo "Logs will be written to: $LOG_DIR/browser.log"
  echo ""

  # Start Electron
  electron . $BROWSER_ARGS >> "$LOG_DIR/browser.log" 2>&1 &
  ELECTRON_PID=$!

  # Optional: Also start the API server in background
  if [ "$START_API_SERVER" == "true" ]; then
    echo "Also starting FastAPI server on port 8000..."
    python -m uvicorn src.koii_os.api.server:app \
      --host 0.0.0.0 \
      --port 8000 \
      --log-level info \
      >> "$LOG_DIR/api.log" 2>&1 &
    API_PID=$!
  fi

  # Wait for Electron to exit
  wait $ELECTRON_PID 2>/dev/null || true

  # Kill API server if running
  if [ -n "$API_PID" ]; then
    kill $API_PID 2>/dev/null || true
  fi

  echo ""
  echo "Electron browser closed. Exiting."
fi
