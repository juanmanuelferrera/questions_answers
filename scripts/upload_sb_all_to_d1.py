#!/usr/bin/env python3
"""
Upload ALL Vedabase data (Cantos 1-10) from local D1 to remote D1
"""

import os
import sqlite3
import subprocess
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100  # Verses per batch

def upload_all_vedabase():
    """Upload all Vedabase books, verses, and chunks to remote D1"""

    print("=" * 80)
    print("UPLOADING ALL VEDABASE DATA TO PRODUCTION D1")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Step 1: Upload books
    print("\n[1/3] Uploading books...")
    cursor.execute("SELECT code, name FROM vedabase_books WHERE code LIKE 'sb%' ORDER BY code")
    books = cursor.fetchall()

    books_sql = []
    for code, name in books:
        books_sql.append(f"""
INSERT OR IGNORE INTO vedabase_books (code, name) VALUES ('{code}', '{name.replace("'", "''")}');
""")

    # Upload books
    if books_sql:
        result = subprocess.run([
            'npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--remote',
            '--command', '\n'.join(books_sql)
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Error uploading books: {result.stderr}")
            return False
        print(f"✓ Uploaded {len(books)} books")

    # Step 2: Get verse count and upload in batches
    print("\n[2/3] Uploading verses and chunks...")
    cursor.execute("SELECT COUNT(*) FROM vedabase_verses v JOIN vedabase_books b ON v.book_id = b.id WHERE b.code LIKE 'sb%'")
    total_verses = cursor.fetchone()[0]
    print(f"Total verses to upload: {total_verses}")

    uploaded = 0
    batch_num = 0

    # Get verses in batches
    cursor.execute("""
        SELECT v.id, b.code, v.chapter, v.verse_number, v.sanskrit, v.synonyms, v.translation
        FROM vedabase_verses v
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE b.code LIKE 'sb%'
        ORDER BY v.id
    """)

    all_verses = cursor.fetchall()

    for i in range(0, len(all_verses), BATCH_SIZE):
        batch = all_verses[i:i+BATCH_SIZE]
        batch_num += 1

        sql_statements = []

        for verse_data in batch:
            verse_id, book_code, chapter, verse_num, sanskrit, synonyms, translation = verse_data

            # Escape quotes
            chapter = (chapter or '').replace("'", "''")
            verse_num = (verse_num or '').replace("'", "''")
            sanskrit = (sanskrit or '').replace("'", "''")
            synonyms = (synonyms or '').replace("'", "''")
            translation = (translation or '').replace("'", "''")

            # Insert verse
            sql_statements.append(f"""
INSERT OR IGNORE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation)
SELECT {verse_id}, id, '{chapter}', '{verse_num}', '{sanskrit}', '{synonyms}', '{translation}'
FROM vedabase_books WHERE code = '{book_code}';
""")

            # Get chunks for this verse
            cursor.execute("""
                SELECT id, chunk_type, chunk_index, content, word_count
                FROM vedabase_chunks
                WHERE verse_id = ?
                ORDER BY id
            """, (verse_id,))

            chunks = cursor.fetchall()

            for chunk_id, chunk_type, chunk_index, content, word_count in chunks:
                content = (content or '').replace("'", "''")
                chunk_index_val = chunk_index if chunk_index is not None else 'NULL'
                word_count_val = word_count if word_count is not None else 0

                sql_statements.append(f"""
INSERT OR IGNORE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index_val}, '{content}', {word_count_val});
""")

        # Upload batch
        if sql_statements:
            result = subprocess.run([
                'npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--remote',
                '--command', '\n'.join(sql_statements)
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"  ✗ Batch {batch_num} failed: {result.stderr}")
                continue

            uploaded += len(batch)
            print(f"  ✓ Batch {batch_num}: {uploaded}/{total_verses} verses ({uploaded*100//total_verses}%)")

    conn.close()

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ Books: {len(books)}")
    print(f"  ✓ Verses: {uploaded}")
    print("=" * 80)

    return True

if __name__ == '__main__':
    success = upload_all_vedabase()
    if not success:
        exit(1)
