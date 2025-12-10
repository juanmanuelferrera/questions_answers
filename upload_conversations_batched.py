#!/usr/bin/env python3
"""
Upload conversation embeddings to Vectorize in small batches using wrangler
Splits large NDJSON file into manageable chunks
"""

import json
import subprocess
import time
from pathlib import Path

EMBEDDINGS_FILE = "conversation_embeddings.json"
BATCH_SIZE = 100  # Very small batches to avoid API errors
PAUSE_BETWEEN_BATCHES = 3

def main():
    print("=" * 80)
    print("UPLOADING CONVERSATIONS TO VECTORIZE (BATCHED)")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s")
    print("=" * 80)
    print()

    # Load embeddings
    print(f"📂 Loading embeddings from {EMBEDDINGS_FILE}...")
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)

    total_embeddings = len(embeddings)
    num_batches = (total_embeddings + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"✅ Loaded {total_embeddings:,} embeddings")
    print(f"📦 Will upload in {num_batches} batches of {BATCH_SIZE}")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_embeddings, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = embeddings[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_embeddings)

        print(f"[{batch_num}/{num_batches}] Uploading vectors {i+1}-{batch_end}...", end=" ", flush=True)

        # Create temporary NDJSON file for this batch
        batch_file = f"temp_conv_batch_{batch_num}.ndjson"

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

        # Upload via wrangler
        try:
            result = subprocess.run(
                ['npx', 'wrangler', 'vectorize', 'upsert', 'lomasa-vectorize',
                 '--file', batch_file],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Clean up temp file
            Path(batch_file).unlink(missing_ok=True)

            if result.returncode == 0:
                print("✅")
                success_count += len(batch)
            else:
                error_msg = result.stderr[:100] if result.stderr else result.stdout[:100]
                print(f"❌ {error_msg}")
                failed_batches.append(batch_num)

        except subprocess.TimeoutExpired:
            Path(batch_file).unlink(missing_ok=True)
            print("❌ Timeout")
            failed_batches.append(batch_num)
        except Exception as e:
            Path(batch_file).unlink(missing_ok=True)
            print(f"❌ {str(e)[:50]}")
            failed_batches.append(batch_num)

        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

        # Progress update every 10 batches
        if batch_num % 10 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60 if elapsed > 0 else 0
            remaining = (num_batches - batch_num) / rate if rate > 0 else 0
            print(f"   Progress: {batch_num}/{num_batches} ({batch_num*100//num_batches}%) | Rate: {rate:.1f} batches/min | ETA: {remaining:.1f} min")

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("VECTORIZE UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Total embeddings: {total_embeddings:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//total_embeddings if total_embeddings > 0 else 0}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print(f"  Rate: {success_count/(elapsed/60) if elapsed > 0 else 0:.0f} vectors/min")
    print("=" * 80)

    if failed_batches:
        print()
        print(f"⚠️  Failed batches ({len(failed_batches)}): {failed_batches[:20]}")
    else:
        print()
        print("✅ All conversation embeddings uploaded to Vectorize!")
        print("🎉 Conversations are now fully searchable with semantic search!")

if __name__ == '__main__':
    main()
