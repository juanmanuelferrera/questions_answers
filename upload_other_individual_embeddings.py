#!/usr/bin/env python3
"""
Upload individual OTHER books embeddings to Cloudflare Vectorize
"""

import json
import subprocess
from pathlib import Path

def upload_embeddings():
    """Upload embeddings to Vectorize in batches"""

    embeddings_file = 'other_individual_embeddings_export.json'
    if not Path(embeddings_file).exists():
        print(f"Error: {embeddings_file} not found")
        return

    print("=" * 80)
    print("UPLOADING INDIVIDUAL OTHER BOOKS EMBEDDINGS TO VECTORIZE")
    print("=" * 80)

    with open(embeddings_file, 'r') as f:
        data = json.load(f)

    chunks = data['chunks']
    print(f"\nLoaded {len(chunks)} embeddings")

    # Upload in batches of 100
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    print(f"\nUploading to Vectorize in batches of {batch_size}...")
    print(f"Total batches: {total_batches}\n")

    uploaded_count = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        # Prepare NDJSON format for Vectorize
        vectors_data = []
        for chunk in batch:
            vectors_data.append({
                'id': str(chunk['id']),
                'values': chunk['embedding'],
                'metadata': {
                    'chunk_id': chunk['id'],
                    'verse_id': chunk['verse_id'],
                    'chunk_type': chunk['chunk_type'],
                    'source': 'vedabase',
                    'book_code': chunk['book_code']
                }
            })

        # Write to NDJSON file
        ndjson_file = 'temp_vectors.ndjson'
        with open(ndjson_file, 'w') as f:
            for vec in vectors_data:
                f.write(json.dumps(vec) + '\n')

        # Upload using wrangler vectorize upsert
        result = subprocess.run(
            ['npx', 'wrangler', 'vectorize', 'upsert', 'philosophy-vectors',
             f'--file={ndjson_file}'],
            capture_output=True,
            text=True
        )

        # Clean up temp file
        Path(ndjson_file).unlink()

        if result.returncode == 0:
            uploaded_count += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: ✓ Uploaded {len(batch)} vectors ({uploaded_count}/{len(chunks)} total)")
        else:
            print(f"  Batch {batch_num}/{total_batches}: ✗ Failed")
            print(f"  Error: {result.stderr[:200]}")
            return

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  Total embeddings uploaded: {uploaded_count}")
    print(f"  Vectorize will index these within 5-30 minutes")
    print("=" * 80)

if __name__ == '__main__':
    upload_embeddings()
