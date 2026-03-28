#!/usr/bin/env python3
"""
Upload re-chunked embeddings with ultra-conservative settings
- Very small batches (100 embeddings)
- Very long timeout (5 minutes)
- Long pauses between batches (10 seconds)
"""

import json
import subprocess
import time
from pathlib import Path

def upload_embeddings(start_embedding=10000):
    """Upload with ultra-safe settings"""

    print("=" * 80)
    print("UPLOADING WITH ULTRA-SAFE SETTINGS")
    print(f"Starting from embedding {start_embedding}")
    print("Batch size: 100 | Timeout: 300s | Pause: 10s")
    print("=" * 80)

    # Load embeddings
    with open('rechunked_embeddings.json', 'r') as f:
        embeddings = json.load(f)

    embeddings = embeddings[start_embedding:]
    total_embeddings = len(embeddings)
    print(f"\nLoaded {total_embeddings} embeddings to upload")

    # Ultra-small batches
    batch_size = 100
    total_batches = (total_embeddings + batch_size - 1) // batch_size

    print(f"Uploading in {total_batches} batches of {batch_size}...")
    print(f"Estimated time: {total_batches * 15 / 60:.1f} minutes\n")

    successful_batches = 0

    for batch_idx in range(total_batches):
        i = batch_idx * batch_size
        batch = embeddings[i:i+batch_size]
        batch_num = batch_idx + 1
        global_embedding_num = start_embedding + i

        # Create batch file
        batch_file = f'temp_ultra_safe_{batch_num}.ndjson'
        with open(batch_file, 'w') as f:
            for embedding in batch:
                f.write(json.dumps(embedding) + '\n')

        print(f"[{batch_num}/{total_batches}] Uploading embeddings {global_embedding_num}-{global_embedding_num + len(batch)}...", end=" ", flush=True)

        # Single attempt with very long timeout
        try:
            result = subprocess.run([
                'npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
                '--file', batch_file
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout!

            if result.returncode == 0:
                print(f"✓ Success")
                successful_batches += 1
            else:
                print(f"✗ Failed")
                print(f"   Error: {result.stderr[:150]}")
                print(f"\n   Resume with: python3 upload_rechunked_ultra_safe.py {global_embedding_num}")
                Path(batch_file).unlink(missing_ok=True)
                return False

        except subprocess.TimeoutExpired:
            print(f"✗ Timeout after 5 minutes")
            print(f"   Resume with: python3 upload_rechunked_ultra_safe.py {global_embedding_num}")
            Path(batch_file).unlink(missing_ok=True)
            return False

        # Clean up
        Path(batch_file).unlink(missing_ok=True)

        # Long pause between batches
        if batch_num < total_batches:
            time.sleep(10)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE!")
    print("=" * 80)
    print(f"✓ {successful_batches} batches uploaded")
    print(f"✓ Embeddings {start_embedding}-{start_embedding + total_embeddings} in Vectorize")
    print("=" * 80)

    return True

if __name__ == '__main__':
    import sys
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    upload_embeddings(start)
