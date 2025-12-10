#!/usr/bin/env python3
"""
Identify and re-upload missing lecture_segment chunks to remote D1
"""

import sqlite3
import subprocess
import time
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100
PAUSE_BETWEEN_BATCHES = 3

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def get_remote_chunk_ids():
    """Get all lecture_segment chunk IDs from remote D1"""
    print("📥 Fetching existing chunk IDs from remote D1...")

    result = subprocess.run(
        ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
         '--remote', '--command',
         "SELECT id FROM vedabase_chunks WHERE chunk_type = 'lecture_segment'"],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        print(f"❌ Error fetching remote IDs: {result.stderr}")
        return set()

    # Parse JSON output
    try:
        output = json.loads(result.stdout)
        chunk_ids = set()
        for item in output:
            if 'results' in item:
                for row in item['results']:
                    chunk_ids.add(row['id'])
        print(f"✅ Found {len(chunk_ids):,} existing chunks in remote D1")
        return chunk_ids
    except Exception as e:
        print(f"❌ Error parsing remote IDs: {e}")
        return set()

def get_local_chunks():
    """Get all lecture_segment chunks from local DB"""
    print("📂 Loading lecture segments from local database...")

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'lecture_segment'
        ORDER BY id
    """)

    chunks = {}
    for row in cursor.fetchall():
        chunk_id = row[0]
        chunks[chunk_id] = row

    conn.close()
    print(f"✅ Found {len(chunks):,} lecture segments in local database")
    return chunks

def upload_missing_chunks():
    """Identify and upload missing chunks"""

    print("=" * 80)
    print("FIXING MISSING LECTURE SEGMENTS IN D1")
    print("=" * 80)
    print()

    # Get remote and local data
    remote_ids = get_remote_chunk_ids()
    local_chunks = get_local_chunks()

    # Find missing chunks
    local_ids = set(local_chunks.keys())
    missing_ids = local_ids - remote_ids

    print()
    print("=" * 80)
    print("📊 COMPARISON")
    print("=" * 80)
    print(f"  Local chunks:  {len(local_ids):,}")
    print(f"  Remote chunks: {len(remote_ids):,}")
    print(f"  Missing:       {len(missing_ids):,}")
    print("=" * 80)
    print()

    if not missing_ids:
        print("✅ No missing chunks! All lecture segments are in remote D1.")
        return

    # Sort missing IDs for organized upload
    missing_ids_sorted = sorted(missing_ids)
    missing_chunks = [local_chunks[chunk_id] for chunk_id in missing_ids_sorted]

    # Calculate batches
    total_chunks = len(missing_chunks)
    num_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📦 Uploading {total_chunks:,} missing chunks in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Estimated time: {(num_batches * (PAUSE_BETWEEN_BATCHES + 5)) / 60:.1f} minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = missing_chunks[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_chunks)

        print(f"[{batch_num}/{num_batches}] Uploading chunks {i+1}-{batch_end}...", end=" ", flush=True)

        # Build SQL INSERT statement
        values = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            escaped_content = escape_sql_string(content)
            chunk_index_str = str(chunk_index) if chunk_index is not None else 'NULL'
            word_count_str = str(word_count) if word_count is not None else 'NULL'

            values.append(f"({chunk_id}, {verse_id}, 'lecture_segment', {chunk_index_str}, {escaped_content}, {word_count_str})")

        sql = f"""
INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES {', '.join(values)};
"""

        # Write SQL to temp file
        sql_file = f"temp_missing_batch_{batch_num}.sql"
        with open(sql_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        # Execute via wrangler
        try:
            result = subprocess.run(
                ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                 '--remote', '--file', sql_file],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Check for success in stdout (not stderr!)
            if result.returncode == 0 and 'success' in result.stdout.lower():
                print("✅")
                success_count += len(batch)
            else:
                print("❌")
                print(f"   stdout: {result.stdout[:200]}")
                print(f"   stderr: {result.stderr[:200]}")
                failed_batches.append(batch_num)

        except subprocess.TimeoutExpired:
            print("⏱️  Timeout")
            failed_batches.append(batch_num)
        except Exception as e:
            print(f"❌ Error: {e}")
            failed_batches.append(batch_num)
        finally:
            # Cleanup temp file
            Path(sql_file).unlink(missing_ok=True)

        # Pause between batches
        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Missing chunks found: {total_chunks:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//total_chunks if total_chunks > 0 else 0}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches: {failed_batches}")
        print("   You may want to retry these specific batches")
    else:
        print("\n✅ All missing chunks uploaded successfully!")
        print("\n🎉 D1 DATABASE NOW COMPLETE!")
        print(f"   Total lecture segments in D1: {len(remote_ids) + success_count:,}")

if __name__ == '__main__':
    upload_missing_chunks()
