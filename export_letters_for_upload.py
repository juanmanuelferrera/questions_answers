#!/usr/bin/env python3
"""
Export letters from local D1 for remote upload
"""

import json
import sqlite3

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def export_letters():
    """Export letters for remote upload"""

    print("=" * 80)
    print("EXPORTING LETTERS FOR REMOTE UPLOAD")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get the LETTERS book
    cursor.execute("""
        SELECT id, code, name
        FROM vedabase_books
        WHERE code = 'LETTERS'
    """)
    book_row = cursor.fetchone()

    if not book_row:
        print("Error: LETTERS book not found in database")
        return

    book_id, book_code, book_name = book_row
    print(f"\nFound book: {book_name} (ID: {book_id})")

    # Get all verses (letters) for this book
    cursor.execute("""
        SELECT id, chapter, verse_number, synonyms, translation
        FROM vedabase_verses
        WHERE book_id = ?
        ORDER BY id
    """, (book_id,))

    verses = cursor.fetchall()
    print(f"Found {len(verses)} letters")

    # Get all chunks
    cursor.execute("""
        SELECT c.id, c.verse_id, c.chunk_type, c.content
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        WHERE v.book_id = ?
        ORDER BY c.id
    """, (book_id,))

    chunks = cursor.fetchall()
    print(f"Found {len(chunks)} chunks")

    conn.close()

    # Prepare export data
    export_data = {
        'book': {
            'id': book_id,
            'code': book_code,
            'name': book_name
        },
        'verses': [
            {
                'id': v[0],
                'book_id': book_id,
                'chapter': v[1],
                'verse_number': v[2],
                'recipient': v[3],  # Stored in synonyms
                'date': v[4],  # Stored in translation
            }
            for v in verses
        ],
        'chunks': [
            {
                'id': c[0],
                'verse_id': c[1],
                'chunk_type': c[2],
                'content': c[3]
            }
            for c in chunks
        ]
    }

    # Save to file
    output_file = 'letters_export_for_upload.json'
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)

    import os
    file_size = os.path.getsize(output_file) / (1024 * 1024)

    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:.2f} MB")
    print(f"  Book: {book_name}")
    print(f"  Letters: {len(verses)}")
    print(f"  Chunks: {len(chunks)}")
    print("=" * 80)

if __name__ == '__main__':
    export_letters()
