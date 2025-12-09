#!/usr/bin/env python3
"""
Generate embeddings for Srimad Bhagavatam Cantos 4-10 chunks
"""

import json
import sqlite3
import os
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def generate_embeddings():
    """Generate embeddings for Srimad Bhagavatam Cantos 4-10 chunks"""

    print("=" * 80)
    print("GENERATING EMBEDDINGS FOR SRIMAD BHAGAVATAM CANTOS 4-10")
    print("=" * 80)

    # Load environment variables from .env file
    load_dotenv()

    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please ensure .env file exists with OPENAI_API_KEY")
        return

    client = OpenAI(api_key=api_key)

    # Connect to database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get all chunks for Cantos 4-10
    cursor.execute("""
        SELECT c.id, c.verse_id, c.chunk_type, c.content,
               v.chapter, v.verse_number, b.code, b.name
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE b.code IN ('sb4', 'sb5', 'sb6', 'sb7', 'sb8', 'sb9', 'sb10')
        ORDER BY c.id
    """)

    chunks = cursor.fetchall()
    total_chunks = len(chunks)
    print(f"Found {total_chunks} chunks to process")

    # Prepare embeddings data
    embeddings_data = []
    batch_size = 100
    processed = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [chunk[3] for chunk in batch]  # Raw content only

        # Generate embeddings for batch
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
                dimensions=1536
            )

            # Store embeddings
            for j, chunk in enumerate(batch):
                chunk_id = chunk[0]
                verse_id = chunk[1]
                chunk_type = chunk[2]
                content = chunk[3]
                chapter = chunk[4]
                verse_number = chunk[5]
                book_code = chunk[6]
                book_name = chunk[7]

                embeddings_data.append({
                    'id': f"vedabase_chunk_{chunk_id}",
                    'values': response.data[j].embedding,
                    'metadata': {
                        'source': 'vedabase',
                        'chunk_id': chunk_id,
                        'verse_id': verse_id,
                        'book_code': book_code,
                        'book_name': book_name,
                        'chapter': chapter,
                        'verse_number': verse_number,
                        'chunk_type': chunk_type,
                        'content': content[:500]
                    }
                })

            processed += len(batch)
            print(f"  Processed {processed}/{total_chunks} chunks ({processed*100//total_chunks}%)")

        except Exception as e:
            print(f"  Error processing batch {i//batch_size + 1}: {e}")
            continue

    conn.close()

    # Save embeddings to file
    output_file = 'sb_cantos_4_10_embeddings.json'
    with open(output_file, 'w') as f:
        json.dump(embeddings_data, f)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 80)
    print(f"  Total chunks processed: {len(embeddings_data)}")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:.2f} MB")
    print("=" * 80)

if __name__ == '__main__':
    generate_embeddings()
