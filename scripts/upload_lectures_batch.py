#!/usr/bin/env python3
"""
Upload lecture data to remote D1 in batches (no transactions)
"""

import json
import subprocess
import time
from pathlib import Path

def execute_remote_sql_batch(sql_statements: list):
    """Execute multiple SQL statements on remote D1 (without transactions)"""
    # Combine into single SQL file
    sql = '\n'.join(sql_statements)

    # Write SQL to temp file
    with open('temp_batch.sql', 'w', encoding='utf-8') as f:
        f.write(sql)

    # Execute using wrangler
    result = subprocess.run(
        ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--file=temp_batch.sql', '--remote'],
        capture_output=True,
        text=True
    )

    Path('temp_batch.sql').unlink()  # Clean up

    if result.returncode != 0:
        return False, result.stderr

    return True, result.stdout

def upload_lectures():
    """Upload lecture data in small batches"""
    # Load export
    with open('lectures_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded export:")
    print(f"  Books: {len(data['books'])}")
    print(f"  Verses: {len(data['verses'])}")
    print(f"  Chunks: {len(data['chunks'])}")

    # 1. Upload books (small, can do all at once)
    print("\n1. Uploading books...")
    book_statements = []
    for book in data['books']:
        name = book['name'].replace("'", "''")
        book_statements.append(
            f"INSERT OR IGNORE INTO vedabase_books (id, code, name) VALUES ({book['id']}, '{book['code']}', '{name}');"
        )

    success, output = execute_remote_sql_batch(book_statements)
    if success:
        print(f"   ✓ Uploaded {len(data['books'])} books")
    else:
        print(f"   ✗ Failed to upload books: {output}")
        return

    # 2. Upload verses in batches of 25
    print("\n2. Uploading verses...")
    batch_size = 25
    verses = data['verses']
    total_uploaded = 0

    for i in range(0, len(verses), batch_size):
        batch = verses[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        statements = []
        for v in batch:
            chapter = v['chapter'].replace("'", "''") if v['chapter'] else ''
            verse_num = v['verse_number'].replace("'", "''") if v['verse_number'] else ''
            sanskrit = v['sanskrit'].replace("'", "''") if v['sanskrit'] else ''
            synonyms = v['synonyms'].replace("'", "''") if v['synonyms'] else ''
            translation = v['translation'].replace("'", "''") if v['translation'] else ''

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation) "
                f"VALUES ({v['id']}, {v['book_id']}, '{chapter}', '{verse_num}', '{sanskrit}', '{synonyms}', '{translation}');"
            )

        success, output = execute_remote_sql_batch(statements)
        if success:
            total_uploaded += len(batch)
            print(f"   Batch {batch_num}/{(len(verses) + batch_size - 1) // batch_size}: ✓ Uploaded {len(batch)} verses ({total_uploaded}/{len(verses)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            break

        time.sleep(0.5)  # Small delay between batches

    # 3. Upload chunks in batches of 25
    print("\n3. Uploading chunks...")
    chunks = data['chunks']
    total_uploaded = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        statements = []
        for c in batch:
            content = c['content'].replace("'", "''") if c['content'] else ''
            chunk_type = c['chunk_type'].replace("'", "''") if c['chunk_type'] else ''
            chunk_index = c['chunk_index'] if c['chunk_index'] is not None else 'NULL'

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({c['id']}, {c['verse_id']}, '{chunk_type}', {chunk_index}, '{content}', {c['word_count']});"
            )

        success, output = execute_remote_sql_batch(statements)
        if success:
            total_uploaded += len(batch)
            print(f"   Batch {batch_num}/{(len(chunks) + batch_size - 1) // batch_size}: ✓ Uploaded {len(batch)} chunks ({total_uploaded}/{len(chunks)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            break

        time.sleep(0.5)  # Small delay between batches

    print(f"\n✅ Upload complete!")

if __name__ == '__main__':
    upload_lectures()
