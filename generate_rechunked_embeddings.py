#!/usr/bin/env python3
"""
Generate embeddings for newly created purport_segment chunks
"""

import os
import json
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
OUTPUT_FILE = "rechunked_embeddings.json"

def generate_embeddings():
    """Generate embeddings for purport_segment chunks"""

    print("=" * 80)
    print("GENERATING EMBEDDINGS FOR RE-CHUNKED PURPORTS")
    print("=" * 80)

    # Connect to database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get only purport_segment chunks (the newly created ones)
    cursor.execute("""
        SELECT c.id, c.content, b.code, v.chapter, v.verse_number
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE c.chunk_type = 'purport_segment'
        ORDER BY c.id
    """)

    chunks = cursor.fetchall()
    total_chunks = len(chunks)

    print(f"\nFound {total_chunks} purport_segment chunks")
    print(f"Estimated cost: ${total_chunks * 0.00001:.2f}")

    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    embeddings_data = []
    batch_size = 100
    total_batches = (total_chunks + batch_size - 1) // batch_size

    print(f"\nProcessing in {total_batches} batches of {batch_size}...")

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch = chunks[start_idx:end_idx]

        # Prepare texts for embedding
        texts = [chunk[1] for chunk in batch]  # content

        # Generate embeddings
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            dimensions=1536
        )

        # Store embeddings with metadata
        for j, chunk in enumerate(batch):
            chunk_id, content, book_code, chapter, verse_number = chunk

            embeddings_data.append({
                'id': f"vedabase_chunk_{chunk_id}",
                'values': response.data[j].embedding,
                'metadata': {
                    'source': 'vedabase',
                    'chunk_id': chunk_id,
                    'book_code': book_code,
                    'chapter': chapter,
                    'verse_number': verse_number,
                    'chunk_type': 'purport_segment'
                }
            })

        print(f"  Batch {batch_idx + 1}/{total_batches}: {end_idx}/{total_chunks} embeddings")

        # Rate limiting
        time.sleep(0.5)

    # Save embeddings
    print(f"\nSaving embeddings to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(embeddings_data, f)

    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 80)
    print(f"  ✓ {total_chunks} embeddings generated")
    print(f"  ✓ Saved to {OUTPUT_FILE} ({file_size_mb:.2f} MB)")
    print(f"  ✓ Ready to upload to Vectorize")
    print("=" * 80)

    conn.close()

if __name__ == '__main__':
    generate_embeddings()
