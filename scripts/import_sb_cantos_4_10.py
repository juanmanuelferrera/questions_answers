#!/usr/bin/env python3
"""
Import Srimad Bhagavatam Cantos 4-10 to local D1 database
"""

import json
import sqlite3
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def import_verses():
    """Import verses to local D1 database"""

    print("=" * 80)
    print("IMPORTING SRIMAD BHAGAVATAM CANTOS 4-10 TO LOCAL D1")
    print("=" * 80)

    # Load parsed data
    input_file = 'sb_cantos_4_10_parsed.json'
    print(f"\nLoading parsed data from {input_file}...")

    with open(input_file, 'r', encoding='utf-8') as f:
        verses = json.load(f)

    print(f"Loaded {len(verses)} verses")

    # Connect to database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Import books first
    books_imported = 0
    for canto_num in range(4, 11):
        book_code = f'sb{canto_num}'
        book_name = f'Srimad Bhagavatam Canto {canto_num}'

        # Check if book already exists
        cursor.execute("SELECT id FROM vedabase_books WHERE code = ?", (book_code,))
        if cursor.fetchone():
            print(f"  Book {book_code} already exists, skipping...")
            continue

        cursor.execute("""
            INSERT INTO vedabase_books (code, name)
            VALUES (?, ?)
        """, (book_code, book_name))
        books_imported += 1

    conn.commit()
    print(f"\n✓ Imported {books_imported} new books")

    # Import verses and create chunks
    verses_imported = 0
    chunks_created = 0

    for verse in verses:
        # Get book_id
        cursor.execute("SELECT id FROM vedabase_books WHERE code = ?", (verse['book_code'],))
        result = cursor.fetchone()
        if not result:
            print(f"  Error: Book {verse['book_code']} not found")
            continue

        book_id = result[0]

        # Insert verse
        cursor.execute("""
            INSERT INTO vedabase_verses (book_id, chapter, verse_number,
                                        sanskrit, synonyms, translation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            book_id,
            verse['chapter'],
            verse['verse_number'],
            verse['sanskrit'],
            verse['synonyms'],
            verse['translation']
        ))

        verse_id = cursor.lastrowid
        verses_imported += 1

        # Create verse_text chunk (sanskrit + synonyms + translation)
        verse_chunk = f"{verse['sanskrit']}\n\n{verse['synonyms']}\n\n{verse['translation']}"
        cursor.execute("""
            INSERT INTO vedabase_chunks (verse_id, chunk_type, content)
            VALUES (?, 'verse_text', ?)
        """, (verse_id, verse_chunk))
        chunks_created += 1

        # Create purport chunks (split by paragraph)
        if verse['purport']:
            # Split purport by double newlines (paragraphs)
            purport_paragraphs = [p.strip() for p in verse['purport'].split('\n\n') if p.strip()]

            for para in purport_paragraphs:
                cursor.execute("""
                    INSERT INTO vedabase_chunks (verse_id, chunk_type, content)
                    VALUES (?, 'purport_paragraph', ?)
                """, (verse_id, para))
                chunks_created += 1

        # Commit every 100 verses
        if verses_imported % 100 == 0:
            conn.commit()
            print(f"  Imported {verses_imported}/{len(verses)} verses, {chunks_created} chunks")

    # Final commit
    conn.commit()

    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"  ✓ Verses imported: {verses_imported}")
    print(f"  ✓ Chunks created: {chunks_created}")
    print(f"  ✓ Average chunks per verse: {chunks_created/verses_imported:.2f}")

    # Print summary by canto
    print("\nBreakdown by Canto:")
    for canto_num in range(4, 11):
        book_code = f'sb{canto_num}'
        cursor.execute("""
            SELECT COUNT(v.id) as verse_count, COUNT(c.id) as chunk_count
            FROM vedabase_verses v
            JOIN vedabase_books b ON v.book_id = b.id
            LEFT JOIN vedabase_chunks c ON v.id = c.verse_id
            WHERE b.code = ?
        """, (book_code,))
        verse_count, chunk_count = cursor.fetchone()
        print(f"  Canto {canto_num}: {verse_count} verses, {chunk_count} chunks")

    print("=" * 80)

    conn.close()

if __name__ == '__main__':
    import_verses()
