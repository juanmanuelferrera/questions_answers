#!/usr/bin/env python3
"""
Upload lecture_segment embeddings to Cloudflare Vectorize
Uses the Wrangler CLI with ultra-safe batching
"""

import json
import subprocess
import time
from pathlib import Path

EMBEDDINGS_FILE = "lecture_segments_embeddings.json"
BATCH_SIZE = 500  # Conservative batch size
PAUSE_BETWEEN_BATCHES = 10  # seconds
TIMEOUT = 300  # 5 minutes per batch

def upload_to_vectorize():
    """Upload embeddings to Vectorize in batches"""

    print("=" * 80)
    print("UPLOADING LECTURE SEGMENT EMBEDDINGS TO VECTORIZE")
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s | Timeout: {TIMEOUT}s")
    print("=" * 80)

    # Load embeddings
    if not Path(EMBEDDINGS_FILE).exists():
        print(f"❌ Error: {EMBEDDINGS_FILE} not found")
        print("   Run: python3 generate_lecture_segment_embeddings.py first")
        return

    print(f"\n📂 Loading embeddings from {EMBEDDINGS_FILE}...")
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)

    total_embeddings = len(embeddings)
    print(f"✅ Loaded {total_embeddings:,} embeddings")

    # Calculate batches
    num_batches = (total_embeddings + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"\n📦 Uploading in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Estimated time: {(num_batches * (PAUSE_BETWEEN_BATCHES + 10)) / 60:.1f} minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_embeddings, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = embeddings[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_embeddings)

        print(f"[{batch_num}/{num_batches}] Uploading embeddings {i}-{batch_end}...", end=" ", flush=True)

        # Create temporary batch file
        batch_file = f"temp_lecture_batch_{batch_num}.ndjson"
        with open(batch_file, 'w') as f:
            for embedding in batch:
                f.write(json.dumps(embedding) + '\n')

        # Upload using wrangler
        try:
            result = subprocess.run(
                ['npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors',
                 '--file', batch_file],
                capture_output=True,
                text=True,
                timeout=TIMEOUT
            )

            if result.returncode == 0:
                print("✅ Success")
                success_count += len(batch)
            else:
                print(f"❌ Failed")
                print(f"   Error: {result.stderr}")
                failed_batches.append(batch_num)

        except subprocess.TimeoutExpired:
            print(f"⏱️  Timeout")
            failed_batches.append(batch_num)
        except Exception as e:
            print(f"❌ Error: {e}")
            failed_batches.append(batch_num)
        finally:
            # Cleanup temp file
            Path(batch_file).unlink(missing_ok=True)

        # Pause between batches (except on last batch)
        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Total embeddings: {total_embeddings:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//total_embeddings}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches: {failed_batches}")
        print("   You may want to retry these specific batches")
    else:
        print("\n✅ All embeddings uploaded successfully!")
        print("\n📌 Next step:")
        print("   Run: python3 upload_lecture_segments_to_d1.py")

if __name__ == '__main__':
    upload_to_vectorize()
