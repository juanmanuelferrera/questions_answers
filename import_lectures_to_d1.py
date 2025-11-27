#!/usr/bin/env python3
"""
Import parsed lecture data to local D1 database
"""

import json
import sqlite3
from pathlib import Path

def get_local_db():
    """Get connection to local D1 database"""
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject')
    db_files = list(db_path.glob('*.sqlite'))

    if not db_files:
        raise FileNotFoundError(f"No D1 database found in {db_path}")

    return sqlite3.connect(db_files[0])

def import_lectures_to_d1():
    """Import lecture chunks to D1"""
    # Load parsed lectures
    with open('lectures_parsed.json', 'r', encoding='utf-8') as f:
        lectures_data = json.load(f)

    conn = get_local_db()
    cursor = conn.cursor()

    # Check current max IDs
    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_verses')
    max_verse_id = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_chunks')
    max_chunk_id = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_books')
    max_book_id = cursor.fetchone()[0]

    print(f"Starting import after verse ID {max_verse_id}, chunk ID {max_chunk_id}, book ID {max_book_id}")

    # Create book entries for lecture collections
    book_mappings = {
        'lec1a': ('Lectures Part 1A', 'LEC1A'),
        'lec1b': ('Lectures Part 1B', 'LEC1B'),
        'lec1c': ('Lectures Part 1C', 'LEC1C'),
        'lec2a': ('Lectures Part 2A', 'LEC2A'),
        'lec2b': ('Lectures Part 2B', 'LEC2B'),
        'lec2c': ('Lectures Part 2C', 'LEC2C'),
        'other': ('Other Vedic Texts', 'OTHER')
    }

    book_id_map = {}
    for book_key, (title, code) in book_mappings.items():
        # Check if book already exists
        cursor.execute('SELECT id FROM vedabase_books WHERE code = ?', (code,))
        existing = cursor.fetchone()

        if existing:
            book_id_map[book_key] = existing[0]
            print(f"Book '{title}' already exists with ID {existing[0]}")
        else:
            max_book_id += 1
            cursor.execute('''
                INSERT INTO vedabase_books (id, code, name)
                VALUES (?, ?, ?)
            ''', (max_book_id, code, title))
            book_id_map[book_key] = max_book_id
            print(f"Created book '{title}' with ID {max_book_id}")

    conn.commit()

    total_verses = 0
    total_chunks = 0

    # Process each lecture file
    for book_key, chunks in lectures_data.items():
        book_id = book_id_map.get(book_key)
        if not book_id:
            print(f"Warning: No book ID for {book_key}, skipping")
            continue

        print(f"\nImporting {book_key}: {len(chunks)} chunks")

        for chunk in chunks:
            max_verse_id += 1

            # Insert into vedabase_verses
            cursor.execute('''
                INSERT INTO vedabase_verses
                (id, book_id, chapter, verse_number, sanskrit, synonyms, translation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                max_verse_id,
                book_id,
                chunk['lecture_title'][:200],  # Truncate long titles
                f"Chunk {chunk['chunk_index'] + 1}",
                '',  # No sanskrit in lectures
                '',  # No synonyms in lectures
                ''   # Translation is in content
            ))

            total_verses += 1

            # Create chunk for RAG
            max_chunk_id += 1
            word_count = len(chunk['content'].split())
            cursor.execute('''
                INSERT INTO vedabase_chunks
                (id, verse_id, chunk_type, chunk_index, content, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                max_chunk_id,
                max_verse_id,
                'lecture_content',
                chunk['chunk_index'],
                chunk['content'],
                word_count
            ))

            total_chunks += 1

            if total_verses % 100 == 0:
                print(f"  Progress: {total_verses} sections, {total_chunks} chunks")
                conn.commit()

    # Note: vedabase_books doesn't have total_verses column, so we skip updating it

    conn.commit()
    conn.close()

    print(f"\n✅ Import complete!")
    print(f"   Total lecture sections imported: {total_verses}")
    print(f"   Total chunks created: {total_chunks}")
    print(f"   New verse ID range: {max_verse_id - total_verses + 1} to {max_verse_id}")
    print(f"   New chunk ID range: {max_chunk_id - total_chunks + 1} to {max_chunk_id}")

if __name__ == '__main__':
    import_lectures_to_d1()
