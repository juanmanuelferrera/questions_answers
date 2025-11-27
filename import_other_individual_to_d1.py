#!/usr/bin/env python3
"""
Import individual OTHER books to local D1 database
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

def import_individual_books():
    """Import individual books from other.html to D1"""

    # Load parsed data
    with open('other_individual_parsed.json', 'r', encoding='utf-8') as f:
        books_data = json.load(f)

    conn = get_local_db()
    cursor = conn.cursor()

    # Check current max IDs
    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_verses')
    max_verse_id = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_chunks')
    max_chunk_id = cursor.fetchone()[0]

    cursor.execute('SELECT COALESCE(MAX(id), 0) FROM vedabase_books')
    max_book_id = cursor.fetchone()[0]

    print("=" * 80)
    print("IMPORTING INDIVIDUAL OTHER BOOKS TO LOCAL D1")
    print("=" * 80)
    print(f"\nStarting IDs: verse={max_verse_id}, chunk={max_chunk_id}, book={max_book_id}")

    verse_id = max_verse_id + 1
    chunk_id = max_chunk_id + 1
    book_id = max_book_id + 1

    total_books_imported = 0
    total_verses_imported = 0
    total_chunks_imported = 0

    # Import each book
    for book_code, book_info in books_data.items():
        book_title = book_info['title']
        chunks = book_info['chunks']

        print(f"\nImporting {book_code}: {book_title}")
        print(f"  Chunks: {len(chunks)}")

        # Insert book entry
        cursor.execute('''
            INSERT INTO vedabase_books (id, code, name, created_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (book_id, book_code, book_title))

        # Group chunks by chapter to create verses
        chapter_chunks = {}
        for chunk in chunks:
            chapter = chunk.get('chapter', 'Introduction')
            if chapter not in chapter_chunks:
                chapter_chunks[chapter] = []
            chapter_chunks[chapter].append(chunk)

        # Insert verses (one per chapter)
        for chapter, chapter_chunk_list in chapter_chunks.items():
            # Insert verse entry
            cursor.execute('''
                INSERT INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation)
                VALUES (?, ?, ?, '', '', '', '')
            ''', (verse_id, book_id, chapter))

            # Insert chunks for this chapter
            for chunk in chapter_chunk_list:
                cursor.execute('''
                    INSERT INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
                    VALUES (?, ?, 'chapter_content', ?, ?, ?)
                ''', (
                    chunk_id,
                    verse_id,
                    chunk['chunk_index'],
                    chunk['content'],
                    len(chunk['content'].split())
                ))

                chunk_id += 1
                total_chunks_imported += 1

            verse_id += 1
            total_verses_imported += 1

        book_id += 1
        total_books_imported += 1

        print(f"  ✓ Imported {len(chapter_chunks)} chapters, {len(chunks)} chunks")

    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"  Books imported: {total_books_imported}")
    print(f"  Chapters/verses imported: {total_verses_imported}")
    print(f"  Chunks imported: {total_chunks_imported}")
    print(f"  New verse ID range: {max_verse_id + 1} to {verse_id - 1}")
    print(f"  New chunk ID range: {max_chunk_id + 1} to {chunk_id - 1}")
    print(f"  New book ID range: {max_book_id + 1} to {book_id - 1}")
    print("=" * 80)

if __name__ == '__main__':
    import_individual_books()
