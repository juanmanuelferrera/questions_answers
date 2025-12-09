#!/usr/bin/env python3
"""
Upload Srimad Bhagavatam Cantos 1-3 embeddings to Vectorize
With retry logic and resume capability
"""

import json
import subprocess
import time
from pathlib import Path

def upload_embeddings(start_batch=0):
    """Upload SB Cantos 1-3 embeddings to Vectorize"""

    print("=" * 80)
    print("UPLOADING SB CANTOS 1-3 EMBEDDINGS TO VECTORIZE")
    if start_batch > 0:
        print(f"RESUMING FROM BATCH {start_batch + 1}")
    print("=" * 80)

    # Load embeddings
    embeddings_file = 'sb_cantos_1_3_embeddings.json'
    print(f"\nLoading embeddings from {embeddings_file}...")

    with open(embeddings_file, 'r') as f:
        embeddings = json.load(f)

    total_embeddings = len(embeddings)
    print(f"Loaded {total_embeddings} embeddings")

    # Upload in batches
    batch_size = 1000
    total_batches = (total_embeddings + batch_size - 1) // batch_size

    print(f"\nUploading in {total_batches} batches of {batch_size}...")

    successful_batches = 0

    for batch_idx in range(start_batch, total_batches):
        i = batch_idx * batch_size
        batch = embeddings[i:i+batch_size]
        batch_num = batch_idx + 1

        # Create temporary batch file
        batch_file = f'temp_batch_{batch_num}.ndjson'
        with open(batch_file, 'w') as f:
            for embedding in batch:
                f.write(json.dumps(embedding) + '\n')

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Upload batch using wrangler
                result = subprocess.run([
                    'npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
                    '--file', batch_file
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    uploaded = min(i + batch_size, total_embeddings)
                    print(f"  ✓ Batch {batch_num}/{total_batches}: {uploaded}/{total_embeddings} embeddings")
                    successful_batches += 1
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  Batch {batch_num} failed (attempt {attempt + 1}/{max_retries}), retrying in 5s...")
                        time.sleep(5)
                    else:
                        print(f"  ✗ Batch {batch_num}/{total_batches} failed after {max_retries} attempts")
                        print(f"     Error: {result.stderr[:200]}")
                        # Clean up and save progress
                        Path(batch_file).unlink()
                        print(f"\n⚠️  Upload stopped. Resume with:")
                        print(f"     python3 upload_sb_1_3_embeddings_resume.py {batch_idx}")
                        return False
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Batch {batch_num} timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(5)
                else:
                    print(f"  ✗ Batch {batch_num} timed out after {max_retries} attempts")
                    Path(batch_file).unlink()
                    return False

        # Clean up temp file
        if Path(batch_file).exists():
            Path(batch_file).unlink()

        # Rate limiting - longer pause between batches
        time.sleep(2)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ {successful_batches} batches uploaded successfully")
    print(f"  ✓ {total_embeddings} embeddings uploaded to Vectorize")
    print("=" * 80)

    return True

if __name__ == '__main__':
    import sys
    start_batch = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    success = upload_embeddings(start_batch)
    if not success:
        exit(1)
