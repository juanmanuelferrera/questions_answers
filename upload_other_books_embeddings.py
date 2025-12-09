#!/usr/bin/env python3
"""
Upload embeddings for other individual books (NOI, SC, TLC, etc.) to Cloudflare Vectorize
These are the 21 smaller books that weren't included in the main SB upload
"""

import json
import requests
import os
import sys

# Vectorize endpoint
ACCOUNT_ID = "40035612bce74407c306499494965595"
INDEX_NAME = "philosophy-vectors"
VECTORIZE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{INDEX_NAME}/insert"

# Get API token from environment
API_TOKEN = os.environ.get('CLOUDFLARE_API_TOKEN')
if not API_TOKEN:
    print("ERROR: CLOUDFLARE_API_TOKEN environment variable not set")
    print("Set it with: export CLOUDFLARE_API_TOKEN='your-token'")
    sys.exit(1)

# Load embeddings
print("Loading embeddings from other_individual_embeddings_export.json...")
with open('other_individual_embeddings_export.json', 'r') as f:
    data = json.load(f)

chunks = data['chunks']
print(f"Total chunks to upload: {len(chunks)}")

# Convert to Vectorize format
vectors = []
for chunk in chunks:
    chunk_id = chunk['id']
    embedding = chunk['embedding']
    book_code = chunk.get('book_code', 'UNKNOWN')

    vector = {
        "id": f"vedabase_chunk_{chunk_id}",
        "values": embedding,
        "metadata": {
            "chunk_id": chunk_id,
            "source": "vedabase",
            "book_code": book_code
        }
    }
    vectors.append(vector)

print(f"\nConverted {len(vectors)} vectors")

# Upload in batches (Vectorize limit is typically 1000 per request)
BATCH_SIZE = 100
total_uploaded = 0
total_batches = (len(vectors) + BATCH_SIZE - 1) // BATCH_SIZE

print(f"\nUploading in {total_batches} batches of {BATCH_SIZE}...")

for i in range(0, len(vectors), BATCH_SIZE):
    batch = vectors[i:i + BATCH_SIZE]
    batch_num = (i // BATCH_SIZE) + 1

    payload = {
        "vectors": batch
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"Batch {batch_num}/{total_batches}: Uploading {len(batch)} vectors...", end=" ", flush=True)

    try:
        response = requests.post(VECTORIZE_URL, json=payload, headers=headers)

        if response.status_code == 200:
            total_uploaded += len(batch)
            print(f"✓ Success! ({total_uploaded}/{len(vectors)})")
        else:
            print(f"✗ Failed!")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

print(f"\n✅ Upload complete! {total_uploaded} vectors uploaded to Vectorize")
print("\nBooks included:")
book_counts = {}
for chunk in chunks:
    code = chunk.get('book_code', 'UNKNOWN')
    book_counts[code] = book_counts.get(code, 0) + 1

for code, count in sorted(book_counts.items()):
    print(f"  {code}: {count} chunks")
