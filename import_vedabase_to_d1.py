#!/usr/bin/env python3
"""
Import Vedabase data to Cloudflare D1 with chunking for RAG
Processes verses and splits purports into paragraphs for better retrieval
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

def create_verse_text_chunk(verse_data: Dict) -> str:
    """Create a comprehensive verse text chunk combining all verse elements"""
    parts = []

    if verse_data.get('sanskrit'):
        parts.append(f"Sanskrit: {verse_data['sanskrit']}")

    if verse_data.get('translation'):
        parts.append(f"Translation: {verse_data['translation']}")

    if verse_data.get('synonyms'):
        parts.append(f"Word meanings: {verse_data['synonyms']}")

    return "\n\n".join(parts)

def import_vedabase_to_d1(json_path: str, db_path: str):
    """Import Vedabase data into D1 database with proper chunking"""

    print(f"Loading Vedabase data from {json_path}...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Connecting to database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Apply schema
    print("Applying database schema...")
    with open('schema_vedabase.sql', 'r') as f:
        schema = f.read()
        cursor.executescript(schema)

    total_verses = 0
    total_chunks = 0

    # Book code mapping
    book_codes = {
        'bg': 'Bhagavad Gita',
        'sb1': 'Srimad Bhagavatam Canto 1',
        'sb2': 'Srimad Bhagavatam Canto 2',
        'sb3': 'Srimad Bhagavatam Canto 3',
        'kb': 'Krishna Book',
        'cc1': 'Caitanya Caritamrita Adi-lila',
        'cc2': 'Caitanya Caritamrita Madhya-lila',
        'cc3': 'Caitanya Caritamrita Antya-lila'
    }

    # Process each book
    for book_code, verses in data.items():
        if not verses:
            print(f"Skipping {book_code} (no verses)")
            continue

        print(f"\nProcessing {book_code}: {len(verses)} verses...")

        # Get book_id
        cursor.execute("SELECT id FROM books WHERE code = ?", (book_code,))
        result = cursor.fetchone()
        if not result:
            print(f"  ERROR: Book {book_code} not found in database!")
            continue
        book_id = result[0]

        # Process each verse
        for verse_data in verses:
            # Insert verse
            cursor.execute("""
                INSERT INTO verses (book_id, chapter, verse_number, sanskrit, synonyms, translation)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                book_id,
                verse_data.get('chapter', ''),
                verse_data.get('verse', ''),
                verse_data.get('sanskrit', ''),
                verse_data.get('synonyms', ''),
                verse_data.get('translation', '')
            ))
            verse_id = cursor.lastrowid
            total_verses += 1

            # Create verse text chunk (combines sanskrit, translation, synonyms)
            verse_text = create_verse_text_chunk(verse_data)
            if verse_text:
                cursor.execute("""
                    INSERT INTO chunks (verse_id, chunk_type, chunk_index, content, word_count)
                    VALUES (?, 'verse_text', 0, ?, ?)
                """, (verse_id, verse_text, count_words(verse_text)))
                total_chunks += 1

            # Split purport into paragraphs and create chunks
            purport = verse_data.get('purport', '')
            if purport:
                paragraphs = split_purport_into_paragraphs(purport)
                for idx, para in enumerate(paragraphs, start=1):
                    cursor.execute("""
                        INSERT INTO chunks (verse_id, chunk_type, chunk_index, content, word_count)
                        VALUES (?, 'purport_paragraph', ?, ?, ?)
                    """, (verse_id, idx, para, count_words(para)))
                    total_chunks += 1

        print(f"  ✓ Imported {len(verses)} verses")
        conn.commit()

    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  Total verses imported: {total_verses}")
    print(f"  Total chunks created: {total_chunks}")
    print(f"  Average chunks per verse: {total_chunks/total_verses:.1f}")
    print(f"{'='*60}")

    conn.close()
    print(f"\n✓ Database saved to {db_path}")

if __name__ == "__main__":
    import_vedabase_to_d1(
        json_path="vedabase_parsed.json",
        db_path="vedabase.db"
    )
