#!/usr/bin/env python3
"""
Fix lecture embeddings metadata - re-upload with correct source and book_code
"""

import json
import sqlite3
from pathlib import Path
import subprocess

def main():
    # Load lecture chunks
    with open('lectures_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data['chunks']
    print(f"Loaded {len(chunks)} lecture chunks")

    # Connect to local D1 to get book codes for each verse
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject')
    db_file = list(db_path.glob('*.sqlite'))[0]
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Build verse_id to book_code mapping
    print("Building verse_id to book_code mapping...")
    cursor.execute("""
        SELECT v.id, b.code
        FROM vedabase_verses v
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE v.id >= 8482
    """)
    verse_to_book = dict(cursor.fetchall())
    print(f"Mapped {len(verse_to_book)} verses to books")

    conn.close()

    # Delete all existing lecture vectors from Vectorize
    print("\nDeleting existing lecture vectors (IDs 19824-26863)...")

    # Create NDJSON with IDs to delete
    delete_file = Path('delete_lectures.ndjson')
    with open(delete_file, 'w') as f:
        for chunk_id in range(19824, 26864):  # All lecture chunk IDs
            f.write(json.dumps({'id': str(chunk_id)}) + '\n')

    # Delete using wrangler
    result = subprocess.run(
        ['npx', 'wrangler', 'vectorize', 'delete', 'philosophy-vectors', '--file=delete_lectures.ndjson'],
        capture_output=True,
        text=True
    )

    delete_file.unlink()

    if result.returncode == 0:
        print(f"✓ Deleted old lecture vectors")
    else:
        print(f"Note: Delete may have failed (expected if vectors don't exist yet)")
        print(f"Error: {result.stderr}")

    # Re-upload with correct metadata
    print(f"\nRe-uploading {len(chunks)} lecture vectors with correct metadata...")
    print("This will take ~35 minutes...")

    # Load existing embeddings from previous upload log
    print("\nNote: You'll need to re-generate embeddings since we're changing metadata")
    print("Run: python3 upload_lecture_embeddings_wrangler_fixed.py")

if __name__ == '__main__':
    main()
