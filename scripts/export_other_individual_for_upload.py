#!/usr/bin/env python3
"""
Export individual OTHER books for upload to remote D1
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

def export_individual_books():
    """Export individual books to JSON"""
    conn = get_local_db()
    cursor = conn.cursor()

    print("=" * 80)
    print("EXPORTING INDIVIDUAL OTHER BOOKS FOR UPLOAD")
    print("=" * 80)

    # Get all books with ID >= 16 (the individual books)
    cursor.execute("SELECT id, code, name FROM vedabase_books WHERE id >= 16 ORDER BY id")
    books = cursor.fetchall()

    print(f"\nFound {len(books)} individual books to export")

    all_data = {
        'books': [],
        'verses': [],
        'chunks': []
    }

    for book_id, book_code, book_name in books:
        print(f"\n{book_code}: {book_name}")

        # Add book
        all_data['books'].append({
            'id': book_id,
            'code': book_code,
            'name': book_name
        })

        # Get verses for this book
        cursor.execute('''
            SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation
            FROM vedabase_verses
            WHERE book_id = ?
            ORDER BY id
        ''', (book_id,))

        verses = cursor.fetchall()
        for row in verses:
            all_data['verses'].append({
                'id': row[0],
                'book_id': row[1],
                'chapter': row[2],
                'verse_number': row[3],
                'sanskrit': row[4],
                'synonyms': row[5],
                'translation': row[6]
            })

        # Get chunks for this book
        cursor.execute('''
            SELECT c.id, c.verse_id, c.chunk_type, c.chunk_index, c.content, c.word_count
            FROM vedabase_chunks c
            JOIN vedabase_verses v ON c.verse_id = v.id
            WHERE v.book_id = ?
            ORDER BY c.id
        ''', (book_id,))

        chunks = cursor.fetchall()
        for row in chunks:
            all_data['chunks'].append({
                'id': row[0],
                'verse_id': row[1],
                'chunk_type': row[2],
                'chunk_index': row[3],
                'content': row[4],
                'word_count': row[5]
            })

        print(f"  Verses: {len(verses)}, Chunks: {len(chunks)}")

    conn.close()

    # Save to JSON
    output_file = 'other_individual_export_for_upload.json'
    print(f"\nSaving to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {file_size:.2f} MB")

    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"  Books: {len(all_data['books'])}")
    print(f"  Verses: {len(all_data['verses'])}")
    print(f"  Chunks: {len(all_data['chunks'])}")
    print(f"  Output: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    export_individual_books()
