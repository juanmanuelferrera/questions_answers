#!/usr/bin/env python3
"""
Delete lecture vectors from Vectorize and re-upload with correct metadata
"""

import json
import subprocess
from pathlib import Path

# Step 1: Delete lecture vectors (IDs 19824-26863)
print("="*80)
print("DELETING OLD LECTURE VECTORS")
print("="*80)
print("Deleting vector IDs 19824-26863 from Vectorize...\n")

# Create list of IDs to delete
lecture_ids = [str(i) for i in range(19824, 26864)]  # 19824 to 26863 inclusive

# Split into batches of 1000 (Vectorize limit)
batch_size = 1000
total_deleted = 0

for i in range(0, len(lecture_ids), batch_size):
    batch = lecture_ids[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (len(lecture_ids) + batch_size - 1) // batch_size

    print(f"Deleting batch {batch_num}/{total_batches} ({len(batch)} vectors)...")

    # Create JSON array for the IDs
    ids_json = json.dumps(batch)

    result = subprocess.run(
        ['npx', 'wrangler', 'vectorize', 'delete-vectors', 'philosophy-vectors', '--ids', ids_json],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        total_deleted += len(batch)
        print(f"  ✓ Deleted {len(batch)} vectors")
        print(f"  Progress: {total_deleted}/{len(lecture_ids)}\n")
    else:
        print(f"  ✗ Failed to delete batch {batch_num}")
        print(f"  Error: {result.stderr}")
        print(f"  Note: This may be OK if vectors don't exist")
        print()

print(f"\n✓ Deletion complete: {total_deleted} vector IDs processed\n")

# Step 2: Re-upload with correct metadata using UPSERT
print("="*80)
print("RE-UPLOADING LECTURES WITH CORRECT METADATA")
print("="*80)
print("Loading lecture data...\n")

# Load parsed lectures
with open('vedabase_parsed.json', 'r') as f:
    data = json.load(f)

chunks = data['chunks']

# Filter to only lecture chunks (IDs 19824-26863)
lecture_chunks = [c for c in chunks if 19824 <= c['id'] <= 26863]
print(f"Found {len(lecture_chunks)} lecture chunks to upload\n")

# Process in batches of 100
batch_size = 100
uploaded_count = 0

for i in range(0, len(lecture_chunks), batch_size):
    batch = lecture_chunks[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (len(lecture_chunks) + batch_size - 1) // batch_size

    print(f"Batch {batch_num}/{total_batches}: Processing chunk IDs {batch[0]['id']} to {batch[-1]['id']} ({len(batch)} chunks)")

    # Generate embeddings and prepare vectors
    print("  Generating embeddings...")

    # Get texts for embedding
    texts = [chunk['content'] for chunk in batch]

    # Call OpenAI API
    import requests
    response = requests.post(
        'https://api.openai.com/v1/embeddings',
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer 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'
        },
        json={
            'model': 'text-embedding-3-small',
            'input': texts
        }
    )

    if response.status_code != 200:
        print(f"  ✗ OpenAI API error: {response.status_code}")
        print(f"  {response.text}")
        exit(1)

    embeddings_data = response.json()
    embeddings = [item['embedding'] for item in embeddings_data['data']]

    # Prepare vectors with correct metadata
    vectors_data = []
    for chunk, embedding in zip(batch, embeddings):
        # Get book code from chunk
        book_id = chunk['book_id']
        book_codes = {
            9: 'LEC1A', 10: 'LEC1B', 11: 'LEC1C',
            12: 'LEC2A', 13: 'LEC2B', 14: 'LEC2C', 15: 'OTHER'
        }
        book_code = book_codes.get(book_id, 'OTHER')

        vectors_data.append({
            'id': str(chunk['id']),
            'values': embedding,
            'metadata': {
                'chunk_id': chunk['id'],
                'verse_id': chunk['verse_id'],
                'chunk_type': 'lecture_content',
                'source': 'vedabase',  # Correct source
                'book_code': book_code  # Added for filtering
            }
        })

    # Save to temp NDJSON
    temp_file = Path('temp_vectors.ndjson')
    with open(temp_file, 'w') as f:
        for vector in vectors_data:
            f.write(json.dumps(vector) + '\n')

    # Upload using wrangler with UPSERT (not insert)
    print("  Uploading to Vectorize with UPSERT...")

    result = subprocess.run(
        ['npx', 'wrangler', 'vectorize', 'upsert', 'philosophy-vectors', '--file=temp_vectors.ndjson'],
        capture_output=True,
        text=True
    )

    # Clean up temp file
    try:
        temp_file.unlink()
    except FileNotFoundError:
        pass

    if result.returncode == 0:
        print(f"  ✓ Successfully upserted {len(batch)} vectors")
        uploaded_count += len(batch)
        print(f"  Progress: {uploaded_count}/{len(lecture_chunks)} ({100 * uploaded_count / len(lecture_chunks):.1f}%)\n")
    else:
        print(f"  ✗ Upsert failed for batch {batch_num}")
        print(f"  Error: {result.stderr}")
        print(f"  Stopping. Fix the issue and run again to resume.")
        exit(1)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"Deleted: {total_deleted} vector IDs")
print(f"Uploaded: {uploaded_count} vectors with correct metadata")
print("\nLecture embeddings now have:")
print("  - source: 'vedabase' (searchable!)")
print("  - book_code: LEC1A, LEC1B, etc. (filterable!)")
print("\nVectorize indexing will take 5-30 minutes.")
print("Monitor progress with: tail -f lecture_monitor_unbuffered.log")
print("="*80)
