#!/usr/bin/env python3
"""
Import only CC books (Caitanya Caritamrita) to existing D1 database
Adds to the existing vedabase tables without re-importing other books
"""

import json
import re
import sqlite3
from pathlib import Path
from typing import List, Dict

def split_purport_into_paragraphs(purport: str) -> List[str]:
    """Split purport text into paragraphs for better RAG chunking"""
    if not purport:
        return []

    # Split by double newlines or period followed by newline
    paragraphs = re.split(r'\n\n+|\.\s*\n', purport)

    # Clean and filter paragraphs
    cleaned = []
    for para in paragraphs:
        para = para.strip()
        # Only keep paragraphs with at least 20 words
        if para and len(para.split()) >= 20:
            cleaned.append(para)

    return cleaned

def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())

def main():
    print("=" * 80)
    print("IMPORTING CC BOOKS TO D1")
    print("=" * 80)

    # Load CC book data
    with open('missing_books_parsed.json', 'r') as f:
        cc_data = json.load(f)

    # Remove empty lec1c
    if 'lec1c' in cc_data:
        del cc_data['lec1c']

    # Connect to local D1 database
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject/') / '3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite'

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Make sure you've run 'npx wrangler dev' at least once")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing book IDs
    book_code_to_id = {}
    cursor.execute("SELECT id, code FROM vedabase_books")
    for row in cursor.fetchall():
        book_id, code = row
        book_code_to_id[code] = book_id

    print(f"\nFound {len(book_code_to_id)} existing books in database")

    # Get max IDs to continue from
    cursor.execute("SELECT MAX(id) FROM vedabase_verses")
    max_verse_id = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MAX(id) FROM vedabase_chunks")
    max_chunk_id = cursor.fetchone()[0] or 0

    print(f"Starting verse ID: {max_verse_id + 1}")
    print(f"Starting chunk ID: {max_chunk_id + 1}")

    total_verses = 0
    total_chunks = 0

    # Process each CC book
    for book_code in ['cc1', 'cc2', 'cc3']:
        if book_code not in cc_data:
            continue

        book_id = book_code_to_id.get(book_code)
        if not book_id:
            print(f"\nError: Book code '{book_code}' not found in database")
            continue

        verses = cc_data[book_code]
        print(f"\n{book_code.upper()}: Processing {len(verses)} verses...")

        verse_count = 0
        chunk_count = 0

        for verse in verses:
            max_verse_id += 1
            chapter = verse.get('chapter', '')
            verse_num = verse.get('verse', '')

            # Insert verse
            cursor.execute("""
                INSERT INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                max_verse_id,
                book_id,
                chapter,
                verse_num,
                verse.get('sanskrit', ''),
                verse.get('synonyms', ''),
                verse.get('translation', '')
            ))

            verse_count += 1

            # Create chunks for purport paragraphs
            purport = verse.get('purport', '')
            if purport:
                paragraphs = split_purport_into_paragraphs(purport)

                for para in paragraphs:
                    max_chunk_id += 1
                    word_count = count_words(para)

                    cursor.execute("""
                        INSERT INTO vedabase_chunks (id, verse_id, chunk_type, content, word_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        max_chunk_id,
                        max_verse_id,
                        'purport_paragraph',
                        para,
                        word_count
                    ))

                    chunk_count += 1

        print(f"  ✓ Inserted {verse_count} verses, {chunk_count} chunks")
        total_verses += verse_count
        total_chunks += chunk_count

    conn.commit()
    conn.close()

    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"Total verses imported: {total_verses}")
    print(f"Total chunks created: {total_chunks}")
    print("=" * 80)

if __name__ == '__main__':
    main()
