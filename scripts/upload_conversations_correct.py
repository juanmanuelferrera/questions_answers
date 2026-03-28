#!/usr/bin/env python3
"""
Upload CORRECT conversation data to remote D1
Uses explicit verse ID range 53439-54482
"""

import sqlite3
import subprocess
import time
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 50
PAUSE_BETWEEN_BATCHES = 2
MAX_RETRIES = 3

# CORRECT verse ID range for Conversations
MIN_VERSE_ID = 53439
MAX_VERSE_ID = 54482

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def upload_batch(sql_statements, batch_num, batch_type):
    """Upload a batch of SQL statements with retry logic"""

    for attempt in range(MAX_RETRIES):
        try:
            # Write SQL to temp file
            sql_file = f"temp_{batch_type}_batch_{batch_num}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(sql_statements))

            # Execute via wrangler
            result = subprocess.run(
                ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                 '--remote', '--file', sql_file],
                capture_output=True,
                text=True,
                timeout=90
            )

            Path(sql_file).unlink(missing_ok=True)

            # Check for success in stdout
            if result.returncode == 0 and 'success' in result.stdout.lower():
                return True, None
            else:
                if attempt < MAX_RETRIES - 1:
                    print(f"Retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                    time.sleep(2 ** attempt)
                    continue
                return False, result.stderr if result.stderr else result.stdout[:100]

        except subprocess.TimeoutExpired:
            if attempt < MAX_RETRIES - 1:
                print(f"Timeout retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                time.sleep(2 ** attempt)
                continue
            return False, "Timeout"
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                time.sleep(2 ** attempt)
                continue
            return False, str(e)[:100]

    return False, "Max retries exceeded"

def main():
    print("=" * 80)
    print("UPLOADING CORRECT CONVERSATIONS TO REMOTE D1")
    print("=" * 80)
    print(f"Verse ID range: {MIN_VERSE_ID}-{MAX_VERSE_ID}")
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s")
    print("=" * 80)
    print()

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Step 1: Upload book entry
    print("📚 Step 1/3: Uploading Conversations book entry...")
    book_sql = "INSERT OR REPLACE INTO vedabase_books (id, code, name, created_at) VALUES (45, 'conversations', 'Conversations', CURRENT_TIMESTAMP);"
    success, error = upload_batch([book_sql], 0, "book")
    if success:
        print("✅ Book entry uploaded")
    else:
        print(f"❌ Failed: {error}")
        return
    print()

    # Step 2: Upload verses WITH CORRECT ID RANGE
    print("📖 Step 2/3: Uploading conversation verses...")
    cursor.execute(f"""
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at
        FROM vedabase_verses
        WHERE id >= {MIN_VERSE_ID} AND id <= {MAX_VERSE_ID}
        ORDER BY id
    """)

    verses = cursor.fetchall()
    num_verses = len(verses)

    # Verify we got the correct data
    if num_verses == 0:
        print(f"❌ ERROR: No verses found in range {MIN_VERSE_ID}-{MAX_VERSE_ID}!")
        return

    # Check first verse to confirm it's Conversations
    first_verse = verses[0]
    print(f"   First verse preview: ID={first_verse[0]}, chapter={first_verse[2]}, verse={first_verse[3]}")
    if 'conversation' not in str(first_verse[2]).lower() and 'morning' not in str(first_verse[2]).lower():
        print(f"   ⚠️  WARNING: First verse doesn't look like Conversations!")
        print(f"   Chapter: {first_verse[2]}")

    num_verse_batches = (num_verses + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Total verses: {num_verses:,}")
    print(f"   Batches: {num_verse_batches}")
    print()

    verse_success = 0
    verse_failed = []

    for i in range(0, num_verses, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = verses[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, num_verses)

        print(f"[{batch_num}/{num_verse_batches}] Verses {i+1}-{batch_end}...", end=" ", flush=True)

        # Build SQL statements
        sql_statements = []
        for verse_id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at in batch:
            sql = f"""INSERT OR REPLACE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at)
VALUES ({verse_id}, {book_id}, {escape_sql_string(chapter)}, {escape_sql_string(verse_number)}, {escape_sql_string(sanskrit)}, {escape_sql_string(synonyms)}, {escape_sql_string(translation)}, {escape_sql_string(created_at)});"""
            sql_statements.append(sql)

        success, error = upload_batch(sql_statements, batch_num, "verse")

        if success:
            print("✅")
            verse_success += len(batch)
        else:
            print(f"❌ {error[:50] if error else 'Unknown error'}")
            verse_failed.append(batch_num)

        if batch_num < num_verse_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

    print()
    print(f"✅ Verses: {verse_success}/{num_verses} uploaded")
    print()

    # Step 3: Upload chunks
    print("💬 Step 3/3: Uploading conversation chunks...")
    cursor.execute(f"""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE verse_id >= {MIN_VERSE_ID} AND verse_id <= {MAX_VERSE_ID}
        ORDER BY id
    """)

    chunks = cursor.fetchall()
    num_chunks = len(chunks)

    if num_chunks == 0:
        print(f"❌ ERROR: No chunks found for verse range {MIN_VERSE_ID}-{MAX_VERSE_ID}!")
        return

    # Sample first chunk to verify content
    first_chunk = chunks[0]
    print(f"   First chunk preview: {first_chunk[4][:80]}...")

    num_chunk_batches = (num_chunks + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"   Total chunks: {num_chunks:,}")
    print(f"   Batches: {num_chunk_batches}")
    print()

    chunk_success = 0
    chunk_failed = []
    start_time = time.time()

    for i in range(0, num_chunks, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = chunks[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, num_chunks)

        print(f"[{batch_num}/{num_chunk_batches}] Chunks {i+1}-{batch_end}...", end=" ", flush=True)

        # Build SQL statements
        sql_statements = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            chunk_index_str = str(chunk_index) if chunk_index is not None else 'NULL'
            word_count_str = str(word_count) if word_count is not None else 'NULL'
            sql = f"""INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index_str}, {escape_sql_string(content)}, {word_count_str});"""
            sql_statements.append(sql)

        success, error = upload_batch(sql_statements, batch_num, "chunk")

        if success:
            print("✅")
            chunk_success += len(batch)
        else:
            print(f"❌ {error[:50] if error else 'Unknown error'}")
            chunk_failed.append(batch_num)

        if batch_num < num_chunk_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

        # Progress update every 50 batches
        if batch_num % 50 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60 if elapsed > 0 else 0
            remaining = (num_chunk_batches - batch_num) / rate if rate > 0 else 0
            print(f"   Progress: {batch_num}/{num_chunk_batches} ({batch_num*100//num_chunk_batches}%) | Rate: {rate:.1f} batches/min | ETA: {remaining:.1f} min")

    elapsed = time.time() - start_time
    conn.close()

    print()
    print("=" * 80)
    print("D1 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Book entry: ✅ Uploaded")
    print(f"  Verses: {verse_success}/{num_verses} ({verse_success*100//num_verses if num_verses > 0 else 0}%)")
    print(f"  Chunks: {chunk_success}/{num_chunks} ({chunk_success*100//num_chunks if num_chunks > 0 else 0}%)")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if verse_failed or chunk_failed:
        print()
        if verse_failed:
            print(f"⚠️  Failed verse batches: {verse_failed[:10]}")
        if chunk_failed:
            print(f"⚠️  Failed chunk batches: {chunk_failed[:10]}")
    else:
        print()
        print("✅ CORRECT conversations uploaded successfully to remote D1!")
        print("🎉 Janice Johnson content is now available!")

if __name__ == '__main__':
    main()
