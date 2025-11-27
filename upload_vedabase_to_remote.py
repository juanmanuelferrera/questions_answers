#!/usr/bin/env python3
"""
Upload Vedabase data from local D1 to remote D1 in batches
Handles the 8,481 verses and 19,823 chunks
"""

import os
import sqlite3
import subprocess
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 50  # Upload in batches of 50 verses (smaller to avoid D1 limits)

def get_verse_count():
    """Get total verse count"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vedabase_verses")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def export_verses_batch(offset, limit):
    """Export a batch of verses with their chunks as INSERT statements"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get verses in this batch
    cursor.execute("""
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at
        FROM vedabase_verses
        ORDER BY id
        LIMIT ? OFFSET ?
    """, (limit, offset))

    verses = cursor.fetchall()

    sql_statements = []

    for verse in verses:
        verse_id, book_id, chapter, verse_num, sanskrit, synonyms, translation, created_at = verse

        # Escape single quotes in text
        chapter = chapter.replace("'", "''") if chapter else ''
        verse_num = verse_num.replace("'", "''") if verse_num else ''
        sanskrit = sanskrit.replace("'", "''") if sanskrit else ''
        synonyms = synonyms.replace("'", "''") if synonyms else ''
        translation = translation.replace("'", "''") if translation else ''

        # Insert verse (OR IGNORE to skip duplicates)
        sql_statements.append(f"""
INSERT OR IGNORE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at)
VALUES ({verse_id}, {book_id}, '{chapter}', '{verse_num}', '{sanskrit}', '{synonyms}', '{translation}', '{created_at}');
""")

        # Get chunks for this verse
        cursor.execute("""
            SELECT id, chunk_type, chunk_index, content, word_count, created_at
            FROM vedabase_chunks
            WHERE verse_id = ?
            ORDER BY chunk_index
        """, (verse_id,))

        chunks = cursor.fetchall()

        for chunk in chunks:
            chunk_id, chunk_type, chunk_index, content, word_count, chunk_created = chunk

            # Escape single quotes
            content = content.replace("'", "''") if content else ''
            chunk_index_val = chunk_index if chunk_index is not None else 'NULL'

            sql_statements.append(f"""
INSERT OR IGNORE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count, created_at)
VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index_val}, '{content}', {word_count}, '{chunk_created}');
""")

    conn.close()
    return sql_statements

def upload_batch_to_remote(sql_statements, batch_num):
    """Upload a batch of SQL statements to remote D1"""

    # Save to temp file
    temp_file = f"temp_batch_{batch_num}.sql"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    print(f"  Uploading batch {batch_num} ({len(sql_statements)} statements)...")

    # Execute on remote D1
    # Clear CLOUDFLARE_API_TOKEN from environment to use OAuth
    try:
        env = os.environ.copy()
        if 'CLOUDFLARE_API_TOKEN' in env:
            del env['CLOUDFLARE_API_TOKEN']

        result = subprocess.run(
            ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--remote', f'--file={temp_file}'],
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )

        if result.returncode == 0:
            print(f"  ✓ Batch {batch_num} uploaded successfully")
            Path(temp_file).unlink()  # Delete temp file
            return True
        else:
            print(f"  ✗ Batch {batch_num} failed:")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print(f"  ✗ Batch {batch_num} timed out")
        return False

def main():
    total_verses = get_verse_count()
    print(f"Found {total_verses} verses in local DB")

    # Using INSERT OR IGNORE, so we can safely upload from beginning
    # Duplicates will be skipped automatically
    print("Using INSERT OR IGNORE to skip duplicates automatically\n")

    start_from_id = 1
    remaining_verses = total_verses
    total_batches = (remaining_verses + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Will upload {remaining_verses} verses in {total_batches} batches of {BATCH_SIZE} each\n")

    successful_batches = 0
    failed_batches = 0

    for batch_num in range(total_batches):
        offset = (start_from_id - 1) + (batch_num * BATCH_SIZE)

        print(f"Processing batch {batch_num + 1}/{total_batches} (verses {offset + 1}-{min(offset + BATCH_SIZE, total_verses)})...")

        sql_statements = export_verses_batch(offset, BATCH_SIZE)

        if upload_batch_to_remote(sql_statements, batch_num + 1):
            successful_batches += 1
        else:
            failed_batches += 1
            print(f"  Stopping due to error. You can retry from batch {batch_num + 1}")
            break

    print(f"\n{'='*60}")
    print(f"Upload Summary:")
    print(f"  Successful batches: {successful_batches}/{total_batches}")
    print(f"  Failed batches: {failed_batches}")
    print(f"  Total verses uploaded: ~{successful_batches * BATCH_SIZE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
