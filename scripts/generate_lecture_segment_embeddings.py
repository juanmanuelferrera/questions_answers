#!/usr/bin/env python3
"""
Generate embeddings for lecture_segment chunks
These are the newly created smaller lecture chunks from rechunking optimization
"""

import json
import sqlite3
import os
from openai import OpenAI
from pathlib import Path
import time

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
OUTPUT_FILE = "lecture_segments_embeddings.json"

def generate_embeddings():
    """Generate embeddings for lecture_segment chunks"""

    print("=" * 80)
    print("GENERATING EMBEDDINGS FOR LECTURE SEGMENTS")
    print("=" * 80)

    # Initialize OpenAI client
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        return

    client = OpenAI(api_key=api_key)

    # Connect to database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get all lecture_segment chunks
    cursor.execute("""
        SELECT c.id, c.verse_id, c.content, c.word_count,
               v.chapter, v.verse_number, v.book_id,
               b.code, b.name
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE c.chunk_type = 'lecture_segment'
        ORDER BY c.id
    """)

    chunks = cursor.fetchall()
    total_chunks = len(chunks)
    print(f"\n📊 Found {total_chunks:,} lecture_segment chunks to process")

    if total_chunks == 0:
        print("⚠️  No lecture segments found!")
        conn.close()
        return

    # Prepare embeddings data
    embeddings_data = []
    batch_size = 100
    processed = 0
    errors = 0

    print(f"\n🔄 Processing in batches of {batch_size}...")
    print(f"⏱️  Estimated time: {(total_chunks / batch_size) * 1.5:.1f} minutes")
    print()

    start_time = time.time()

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [chunk[2] for chunk in batch]  # content

        # Generate embeddings for batch
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
                dimensions=1536
            )

            # Store embeddings
            for j, chunk in enumerate(batch):
                chunk_id, verse_id, content, word_count, chapter, verse_number, book_id, book_code, book_name = chunk

                embeddings_data.append({
                    'id': f"lecture_segment_{chunk_id}",
                    'values': response.data[j].embedding,
                    'metadata': {
                        'source': 'vedabase',
                        'chunk_id': chunk_id,
                        'verse_id': verse_id,
                        'book_code': book_code,
                        'book_name': book_name,
                        'chapter': chapter,
                        'verse_number': verse_number,
                        'chunk_type': 'lecture_segment',
                        'content': content[:500]  # First 500 chars for metadata
                    }
                })

            processed += len(batch)
            elapsed = time.time() - start_time
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = (total_chunks - processed) / rate if rate > 0 else 0

            print(f"  [{processed:5d}/{total_chunks}] {processed*100//total_chunks:3d}% | "
                  f"Rate: {rate:.1f} chunks/s | ETA: {remaining/60:.1f} min")

        except Exception as e:
            print(f"  ❌ Error processing batch {i//batch_size + 1}: {e}")
            errors += 1
            if errors > 5:
                print("  ⚠️  Too many errors, stopping...")
                break
            continue

    conn.close()

    # Save embeddings to file
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(embeddings_data, f)

    file_size = Path(OUTPUT_FILE).stat().st_size / (1024 * 1024)
    total_time = time.time() - start_time

    print("\n" + "=" * 80)
    print("✅ EMBEDDING GENERATION COMPLETE")
    print("=" * 80)
    print(f"  Total chunks processed: {len(embeddings_data):,}")
    print(f"  Output file: {OUTPUT_FILE}")
    print(f"  File size: {file_size:.2f} MB")
    print(f"  Total time: {total_time/60:.1f} minutes")
    print(f"  Average rate: {processed/total_time:.1f} chunks/second")
    print(f"  Errors: {errors}")
    print("=" * 80)
    print()
    print("📌 Next steps:")
    print("  1. Run: python3 upload_lecture_segments_to_vectorize.py")
    print("  2. Run: python3 upload_lecture_segments_to_d1.py")
    print()

if __name__ == '__main__':
    generate_embeddings()
