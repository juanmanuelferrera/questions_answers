#!/usr/bin/env python3
"""
Upload re-chunked embeddings to Vectorize with smaller batches (500)
Resume from batch 11 (starting at embedding 10,000)
"""

import json
import subprocess
import time
from pathlib import Path

def upload_embeddings(start_embedding=10000):
    """Upload re-chunked embeddings in smaller batches"""

    print("=" * 80)
    print("UPLOADING RE-CHUNKED EMBEDDINGS TO VECTORIZE (SMALL BATCHES)")
    print(f"STARTING FROM EMBEDDING {start_embedding}")
    print("=" * 80)

    # Load embeddings
    embeddings_file = 'rechunked_embeddings.json'
    print(f"\nLoading embeddings from {embeddings_file}...")

    with open(embeddings_file, 'r') as f:
        embeddings = json.load(f)

    # Start from specified embedding
    embeddings = embeddings[start_embedding:]
    total_embeddings = len(embeddings)
    print(f"Loaded {total_embeddings} embeddings (starting from {start_embedding})")

    # Upload in smaller batches (500 instead of 1000)
    batch_size = 500
    total_batches = (total_embeddings + batch_size - 1) // batch_size

    print(f"\nUploading in {total_batches} batches of {batch_size}...")

    successful_batches = 0

    for batch_idx in range(total_batches):
        i = batch_idx * batch_size
        batch = embeddings[i:i+batch_size]
        batch_num = batch_idx + 1
        global_embedding_num = start_embedding + i

        # Create temporary batch file
        batch_file = f'temp_batch_small_{batch_num}.ndjson'
        with open(batch_file, 'w') as f:
            for embedding in batch:
                f.write(json.dumps(embedding) + '\n')

        # Retry logic with longer timeout
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Upload batch using wrangler with longer timeout
                result = subprocess.run([
                    'npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
                    '--file', batch_file
                ], capture_output=True, text=True, timeout=120)  # 2 minute timeout

                if result.returncode == 0:
                    uploaded = global_embedding_num + len(batch)
                    print(f"  ✓ Batch {batch_num}/{total_batches}: Embedding {uploaded} (batch size: {len(batch)})")
                    successful_batches += 1
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  Batch {batch_num} failed (attempt {attempt + 1}/{max_retries}), retrying in 10s...")
                        time.sleep(10)
                    else:
                        print(f"  ✗ Batch {batch_num} failed after {max_retries} attempts")
                        print(f"     Resume with: python3 upload_rechunked_small_batches.py {global_embedding_num}")
                        # Clean up and save progress
                        Path(batch_file).unlink(missing_ok=True)
                        return False
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Batch {batch_num} timeout (attempt {attempt + 1}/{max_retries}), retrying in 10s...")
                    time.sleep(10)
                else:
                    print(f"  ✗ Batch {batch_num} timed out after {max_retries} attempts")
                    print(f"     Resume with: python3 upload_rechunked_small_batches.py {global_embedding_num}")
                    Path(batch_file).unlink(missing_ok=True)
                    return False

        # Clean up temp file
        if Path(batch_file).exists():
            Path(batch_file).unlink()

        # Longer pause between batches to avoid rate limiting
        time.sleep(3)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ {successful_batches} batches uploaded successfully")
    print(f"  ✓ Embeddings {start_embedding} to {start_embedding + total_embeddings} uploaded")
    print("=" * 80)

    return True

if __name__ == '__main__':
    import sys
    start_embedding = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
    success = upload_embeddings(start_embedding)
    if not success:
        exit(1)
