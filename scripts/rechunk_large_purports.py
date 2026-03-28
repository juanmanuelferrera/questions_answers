#!/usr/bin/env python3
"""
Re-chunk large purport paragraphs into smaller segments
This helps with retrieval when specific names/concepts are buried in long text
"""

import sqlite3
import re

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
MAX_CHUNK_SIZE = 600  # Target chunk size in characters

def split_into_sentences(text):
    """Split text into sentences"""
    # Simple sentence splitting (can be improved)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def create_smaller_chunks(text, max_size=MAX_CHUNK_SIZE):
    """Split long text into smaller chunks at sentence boundaries"""
    if len(text) <= max_size:
        return [text]

    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_size + sentence_len > max_size and current_chunk:
            # Save current chunk and start new one
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_size = sentence_len
        else:
            current_chunk.append(sentence)
            current_size += sentence_len + 1  # +1 for space

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def rechunk_large_purports():
    """Find and split large purport chunks"""

    print("=" * 80)
    print("RE-CHUNKING LARGE PURPORT PARAGRAPHS")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Find large purport chunks
    cursor.execute("""
        SELECT id, verse_id, content, chunk_index
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_paragraph'
        AND length(content) > ?
        ORDER BY id
    """, (MAX_CHUNK_SIZE,))

    large_chunks = cursor.fetchall()
    print(f"\nFound {len(large_chunks)} large purport chunks to split")

    chunks_added = 0
    chunks_deleted = 0

    for chunk_id, verse_id, content, chunk_index in large_chunks:
        # Split into smaller chunks
        smaller_chunks = create_smaller_chunks(content, MAX_CHUNK_SIZE)

        if len(smaller_chunks) > 1:
            print(f"  Splitting chunk {chunk_id}: {len(content)} chars → {len(smaller_chunks)} sub-chunks")

            # Delete original chunk
            cursor.execute("DELETE FROM vedabase_chunks WHERE id = ?", (chunk_id,))
            chunks_deleted += 1

            # Insert smaller chunks
            for i, small_chunk in enumerate(smaller_chunks):
                cursor.execute("""
                    INSERT INTO vedabase_chunks (verse_id, chunk_type, chunk_index, content, word_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    verse_id,
                    'purport_segment',  # New type to distinguish from original paragraphs
                    chunk_index + i if chunk_index else None,
                    small_chunk,
                    len(small_chunk.split())
                ))
                chunks_added += 1

    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print("RE-CHUNKING COMPLETE")
    print("=" * 80)
    print(f"  Large chunks split: {chunks_deleted}")
    print(f"  New smaller chunks created: {chunks_added}")
    print(f"  Net change: +{chunks_added - chunks_deleted} chunks")
    print("=" * 80)
    print("\n⚠️  IMPORTANT: You'll need to:")
    print("  1. Generate new embeddings for the new chunks")
    print("  2. Upload to production D1")
    print("  3. Upload embeddings to Vectorize")
    print("=" * 80)

if __name__ == '__main__':
    rechunk_large_purports()
