#!/usr/bin/env python3
"""
Upload letters to remote Cloudflare D1 in batches
"""

import json
import subprocess
import time

def upload_batch(statements, batch_num, total_batches):
    """Upload a batch of SQL statements"""
    sql = '; '.join(statements) + ';'

    result = subprocess.run(
        ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--remote',
         '--command=' + sql],
        capture_output=True,
        text=True
    )

    # Check for actual errors (not just warnings)
    if result.returncode != 0 and 'ERROR' in result.stderr:
        return False, result.stderr

    return True, None

def upload_letters():
    """Upload letters to remote D1"""

    print("=" * 80)
    print("UPLOADING LETTERS TO REMOTE D1")
    print("=" * 80)

    with open('letters_export_for_upload.json', 'r') as f:
        data = json.load(f)

    book = data['book']
    verses = data['verses']
    chunks = data['chunks']

    print(f"\nBook: {book['name']} (ID: {book['id']})")
    print(f"Letters: {len(verses)}")
    print(f"Chunks: {len(chunks)}")

    # 1. Upload book
    print("\n1. Uploading book...")
    book_name = book['name'].replace("'", "''")
    statements = [
        f"INSERT OR REPLACE INTO vedabase_books (id, code, name, created_at) "
        f"VALUES ({book['id']}, '{book['code']}', '{book_name}', datetime('now'))"
    ]

    success, error = upload_batch(statements, 1, 1)
    if not success:
        print(f"✗ Failed to upload book: {error}")
        return
    print("  ✓ Book uploaded")

    # 2. Upload verses (letters) in batches
    print("\n2. Uploading letters...")
    batch_size = 500
    total_batches = (len(verses) + batch_size - 1) // batch_size

    for i in range(0, len(verses), batch_size):
        batch = verses[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        statements = []
        for v in batch:
            recipient = v['recipient'].replace("'", "''") if v['recipient'] else ''
            date = v['date'].replace("'", "''") if v['date'] else ''
            chapter = v['chapter'].replace("'", "''")

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_verses "
                f"(id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at) "
                f"VALUES ({v['id']}, {v['book_id']}, '{chapter}', '{v['verse_number']}', "
                f"'', '{recipient}', '{date}', datetime('now'))"
            )

        success, error = upload_batch(statements, batch_num, total_batches)
        if not success:
            print(f"  ✗ Batch {batch_num}/{total_batches} failed: {error}")
            return

        print(f"  ✓ Batch {batch_num}/{total_batches}: {len(batch)} letters")
        time.sleep(0.5)

    # 3. Upload chunks in batches
    print("\n3. Uploading chunks...")
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        statements = []
        for c in batch:
            content = c['content'].replace("'", "''")
            chunk_type = c['chunk_type']

            statements.append(
                f"INSERT OR REPLACE INTO vedabase_chunks "
                f"(id, verse_id, chunk_type, content, created_at) "
                f"VALUES ({c['id']}, {c['verse_id']}, '{chunk_type}', '{content}', datetime('now'))"
            )

        success, error = upload_batch(statements, batch_num, total_batches)
        if not success:
            print(f"  ✗ Batch {batch_num}/{total_batches} failed: {error}")
            return

        uploaded = min(i + batch_size, len(chunks))
        print(f"  ✓ Batch {batch_num}/{total_batches}: {uploaded}/{len(chunks)} chunks")
        time.sleep(0.5)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ Book uploaded: {book['name']}")
    print(f"  ✓ {len(verses)} letters uploaded")
    print(f"  ✓ {len(chunks)} chunks uploaded")
    print("=" * 80)

if __name__ == '__main__':
    upload_letters()
