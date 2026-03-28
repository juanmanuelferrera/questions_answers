#!/usr/bin/env python3
"""
Generate embeddings for conversation chunks
"""

import sqlite3
import json
import openai
import time
import os
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
OUTPUT_FILE = "conversation_embeddings.json"
BATCH_SIZE = 100
EMBEDDING_MODEL = "text-embedding-3-small"

# Set OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_conversation_chunks():
    """Get all conversation chunks from local DB"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type IN ('morning_walk_segment', 'room_conversation_segment', 'conversation_segment')
        ORDER BY id
    """)

    chunks = []
    for row in cursor.fetchall():
        chunks.append({
            'id': row[0],
            'verse_id': row[1],
            'chunk_type': row[2],
            'chunk_index': row[3],
            'content': row[4],
            'word_count': row[5]
        })

    conn.close()
    return chunks

def generate_embeddings_batch(texts):
    """Generate embeddings for a batch of texts"""
    try:
        response = openai.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"\n❌ Error generating embeddings: {e}")
        return None

def main():
    print("=" * 80)
    print("GENERATING CONVERSATION EMBEDDINGS")
    print("=" * 80)
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Batch size: {BATCH_SIZE}")
    print("=" * 80)
    print()

    # Get all conversation chunks
    print("📂 Loading conversation chunks from database...")
    chunks = get_conversation_chunks()
    total_chunks = len(chunks)

    print(f"✅ Found {total_chunks:,} conversation chunks")
    print()

    # Calculate batches
    num_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📦 Processing {num_batches} batches of {BATCH_SIZE}...")
    print()

    all_embeddings = []
    success_count = 0
    start_time = time.time()

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = chunks[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_chunks)

        print(f"[{batch_num}/{num_batches}] Generating embeddings for chunks {i+1}-{batch_end}...", end=" ", flush=True)

        # Extract text content
        texts = [chunk['content'] for chunk in batch]

        # Generate embeddings
        embeddings = generate_embeddings_batch(texts)

        if embeddings:
            # Store embeddings with metadata
            for chunk, embedding in zip(batch, embeddings):
                all_embeddings.append({
                    'id': chunk['id'],
                    'verse_id': chunk['verse_id'],
                    'chunk_type': chunk['chunk_type'],
                    'embedding': embedding
                })
            print("✅")
            success_count += len(batch)
        else:
            print("❌ Failed")

        # Progress update every 10 batches
        if batch_num % 10 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60 if elapsed > 0 else 0
            remaining = (num_batches - batch_num) / rate if rate > 0 else 0
            print(f"   Progress: {batch_num}/{num_batches} ({batch_num*100//num_batches}%) | Rate: {rate:.1f} batches/min | ETA: {remaining:.1f} min")

        # Small pause to avoid rate limiting
        time.sleep(0.1)

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("EMBEDDING GENERATION SUMMARY")
    print("=" * 80)
    print(f"  Total chunks: {total_chunks:,}")
    print(f"  Successfully generated: {success_count:,} ({success_count*100//total_chunks if total_chunks > 0 else 0}%)")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print(f"  Rate: {success_count/(elapsed/60):.0f} embeddings/min")
    print("=" * 80)
    print()

    # Save to JSON
    print(f"💾 Saving embeddings to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_embeddings, f)

    print(f"✅ Saved {len(all_embeddings):,} embeddings")
    print()

    # Calculate file size
    file_size = Path(OUTPUT_FILE).stat().st_size / (1024 * 1024)
    print(f"📊 File size: {file_size:.1f} MB")
    print()

    print("Next steps:")
    print("1. Upload conversation verses to remote D1")
    print("2. Upload conversation chunks to remote D1")
    print("3. Upload conversation embeddings to Vectorize")

if __name__ == '__main__':
    main()
