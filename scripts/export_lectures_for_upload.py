#!/usr/bin/env python3
"""
Export lecture data to JSON format for upload
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

def export_lectures():
    """Export lecture data to JSON"""
    conn = get_local_db()
    cursor = conn.cursor()

    # Get lecture books (IDs 9+)
    cursor.execute('SELECT id, code, name FROM vedabase_books WHERE id >= 9 ORDER BY id')
    books = []
    for row in cursor.fetchall():
        books.append({
            'id': row[0],
            'code': row[1],
            'name': row[2]
        })

    # Get lecture verses (IDs 8482+)
    cursor.execute('''
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation
        FROM vedabase_verses
        WHERE id >= 8482
        ORDER BY id
    ''')

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

    # Get lecture chunks (IDs 19824+)
    cursor.execute('''
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE id >= 19824
        ORDER BY id
    ''')

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

    # Save to JSON
    export_data = {
        'books': books,
        'verses': verses,
        'chunks': chunks
    }

    output_file = Path('lectures_export.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Export complete:")
    print(f"   Books: {len(books)}")
    print(f"   Verses: {len(verses)}")
    print(f"   Chunks: {len(chunks)}")
    print(f"   Saved to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    export_lectures()
