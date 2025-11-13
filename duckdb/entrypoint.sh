#!/bin/bash
set -e

# Forward SIGTERM and SIGINT to child processes for graceful shutdown
trap 'kill -TERM $APP_PID 2>/dev/null; kill -TERM $SOCAT_PID 2>/dev/null; wait' TERM INT

# Start the FastAPI application in the background
echo "Starting DuckDB Analytics Service..."
python main.py &
APP_PID=$!

# Wait a bit for the DuckDB UI server to initialize
sleep 3

# Start socat to forward IPv4 connections on port 4213 to IPv6 localhost
# DuckDB UI binds to [::1]:4213 (IPv6 localhost only)
# This proxies IPv4 0.0.0.0:4213 -> [::1]:4213 for Docker port forwarding
echo "Starting IPv4 proxy for DuckDB UI..."
socat TCP4-LISTEN:42130,bind=0.0.0.0,fork,reuseaddr TCP6:[::1]:4213 &
SOCAT_PID=$!

echo "DuckDB service ready."
echo "  API: http://0.0.0.0:8300"
echo "  UI:  http://0.0.0.0:42130 (proxied to localhost:4213)"

# Wait for the FastAPI app to exit and preserve its exit code
wait $APP_PID
EXIT_CODE=$?

# Clean up socat
kill -TERM $SOCAT_PID 2>/dev/null || true
wait $SOCAT_PID 2>/dev/null || true

exit $EXIT_CODE
