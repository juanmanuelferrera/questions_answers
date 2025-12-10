#!/usr/bin/env python3
"""
Upload missing vedabase_verses to remote D1
This fixes the FOREIGN KEY constraint issue preventing lecture segment uploads
"""

import sqlite3
import subprocess
import time
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100  # Verses are smaller than chunks
PAUSE_BETWEEN_BATCHES = 2
MAX_RETRIES = 3

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def get_remote_verse_ids():
    """Get all verse IDs from remote D1"""
    print("📥 Fetching existing verse IDs from remote D1...")

    try:
        result = subprocess.run(
            ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
             '--remote', '--command',
             "SELECT id FROM vedabase_verses"],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            print(f"❌ Error fetching remote IDs")
            return set()

        # Parse output - extract IDs from JSON-like output
        import re
        ids = set()
        for match in re.finditer(r'"id":\s*(\d+)', result.stdout):
            ids.add(int(match.group(1)))

        print(f"✅ Found {len(ids):,} existing verses in remote D1")
        return ids
    except Exception as e:
        print(f"❌ Error: {e}")
        return set()

def get_all_local_verses():
    """Get all verses from local DB"""
    print("📂 Loading all verses from local database...")

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at
        FROM vedabase_verses
        ORDER BY id
    """)

    verses = {}
    for row in cursor.fetchall():
        verse_id = row[0]
        verses[verse_id] = row

    conn.close()
    print(f"✅ Found {len(verses):,} verses in local database")
    return verses

def upload_batch(batch, batch_num):
    """Upload a single batch with retry logic"""

    for attempt in range(MAX_RETRIES):
        try:
            # Build SQL INSERT statement
            values = []
            for verse_id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at in batch:
                book_id_str = str(book_id) if book_id is not None else 'NULL'
                escaped_chapter = escape_sql_string(chapter)
                escaped_verse_number = escape_sql_string(verse_number)
                escaped_sanskrit = escape_sql_string(sanskrit)
                escaped_synonyms = escape_sql_string(synonyms)
                escaped_translation = escape_sql_string(translation)
                escaped_created_at = escape_sql_string(created_at)

                values.append(f"({verse_id}, {book_id_str}, {escaped_chapter}, {escaped_verse_number}, {escaped_sanskrit}, {escaped_synonyms}, {escaped_translation}, {escaped_created_at})")

            sql = f"""
INSERT OR REPLACE INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at)
VALUES {', '.join(values)};
"""
            # Write SQL to temp file
            sql_file = f"temp_verses_batch_{batch_num}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql)

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
    print("UPLOADING MISSING VEDABASE VERSES TO D1")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s | Max retries: {MAX_RETRIES}")
    print("=" * 80)
    print()

    # Get remote verse IDs
    remote_ids = get_remote_verse_ids()

    # Get all local verses
    local_verses = get_all_local_verses()
    local_ids = set(local_verses.keys())

    # Find missing verses
    missing_ids = local_ids - remote_ids
    missing_count = len(missing_ids)

    print()
    print("=" * 80)
    print("📊 COMPARISON")
    print("=" * 80)
    print(f"  Local verses:  {len(local_ids):,}")
    print(f"  Remote verses: {len(remote_ids):,}")
    print(f"  Missing:       {missing_count:,}")
    print("=" * 80)
    print()

    if missing_count == 0:
        print("✅ No missing verses! All verses are in remote D1.")
        print("🎉 VERSES COMPLETE - Ready to upload lecture segments!")
        return

    # Sort missing IDs and prepare for upload
    missing_ids_sorted = sorted(missing_ids)
    missing_verses = [local_verses[verse_id] for verse_id in missing_ids_sorted]

    # Calculate batches
    num_batches = (missing_count + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📦 Uploading {missing_count:,} missing verses in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Estimated time: {(num_batches * (PAUSE_BETWEEN_BATCHES + 5)) / 60:.1f} minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, missing_count, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = missing_verses[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, missing_count)

        print(f"[{batch_num}/{num_batches}] Verses {i+1}-{batch_end}...", end=" ", flush=True)

        # Upload batch
        success, error = upload_batch(batch, batch_num)

        if success:
            print("✅")
            success_count += len(batch)
        else:
            print(f"❌ {error[:50] if error else 'Unknown error'}")
            failed_batches.append(batch_num)

        # Pause between batches
        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

        # Progress update every 25 batches
        if batch_num % 25 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60 if elapsed > 0 else 0
            remaining = (num_batches - batch_num) / rate if rate > 0 else 0
            print(f"   Progress: {batch_num}/{num_batches} ({batch_num*100//num_batches}%) | Rate: {rate:.1f} batches/min | ETA: {remaining:.1f} min")

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("📊 VERSES UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Missing verses found: {missing_count:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//missing_count if missing_count > 0 else 0}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches ({len(failed_batches)}): {failed_batches[:20]}{'...' if len(failed_batches) > 20 else ''}")
    else:
        print("\n✅ All missing verses uploaded successfully!")
        print("\n🎉 VERSES COMPLETE - Now ready to upload lecture segments!")

if __name__ == '__main__':
    main()
