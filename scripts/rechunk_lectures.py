#!/usr/bin/env python3
"""
Split large lecture_content chunks into smaller segments for better retrieval
Target: 404 words avg → 100-150 words
"""

import sqlite3
import re

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
TARGET_WORDS = 125  # Target chunk size in words
MAX_WORDS = 175     # Maximum before forcing a split

def split_into_sentences(text):
    """Split text into sentences preserving punctuation"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def create_word_based_chunks(text, target_words=TARGET_WORDS, max_words=MAX_WORDS):
    """Split text into chunks based on word count at sentence boundaries"""
    words = text.split()

    if len(words) <= max_words:
        return [text]

    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())

        # If adding this sentence would exceed max, save current chunk
        if current_word_count + sentence_words > max_words and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = sentence_words
        # If we're at or above target and have content, start new chunk
        elif current_word_count >= target_words and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentence]
            current_word_count = sentence_words
        else:
            current_chunk.append(sentence)
            current_word_count += sentence_words

    # Add remaining sentences
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def rechunk_lectures():
    """Find and split large lecture chunks"""

    print("=" * 80)
    print("RE-CHUNKING LECTURE CONTENT")
    print(f"Target: {TARGET_WORDS} words per chunk (max {MAX_WORDS})")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Find lecture chunks that are too large (>175 words)
    cursor.execute("""
        SELECT id, verse_id, content, word_count, chunk_index
        FROM vedabase_chunks
        WHERE chunk_type = 'lecture_content'
        AND word_count > ?
        ORDER BY id
    """, (MAX_WORDS,))

    large_chunks = cursor.fetchall()
    print(f"\nFound {len(large_chunks)} large lecture chunks to split")

    if len(large_chunks) == 0:
        print("No chunks need splitting!")
        conn.close()
        return

    chunks_added = 0
    chunks_deleted = 0
    total_original_words = 0
    total_new_chunks = 0

    for chunk_id, verse_id, content, word_count, chunk_index in large_chunks:
        total_original_words += word_count

        # Split into smaller chunks
        smaller_chunks = create_word_based_chunks(content, TARGET_WORDS, MAX_WORDS)

        if len(smaller_chunks) > 1:
            print(f"  Chunk {chunk_id}: {word_count} words → {len(smaller_chunks)} sub-chunks")

            # Delete original chunk
            cursor.execute("DELETE FROM vedabase_chunks WHERE id = ?", (chunk_id,))
            chunks_deleted += 1

            # Insert smaller chunks
            for i, small_chunk in enumerate(smaller_chunks):
                words_in_chunk = len(small_chunk.split())
                cursor.execute("""
                    INSERT INTO vedabase_chunks (verse_id, chunk_type, chunk_index, content, word_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    verse_id,
                    'lecture_segment',  # New type to distinguish from original
                    (chunk_index * 100 + i) if chunk_index else i,
                    small_chunk,
                    words_in_chunk
                ))
                chunks_added += 1
                total_new_chunks += 1

    conn.commit()

    # Get statistics
    cursor.execute("""
        SELECT AVG(word_count), MIN(word_count), MAX(word_count)
        FROM vedabase_chunks
        WHERE chunk_type = 'lecture_segment'
    """)
    avg, min_w, max_w = cursor.fetchone()

    conn.close()

    print("\n" + "=" * 80)
    print("RE-CHUNKING COMPLETE")
    print("=" * 80)
    print(f"  Original chunks: {len(large_chunks)} ({total_original_words:,} words total)")
    print(f"  Chunks deleted: {chunks_deleted}")
    print(f"  New chunks created: {chunks_added}")
    print(f"  New chunk stats: avg={avg:.1f} words, min={min_w}, max={max_w}")
    print(f"  Average split ratio: {chunks_added/chunks_deleted:.1f}x")
    print("=" * 80)

if __name__ == '__main__':
    rechunk_lectures()
