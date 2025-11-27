#!/usr/bin/env python3
"""Monitor embedding generation progress"""
import time
import re
from pathlib import Path

PROGRESS_FILE = "vedabase_embedding_progress.json"
TARGET_CHUNKS = 19823

print("Monitoring embedding generation...")
print("=" * 70)

last_processed = 0
start_time = time.time()

while True:
    # Check progress file
    if Path(PROGRESS_FILE).exists():
        import json
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)

        processed = progress.get('total_processed', 0)

        if processed != last_processed:
            elapsed = time.time() - start_time
            percent = (processed / TARGET_CHUNKS) * 100
            remaining = TARGET_CHUNKS - processed

            if processed > last_processed and processed > 0:
                rate = processed / elapsed  # chunks per second
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60

                print(f"[{time.strftime('%H:%M:%S')}] Progress: {processed:,}/{TARGET_CHUNKS:,} ({percent:.1f}%) - ETA: {eta_minutes:.0f} min")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Progress: {processed:,}/{TARGET_CHUNKS:,} ({percent:.1f}%)")

            last_processed = processed

            if processed >= TARGET_CHUNKS:
                print("\n" + "=" * 70)
                print("✓ Embedding generation complete!")
                print(f"Total time: {elapsed/60:.1f} minutes")
                print("=" * 70)
                break

    time.sleep(30)  # Check every 30 seconds
