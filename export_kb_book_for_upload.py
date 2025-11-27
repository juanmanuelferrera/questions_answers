#!/usr/bin/env python3
"""
Export only KB books (Caitanya Caritamrita) data for upload to remote D1
Exports only verses/chunks added for KB1, KB2, KB3
"""

import sqlite3
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def export_kb_to_json():
    """Export only KB books data to JSON format"""

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get KB book IDs
    cursor.execute("SELECT id, code FROM vedabase_books WHERE code = 'kb'")
    kb_books = {code: book_id for book_id, code in cursor.fetchall()}

    print(f"Found KB book IDs: {kb_books}")

    data = {
        'verses': [],
        'chunks': []
    }

    # Export verses for KB books only
    print("\nExporting KB verses...")
    for code, book_id in kb_books.items():
        cursor.execute("""
            SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation
            FROM vedabase_verses
            WHERE book_id = ?
            ORDER BY id
        """, (book_id,))

        count = 0
        for row in cursor.fetchall():
            data['verses'].append({
                'id': row[0],
                'book_id': row[1],
                'chapter': row[2],
                'verse_number': row[3],
                'sanskrit': row[4],
                'synonyms': row[5],
                'translation': row[6]
            })
            count += 1

        print(f"  {code.upper()}: {count} verses")

    print(f"\n  Total KB verses: {len(data['verses'])}")

    # Export chunks for KB books only
    print("\nExporting KB chunks...")
    cursor.execute("""
        SELECT c.id, c.verse_id, c.chunk_type, c.chunk_index, c.content, c.word_count
        FROM vedabase_chunks c
        INNER JOIN vedabase_verses v ON c.verse_id = v.id
        WHERE v.book_id = ?
        ORDER BY c.id
    """, (list(kb_books.values())[0],))

    for row in cursor.fetchall():
        data['chunks'].append({
            'id': row[0],
            'verse_id': row[1],
            'chunk_type': row[2],
            'chunk_index': row[3],
            'content': row[4],
            'word_count': row[5]
        })

    print(f"  Total KB chunks: {len(data['chunks'])}")

    conn.close()

    # Save to file
    output_file = "kb_books_export_for_upload.json"
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"✓ Export complete: {file_size:.2f} MB")

    return data

if __name__ == "__main__":
    print("=" * 80)
    print("EXPORTING KB BOOKS FOR UPLOAD")
    print("=" * 80)

    data = export_kb_to_json()

    print(f"\n{'='*80}")
    print(f"Export Summary:")
    print(f"  KB Verses: {len(data['verses'])}")
    print(f"  KB Chunks: {len(data['chunks'])}")
    print(f"  Ready for upload to remote D1")
    print(f"{'='*80}")
