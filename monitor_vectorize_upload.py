#!/usr/bin/env python3
"""Monitor Vectorize upload progress"""
import time
import json
from pathlib import Path

PROGRESS_FILE = "vectorize_upload_progress.json"
TARGET_CHUNKS = 19823

print("Monitoring Vectorize upload...")
print("=" * 70)

last_uploaded = 0
start_time = time.time()

while True:
    # Check progress file
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)

        uploaded = progress.get('total_uploaded', 0)

        if uploaded != last_uploaded:
            elapsed = time.time() - start_time
            percent = (uploaded / TARGET_CHUNKS) * 100
            remaining = TARGET_CHUNKS - uploaded

            if uploaded > last_uploaded and uploaded > 0:
                rate = uploaded / elapsed  # chunks per second
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60

                print(f"[{time.strftime('%H:%M:%S')}] Uploaded: {uploaded:,}/{TARGET_CHUNKS:,} ({percent:.1f}%) - ETA: {eta_minutes:.0f} min")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Uploaded: {uploaded:,}/{TARGET_CHUNKS:,} ({percent:.1f}%)")

            last_uploaded = uploaded

            if uploaded >= TARGET_CHUNKS:
                print("\n" + "=" * 70)
                print("✓ Vectorize upload complete!")
                print(f"Total time: {elapsed/60:.1f} minutes")
                print("=" * 70)
                break

    time.sleep(30)  # Check every 30 seconds
