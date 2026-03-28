#!/usr/bin/env python3
"""
Upload conversation embeddings to Cloudflare Vectorize
Uses the Vectorize HTTP API with batch upserts
"""

import json
import requests
import time
import os

EMBEDDINGS_FILE = "conversation_embeddings.json"
BATCH_SIZE = 100  # Vectorize batch limit
PAUSE_BETWEEN_BATCHES = 0.5

# Cloudflare API configuration
ACCOUNT_ID = "40035612bce74407c306499494965595"
VECTORIZE_INDEX_ID = "3e3b090d-245a-42b9-a77b-cef0fca9db31"
API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

def upload_batch(batch, batch_num):
    """Upload a batch of vectors to Vectorize"""

    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{VECTORIZE_INDEX_ID}/upsert"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format batch for Vectorize API
    vectors = []
    for item in batch:
        vectors.append({
            "id": str(item['id']),
            "values": item['embedding'],
            "metadata": {
                "source": "vedabase",
                "book_code": "conversations",
                "chunk_id": item['id'],
                "chunk_type": item['chunk_type'],
                "verse_id": item['verse_id']
            }
        })

    payload = {"vectors": vectors}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            return True, None
        else:
            return False, f"HTTP {response.status_code}: {response.text[:100]}"

    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:100]

def main():
    print("=" * 80)
    print("UPLOADING CONVERSATION EMBEDDINGS TO VECTORIZE")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s")
    print("=" * 80)
    print()

    # Check API token
    if not API_TOKEN:
        print("❌ CLOUDFLARE_API_TOKEN environment variable not set")
        print("   Run: export CLOUDFLARE_API_TOKEN='your-token'")
        return

    # Load embeddings
    print(f"📂 Loading embeddings from {EMBEDDINGS_FILE}...")
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)

    total_embeddings = len(embeddings)
    num_batches = (total_embeddings + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"✅ Loaded {total_embeddings:,} embeddings")
    print(f"📦 Will upload in {num_batches} batches")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_embeddings, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = embeddings[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_embeddings)

        print(f"[{batch_num}/{num_batches}] Uploading vectors {i+1}-{batch_end}...", end=" ", flush=True)

        success, error = upload_batch(batch, batch_num)

        if success:
            print("✅")
            success_count += len(batch)
        else:
            print(f"❌ {error}")
            failed_batches.append(batch_num)

        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

        # Progress update every 20 batches
        if batch_num % 20 == 0:
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
        print("🎉 Conversations are now fully searchable!")

if __name__ == '__main__':
    main()
