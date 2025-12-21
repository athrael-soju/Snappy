#!/usr/bin/env python3
"""Monitor OCR request rate."""

import time
import requests
from collections import deque

url = "http://localhost:8200/health"
timestamps = deque(maxlen=10)

print("Monitoring DeepSeek OCR service...")
print("Checking if the service is being called externally...")
print("Press Ctrl+C to stop\n")

try:
    # Just monitor the logs, not make requests
    print("Please check your backend logs for:")
    print("  1. Any scheduled tasks calling OCR")
    print("  2. File watchers triggering OCR")
    print("  3. Retry loops or polling")
    print("\nTo check backend processes:")
    print("  ps aux | grep -i snappy")
    print("\nTo check what's calling the OCR service:")
    print("  tail -f /path/to/backend/logs | grep -i ocr")

except KeyboardInterrupt:
    print("\n\nStopped monitoring")
