#!/usr/bin/env python3
"""
Upload individual OTHER books to remote D1 in batches
"""

import json
import subprocess
import time
from pathlib import Path

def execute_remote_sql_batch(sql_statements: list):
    """Execute multiple SQL statements on remote D1"""
    sql = '\n'.join(sql_statements)

    with open('temp_batch.sql', 'w', encoding='utf-8') as f:
        f.write(sql)

    result = subprocess.run(
        ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--file=temp_batch.sql', '--remote'],
        capture_output=True,
        text=True
    )

    try:
        Path('temp_batch.sql').unlink()
    except FileNotFoundError:
        pass

    # Check for actual errors (not just warnings)
    if result.returncode != 0 and 'ERROR' in result.stderr:
        return False, result.stderr

    return True, result.stdout

def upload_individual_books():
    """Upload individual books data in batches"""
    with open('other_individual_export_for_upload.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("UPLOADING INDIVIDUAL OTHER BOOKS TO REMOTE D1")
    print("=" * 80)
    print(f"\nLoaded export:")
    print(f"  Books: {len(data['books'])}")
    print(f"  Verses: {len(data['verses'])}")
    print(f"  Chunks: {len(data['chunks'])}")

    # Upload books first
    print("\n1. Uploading book entries...")
    statements = []
    for book in data['books']:
        book_name = book['name'].replace("'", "''")
        statements.append(
            f"INSERT OR REPLACE INTO vedabase_books (id, code, name, created_at) "
            f"VALUES ({book['id']}, '{book['code']}', '{book_name}', datetime('now'));"
        )

    success, output = execute_remote_sql_batch(statements)
    if success:
        print(f"   ✓ Uploaded {len(data['books'])} book entries")
    else:
        print(f"   ✗ Failed - {output[:200]}")
        return

    # Upload verses in batches of 50
    print("\n2. Uploading verses...")
    batch_size = 50
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
            total_batches = (len(verses) + batch_size - 1) // batch_size
            print(f"   Batch {batch_num}/{total_batches}: ✓ Uploaded {len(batch)} verses ({total_uploaded}/{len(verses)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            return

        time.sleep(0.3)

    # Upload chunks in batches of 50
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

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({c['id']}, {c['verse_id']}, '{chunk_type}', {c['chunk_index']}, '{content}', {c['word_count']});"
            )

        success, output = execute_remote_sql_batch(statements)
        if success:
            total_uploaded += len(batch)
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            print(f"   Batch {batch_num}/{total_batches}: ✓ Uploaded {len(batch)} chunks ({total_uploaded}/{len(chunks)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            return

        time.sleep(0.3)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  Books uploaded: {len(data['books'])}")
    print(f"  Verses uploaded: {len(data['verses'])}")
    print(f"  Chunks uploaded: {len(data['chunks'])}")
    print("=" * 80)

if __name__ == '__main__':
    upload_individual_books()
