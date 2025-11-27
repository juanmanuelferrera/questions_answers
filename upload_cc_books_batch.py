#!/usr/bin/env python3
"""
Upload CC books (Caitanya Caritamrita) to remote D1 in batches
Uploads CC1, CC2, CC3 verses and chunks
"""

import json
import subprocess
import time
from pathlib import Path

def execute_remote_sql_batch(sql_statements: list):
    """Execute multiple SQL statements on remote D1"""
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

    # Clean up (ignore if file doesn't exist)
    try:
        Path('temp_batch.sql').unlink()
    except FileNotFoundError:
        pass

    # Only treat it as failure if the return code is non-zero
    # (wrangler outputs warnings to stderr which we can ignore)
    if result.returncode != 0:
        return False, result.stderr

    return True, result.stdout

def upload_cc_books():
    """Upload CC books data in batches"""
    # Load export
    with open('cc_books_export_for_upload.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("=" * 80)
    print("UPLOADING CC BOOKS TO REMOTE D1")
    print("=" * 80)
    print(f"\nLoaded export:")
    print(f"  CC Verses: {len(data['verses'])}")
    print(f"  CC Chunks: {len(data['chunks'])}")

    # Upload verses in batches of 25
    print("\n1. Uploading CC verses...")
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
            total_batches = (len(verses) + batch_size - 1) // batch_size
            print(f"   Batch {batch_num}/{total_batches}: ✓ Uploaded {len(batch)} verses ({total_uploaded}/{len(verses)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            return

        time.sleep(0.5)  # Small delay between batches

    # Upload chunks in batches of 25
    print("\n2. Uploading CC chunks...")
    chunks = data['chunks']
    total_uploaded = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        statements = []
        for c in batch:
            content = c['content'].replace("'", "''") if c['content'] else ''
            chunk_type = c['chunk_type'].replace("'", "''") if c['chunk_type'] else ''
            chunk_index = c['chunk_index'] if c['chunk_index'] is not None else 0

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({c['id']}, {c['verse_id']}, '{chunk_type}', {chunk_index}, '{content}', {c['word_count']});"
            )

        success, output = execute_remote_sql_batch(statements)
        if success:
            total_uploaded += len(batch)
            total_batches = (len(chunks) + batch_size - 1) // batch_size
            print(f"   Batch {batch_num}/{total_batches}: ✓ Uploaded {len(batch)} chunks ({total_uploaded}/{len(chunks)} total)")
        else:
            print(f"   Batch {batch_num}: ✗ Failed - {output[:200]}")
            return

        time.sleep(0.5)  # Small delay between batches

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  CC Verses uploaded: {len(verses)}")
    print(f"  CC Chunks uploaded: {len(chunks)}")
    print("=" * 80)

if __name__ == '__main__':
    upload_cc_books()
