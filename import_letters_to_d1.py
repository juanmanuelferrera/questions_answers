#!/usr/bin/env python3
"""
Import Srila Prabhupada's Letters to local D1 database
"""

import json
import sqlite3
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def import_letters():
    """Import letters to D1"""

    print("=" * 80)
    print("IMPORTING LETTERS TO LOCAL D1")
    print("=" * 80)

    # Load parsed data
    with open('letters_parsed_for_rag.json', 'r') as f:
        book = json.load(f)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get next book ID
    cursor.execute("SELECT MAX(id) FROM vedabase_books")
    result = cursor.fetchone()
    next_book_id = (result[0] or 0) + 1

    print(f"\nBook ID: {next_book_id}")
    print(f"Book: {book['name']} ({book['code']})")

    # Insert book
    cursor.execute("""
        INSERT INTO vedabase_books (id, code, name, created_at)
        VALUES (?, ?, ?, datetime('now'))
    """, (next_book_id, book['code'], book['name']))

    print(f"✓ Inserted book")

    # Get next verse ID
    cursor.execute("SELECT MAX(id) FROM vedabase_verses")
    result = cursor.fetchone()
    next_verse_id = (result[0] or 0) + 1

    # Get next chunk ID
    cursor.execute("SELECT MAX(id) FROM vedabase_chunks")
    result = cursor.fetchone()
    next_chunk_id = (result[0] or 0) + 1

    total_verses = 0
    total_chunks = 0

    for chapter in book['chapters']:
        chapter_name = chapter['chapter_name']

        for verse in chapter['verses']:
            # Insert verse (letter)
            cursor.execute("""
                INSERT INTO vedabase_verses
                (id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                next_verse_id,
                next_book_id,
                chapter_name,
                verse['verse_number'],
                '',  # No sanskrit for letters
                verse.get('recipient', ''),  # Use recipient as synonyms
                verse.get('full_date', ''),  # Use date as translation
            ))

            # Insert chunks
            for chunk in verse['chunks']:
                cursor.execute("""
                    INSERT INTO vedabase_chunks
                    (id, verse_id, chunk_type, content, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (
                    next_chunk_id,
                    next_verse_id,
                    chunk['chunk_type'],
                    chunk['content']
                ))
                next_chunk_id += 1
                total_chunks += 1

            next_verse_id += 1
            total_verses += 1

        if total_verses % 500 == 0:
            print(f"  Processed {total_verses} letters, {total_chunks} chunks...")

    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"  Book ID: {next_book_id}")
    print(f"  Total letters: {total_verses}")
    print(f"  Total chunks: {total_chunks}")
    print("=" * 80)

if __name__ == '__main__':
    import_letters()
