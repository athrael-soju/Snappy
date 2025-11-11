#!/bin/bash
set -e

# Start the FastAPI application in the background
echo "Starting DuckDB Analytics Service..."
python app.py &
APP_PID=$!

# Wait a bit for the DuckDB UI server to initialize
sleep 3

# Start socat to forward IPv4 connections on port 4213 to IPv6 localhost
# DuckDB UI binds to [::1]:4213 (IPv6 localhost only)
# This proxies IPv4 0.0.0.0:4213 -> [::1]:4213 for Docker port forwarding
echo "Starting IPv4 proxy for DuckDB UI..."
socat TCP4-LISTEN:42130,bind=0.0.0.0,fork,reuseaddr TCP6:[::1]:4213 &

echo "DuckDB service ready."
echo "  API: http://0.0.0.0:8300"
echo "  UI:  http://0.0.0.0:42130 (proxied to localhost:4213)"

# Wait for the FastAPI app to exit
wait $APP_PID
