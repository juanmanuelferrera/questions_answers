#!/usr/bin/env python3
"""
Retry failed Vectorize batches 15 and 16
"""
import json
import subprocess
import time
from pathlib import Path

EMBEDDINGS_FILE = "conversation_embeddings.json"
BATCH_SIZE = 500
INDEX_NAME = "philosophy-vectors"
FAILED_BATCHES = [15, 16]

def main():
    print("=" * 80)
    print(f"RETRYING FAILED VECTORIZE BATCHES: {FAILED_BATCHES}")
    print("=" * 80)

    # Load embeddings
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)

    total = len(embeddings)

    for batch_num in FAILED_BATCHES:
        start_idx = (batch_num - 1) * BATCH_SIZE
        end_idx = min(batch_num * BATCH_SIZE, total)
        batch = embeddings[start_idx:end_idx]

        print(f"\n[Batch {batch_num}] Uploading embeddings {start_idx+1}-{end_idx}...")

        # Create temp NDJSON
        batch_file = f"temp_retry_batch_{batch_num}.ndjson"
        with open(batch_file, 'w') as f:
            for item in batch:
                ndjson_item = {
                    "id": str(item['id']),
                    "values": item['embedding'],
                    "metadata": {
                        "source": "vedabase",
                        "book_code": "conversations",
                        "chunk_id": item['id'],
                        "chunk_type": item['chunk_type'],
                        "verse_id": item['verse_id']
                    }
                }
                f.write(json.dumps(ndjson_item) + '\n')

        # Upload with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    ['npx', 'wrangler', 'vectorize', 'upsert', INDEX_NAME,
                     '--file', batch_file],
                    capture_output=True,
                    text=True,
                    timeout=180
                )

                if result.returncode == 0:
                    print(f"✅ Batch {batch_num} uploaded successfully!")
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"⚠️  Retry {attempt + 1}/{max_retries}...")
                        time.sleep(5)
                    else:
                        print(f"❌ Batch {batch_num} failed after {max_retries} attempts")
                        print(f"Error: {result.stderr[:200]}")

            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️  Retry {attempt + 1}/{max_retries}...")
                    time.sleep(5)
                else:
                    print(f"❌ Batch {batch_num} failed: {str(e)[:100]}")

        Path(batch_file).unlink(missing_ok=True)
        time.sleep(2)

    print()
    print("=" * 80)
    print("RETRY COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()
