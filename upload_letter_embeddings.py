#!/usr/bin/env python3
"""
Upload letter embeddings to Cloudflare Vectorize
"""

import json
import subprocess
import time
from pathlib import Path

def upload_embeddings():
    """Upload letter embeddings to Vectorize"""

    print("=" * 80)
    print("UPLOADING LETTER EMBEDDINGS TO VECTORIZE")
    print("=" * 80)

    # Load embeddings
    embeddings_file = 'letter_embeddings_for_upload.json'
    print(f"\nLoading embeddings from {embeddings_file}...")

    with open(embeddings_file, 'r') as f:
        embeddings = json.load(f)

    total_embeddings = len(embeddings)
    print(f"Loaded {total_embeddings} embeddings")

    # Upload in batches
    batch_size = 1000
    total_batches = (total_embeddings + batch_size - 1) // batch_size

    print(f"\nUploading in {total_batches} batches of {batch_size}...")

    for i in range(0, total_embeddings, batch_size):
        batch = embeddings[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        # Create temporary batch file
        batch_file = f'temp_batch_{batch_num}.ndjson'
        with open(batch_file, 'w') as f:
            for embedding in batch:
                f.write(json.dumps(embedding) + '\n')

        # Upload batch using wrangler
        result = subprocess.run([
            'npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
            '--file', batch_file
        ], capture_output=True, text=True)

        # Clean up temp file
        Path(batch_file).unlink()

        if result.returncode != 0:
            print(f"  ✗ Batch {batch_num}/{total_batches} failed: {result.stderr}")
            return False

        uploaded = min(i + batch_size, total_embeddings)
        print(f"  ✓ Batch {batch_num}/{total_batches}: {uploaded}/{total_embeddings} embeddings")

        # Rate limiting
        time.sleep(0.5)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ {total_embeddings} embeddings uploaded to Vectorize")
    print("=" * 80)

    return True

if __name__ == '__main__':
    success = upload_embeddings()
    if not success:
        exit(1)
