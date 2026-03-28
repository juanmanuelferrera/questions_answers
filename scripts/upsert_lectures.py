#!/usr/bin/env python3
"""
Re-upload lecture vectors using UPSERT to replace existing ones with correct metadata
"""

import json
import subprocess
from pathlib import Path

print("="*80)
print("UPSERTING LECTURES WITH CORRECT METADATA")
print("="*80)
print("Note: UPSERT will replace any existing vectors with the same IDs\n")

# Load parsed lectures from lectures_export.json
print("Loading lecture data from lectures_export.json...")
with open('lectures_export.json', 'r') as f:
    lectures_data = json.load(f)

# Get chunks and verses
all_chunks = lectures_data['chunks']
verses = lectures_data['verses']

# Map book IDs to codes
book_id_to_code = {}
for book in lectures_data['books']:
    book_id_to_code[book['id']] = book['code']

# Map verse IDs to book IDs
verse_id_to_book_id = {}
for verse in verses:
    verse_id_to_book_id[verse['id']] = verse['book_id']

# Add book_code to each chunk (via verse_id -> book_id -> book_code)
for chunk in all_chunks:
    book_id = verse_id_to_book_id.get(chunk['verse_id'])
    chunk['book_code'] = book_id_to_code.get(book_id, 'OTHER')

print(f"Found {len(all_chunks)} lecture chunks total\n")

# Process in batches of 100
batch_size = 100
uploaded_count = 0

for i in range(0, len(all_chunks), batch_size):
    batch = all_chunks[i:i+batch_size]
    batch_num = (i // batch_size) + 1
    total_batches = (len(all_chunks) + batch_size - 1) // batch_size

    print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} chunks")

    # Generate embeddings
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
        vectors_data.append({
            'id': str(chunk['id']),
            'values': embedding,
            'metadata': {
                'chunk_id': chunk['id'],
                'verse_id': chunk['verse_id'],
                'chunk_type': 'lecture_content',
                'source': 'vedabase',  # Correct source for searching
                'book_code': chunk['book_code']  # For filtering
            }
        })

    # Save to temp NDJSON
    temp_file = Path('temp_vectors.ndjson')
    with open(temp_file, 'w') as f:
        for vector in vectors_data:
            f.write(json.dumps(vector) + '\n')

    # Upload using wrangler with UPSERT
    print("  Upserting to Vectorize...")

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
        print(f"  Progress: {uploaded_count}/{len(all_chunks)} ({100 * uploaded_count / len(all_chunks):.1f}%)\n")
    else:
        print(f"  ✗ Upsert failed for batch {batch_num}")
        print(f"  Error: {result.stderr}")
        print(f"  Stopping. Fix the issue and run again to resume.")
        exit(1)

print("\n" + "="*80)
print("COMPLETE!")
print("="*80)
print(f"Upserted: {uploaded_count} lecture vectors")
print("\nLecture embeddings now have CORRECT metadata:")
print("  - source: 'vedabase' (searchable with vedabase filter!)")
print("  - book_code: LEC1A, LEC1B, LEC2A, LEC2B, LEC2C, OTHER")
print("\nVectorize will index these within 5-30 minutes.")
print("The monitor script will detect when they're ready.")
print("="*80)
