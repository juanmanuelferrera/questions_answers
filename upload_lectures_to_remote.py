#!/usr/bin/env python3
"""
Upload lecture data from local D1 to remote D1 using wrangler d1 execute
"""

import sqlite3
import json
import subprocess
from pathlib import Path

def get_local_db():
    """Get connection to local D1 database"""
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject')
    db_files = list(db_path.glob('*.sqlite'))
    if not db_files:
        raise FileNotFoundError(f"No D1 database found in {db_path}")
    return sqlite3.connect(db_files[0])

def execute_remote_sql(sql: str):
    """Execute SQL on remote D1 database"""
    # Write SQL to temp file
    with open('temp_upload.sql', 'w') as f:
        f.write(sql)

    # Execute using wrangler
    result = subprocess.run(
        ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--file=temp_upload.sql', '--remote'],
        capture_output=True,
        text=True
    )

    Path('temp_upload.sql').unlink()  # Clean up

    if result.returncode != 0:
        raise Exception(f"Wrangler error: {result.stderr}")

    return result.stdout

def upload_lectures():
    """Upload lecture data to remote D1"""
    conn = get_local_db()
    cursor = conn.cursor()

    # Get lecture books (IDs 9+)
    cursor.execute('SELECT id, code, name FROM vedabase_books WHERE id >= 9 ORDER BY id')
    lecture_books = cursor.fetchall()

    print(f"Found {len(lecture_books)} lecture books to upload")

    # Upload books first
    print("\n1. Uploading books...")
    book_sql = "BEGIN TRANSACTION;\n"
    for book_id, code, name in lecture_books:
        escaped_name = name.replace("'", "''")
        book_sql += f"INSERT OR IGNORE INTO vedabase_books (id, code, name) VALUES ({book_id}, '{code}', '{escaped_name}');\n"
    book_sql += "COMMIT;"

    execute_remote_sql(book_sql)
    print(f"   ✓ Uploaded {len(lecture_books)} books")

    # Upload verses and chunks in batches
    print("\n2. Uploading verses and chunks...")

    # Get verses for lecture books (IDs 8482+)
    cursor.execute('''
        SELECT v.id, v.book_id, v.chapter, v.verse_number, v.sanskrit, v.synonyms, v.translation
        FROM vedabase_verses v
        WHERE v.id >= 8482
        ORDER BY v.id
    ''')

    verses = cursor.fetchall()
    print(f"   Found {len(verses)} lecture verses to upload")

    # Upload in batches of 50
    batch_size = 50
    total_uploaded = 0

    for i in range(0, len(verses), batch_size):
        batch = verses[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        sql = "BEGIN TRANSACTION;\n"

        for verse_id, book_id, chapter, verse_num, sanskrit, synonyms, translation in batch:
            # Escape single quotes
            chapter = chapter.replace("'", "''") if chapter else ''
            verse_num = verse_num.replace("'", "''") if verse_num else ''
            sanskrit = sanskrit.replace("'", "''") if sanskrit else ''
            synonyms = synonyms.replace("'", "''") if synonyms else ''
            translation = translation.replace("'", "''") if translation else ''

            sql += f"""INSERT OR REPLACE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation)
VALUES ({verse_id}, {book_id}, '{chapter}', '{verse_num}', '{sanskrit}', '{synonyms}', '{translation}');\n"""

        # Get chunks for these verses
        verse_ids = [v[0] for v in batch]
        placeholders = ','.join('?' * len(verse_ids))
        cursor.execute(f'''
            SELECT id, verse_id, chunk_type, chunk_index, content, word_count
            FROM vedabase_chunks
            WHERE verse_id IN ({placeholders})
            ORDER BY id
        ''', verse_ids)

        chunks = cursor.fetchall()

        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in chunks:
            content = content.replace("'", "''") if content else ''
            chunk_type = chunk_type.replace("'", "''") if chunk_type else ''
            chunk_index_val = chunk_index if chunk_index is not None else 'NULL'

            sql += f"""INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index_val}, '{content}', {word_count});\n"""

        sql += "COMMIT;"

        # Execute batch
        try:
            execute_remote_sql(sql)
            total_uploaded += len(batch)
            print(f"   Batch {batch_num}/{(len(verses) + batch_size - 1) // batch_size}: Uploaded {len(batch)} verses + {len(chunks)} chunks ({total_uploaded}/{len(verses)} total)")
        except Exception as e:
            print(f"   ✗ Batch {batch_num} failed: {e}")
            break

    conn.close()

    print(f"\n✅ Upload complete!")
    print(f"   Total verses uploaded: {total_uploaded}")

if __name__ == '__main__':
    upload_lectures()
