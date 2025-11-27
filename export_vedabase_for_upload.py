#!/usr/bin/env python3
"""
Export Vedabase data to JSON for bulk upload to remote D1
Creates manageable JSON files for the Worker to import
"""

import sqlite3
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def export_vedabase_to_json():
    """Export all Vedabase data to JSON format"""

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    data = {
        'verses': [],
        'chunks': []
    }

    print("Exporting verses...")
    cursor.execute("""
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation
        FROM vedabase_verses
        ORDER BY id
    """)

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

    print(f"  Exported {len(data['verses'])} verses")

    print("Exporting chunks...")
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        ORDER BY id
    """)

    for row in cursor.fetchall():
        data['chunks'].append({
            'id': row[0],
            'verse_id': row[1],
            'chunk_type': row[2],
            'chunk_index': row[3],
            'content': row[4],
            'word_count': row[5]
        })

    print(f"  Exported {len(data['chunks'])} chunks")

    conn.close()

    # Save to file
    output_file = "vedabase_export_for_upload.json"
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"✓ Export complete: {file_size:.2f} MB")

    return data

if __name__ == "__main__":
    data = export_vedabase_to_json()

    print(f"\n{'='*60}")
    print(f"Export Summary:")
    print(f"  Verses: {len(data['verses'])}")
    print(f"  Chunks: {len(data['chunks'])}")
    print(f"  Ready for upload to remote D1")
    print(f"{'='*60}")
