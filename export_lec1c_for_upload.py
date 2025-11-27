#!/usr/bin/env python3
"""
Export only LEC1C data for upload to remote D1
"""

import sqlite3
import json
from pathlib import Path

def get_local_db():
    """Get connection to local D1 database"""
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject')
    db_files = list(db_path.glob('*.sqlite'))
    if not db_files:
        raise FileNotFoundError(f"No D1 database found in {db_path}")
    return sqlite3.connect(db_files[0])

def export_lec1c():
    """Export LEC1C data to JSON"""
    conn = get_local_db()
    cursor = conn.cursor()

    print("=" * 80)
    print("EXPORTING LEC1C FOR UPLOAD")
    print("=" * 80)

    # Get LEC1C book ID
    cursor.execute("SELECT id, code, name FROM vedabase_books WHERE code = 'LEC1C'")
    book_row = cursor.fetchone()

    if not book_row:
        print("Error: LEC1C not found in database")
        return

    book_id = book_row[0]
    print(f"\nFound LEC1C book: ID={book_id}, code={book_row[1]}, name={book_row[2]}")

    # Get LEC1C verses
    cursor.execute('''
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation
        FROM vedabase_verses
        WHERE book_id = ?
        ORDER BY id
    ''', (book_id,))

    verses = []
    for row in cursor.fetchall():
        verses.append({
            'id': row[0],
            'book_id': row[1],
            'chapter': row[2],
            'verse_number': row[3],
            'sanskrit': row[4],
            'synonyms': row[5],
            'translation': row[6]
        })

    print(f"  Verses: {len(verses)}")

    # Get LEC1C chunks
    cursor.execute('''
        SELECT c.id, c.verse_id, c.chunk_type, c.chunk_index, c.content, c.word_count
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        WHERE v.book_id = ?
        ORDER BY c.id
    ''', (book_id,))

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

    print(f"  Chunks: {len(chunks)}")

    conn.close()

    # Save to JSON
    data = {
        'verses': verses,
        'chunks': chunks
    }

    output_file = 'lec1c_export_for_upload.json'
    print(f"\nSaving to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {file_size:.2f} MB")

    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"  LEC1C verses: {len(verses)}")
    print(f"  LEC1C chunks: {len(chunks)}")
    print(f"  Output: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    export_lec1c()
