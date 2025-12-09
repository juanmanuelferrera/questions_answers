#!/usr/bin/env python3
"""
Retry the failed Vectorize batch (batch 56: embeddings 27,500-28,000)
"""

import json
import subprocess
from pathlib import Path

EMBEDDINGS_FILE = "lecture_segments_embeddings.json"
FAILED_BATCH = 56
BATCH_SIZE = 500

def retry_batch():
    print("=" * 80)
    print("RETRYING FAILED VECTORIZE BATCH")
    print("=" * 80)
    print(f"\nBatch: {FAILED_BATCH}")
    print(f"Embeddings: {(FAILED_BATCH-1)*BATCH_SIZE} - {FAILED_BATCH*BATCH_SIZE}")
    print()

    # Load embeddings
    if not Path(EMBEDDINGS_FILE).exists():
        print(f"❌ Error: {EMBEDDINGS_FILE} not found")
        return

    print(f"📂 Loading embeddings from {EMBEDDINGS_FILE}...")
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)

    # Extract the failed batch
    start_idx = (FAILED_BATCH - 1) * BATCH_SIZE
    end_idx = FAILED_BATCH * BATCH_SIZE
    batch = embeddings[start_idx:end_idx]

    print(f"✅ Extracted {len(batch)} embeddings from batch {FAILED_BATCH}")

    # Create batch file
    batch_file = f"retry_batch_{FAILED_BATCH}.ndjson"
    with open(batch_file, 'w') as f:
        for embedding in batch:
            f.write(json.dumps(embedding) + '\n')

    print(f"📝 Created {batch_file}")

    # Upload using wrangler
    print(f"\n🔄 Uploading batch {FAILED_BATCH}...")
    try:
        result = subprocess.run(
            ['npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
             '--file', batch_file],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            print("✅ SUCCESS!")
            print(f"\nBatch {FAILED_BATCH} has been uploaded successfully")
            print(f"Embeddings {start_idx}-{end_idx} are now in Vectorize")
        else:
            print("❌ FAILED")
            print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("⏱️  TIMEOUT")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup
        Path(batch_file).unlink(missing_ok=True)

    print("\n" + "=" * 80)

if __name__ == '__main__':
    retry_batch()
