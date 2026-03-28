#!/usr/bin/env python3
"""
Fast D1 retry - targets 1 hour completion
Batch size: 100, Pause: 1s, Total batches: ~250
"""

import sqlite3
import subprocess
import time
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100  # Larger batches for speed
PAUSE_BETWEEN_BATCHES = 1  # Minimal pause
MAX_RETRIES = 3  # Standard retries

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def get_remote_chunk_count():
    """Get count of lecture_segment chunks in remote D1"""
    try:
        result = subprocess.run(
            ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
             '--remote', '--command',
             "SELECT COUNT(*) as count FROM vedabase_chunks WHERE chunk_type = 'lecture_segment'"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            import re
            match = re.search(r'"count":\s*(\d+)', result.stdout)
            if match:
                return int(match.group(1))
        return 0
    except Exception as e:
        print(f"Error getting remote count: {e}")
        return 0

def get_remote_chunk_ids():
    """Get all lecture_segment chunk IDs from remote D1"""
    print("📥 Fetching existing chunk IDs from remote D1...")

    try:
        result = subprocess.run(
            ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
             '--remote', '--command',
             "SELECT id FROM vedabase_chunks WHERE chunk_type = 'lecture_segment'"],
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

        print(f"✅ Found {len(ids):,} existing chunks in remote D1")
        return ids
    except Exception as e:
        print(f"❌ Error: {e}")
        return set()

def get_all_local_chunks():
    """Get all lecture_segment chunks from local DB"""
    print("📂 Loading all lecture segments from local database...")

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

def upload_batch(batch, batch_num):
    """Upload a single batch with retry logic"""

    for attempt in range(MAX_RETRIES):
        try:
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
            sql_file = f"fast_retry_batch_{batch_num}.sql"
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(sql)

            # Execute via wrangler
            result = subprocess.run(
                ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                 '--remote', '--file', sql_file],
                capture_output=True,
                text=True,
                timeout=60
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
    print("FAST D1 RETRY - 1 HOUR TARGET")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s | Max retries: {MAX_RETRIES}")
    print("=" * 80)
    print()

    # Get current remote count
    print("📊 Checking current D1 status...")
    remote_count = get_remote_chunk_count()
    print(f"   Remote D1 has: {remote_count:,} lecture segments")
    print()

    # Get remote chunk IDs
    remote_ids = get_remote_chunk_ids()

    # Get all local chunks
    local_chunks = get_all_local_chunks()
    local_ids = set(local_chunks.keys())

    # Find missing chunks
    missing_ids = local_ids - remote_ids
    missing_count = len(missing_ids)

    print()
    print("=" * 80)
    print("📊 COMPARISON")
    print("=" * 80)
    print(f"  Local chunks:  {len(local_ids):,}")
    print(f"  Remote chunks: {len(remote_ids):,}")
    print(f"  Missing:       {missing_count:,}")
    print("=" * 80)
    print()

    if missing_count == 0:
        print("✅ No missing chunks! All lecture segments are in remote D1.")
        print("🎉 D1 DATABASE COMPLETE!")
        return

    # Sort missing IDs and prepare for upload
    missing_ids_sorted = sorted(missing_ids)
    missing_chunks = [local_chunks[chunk_id] for chunk_id in missing_ids_sorted]

    # Calculate batches
    num_batches = (missing_count + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"📦 Uploading {missing_count:,} missing chunks in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Target time: ~60 minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, missing_count, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = missing_chunks[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, missing_count)

        print(f"[{batch_num}/{num_batches}] Chunks {i+1}-{batch_end}...", end=" ", flush=True)

        # Upload batch
        success, error = upload_batch(batch, batch_num)

        if success:
            print("✅")
            success_count += len(batch)
        else:
            print(f"❌ {error}")
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
    print("📊 FAST RETRY SUMMARY")
    print("=" * 80)
    print(f"  Missing chunks found: {missing_count:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//missing_count if missing_count > 0 else 0}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches ({len(failed_batches)}): {failed_batches[:30]}{'...' if len(failed_batches) > 30 else ''}")
    else:
        print("\n✅ All missing chunks uploaded successfully!")

    # Final verification
    print("\n🔍 Verifying final count...")
    final_count = get_remote_chunk_count()
    print(f"   D1 now has: {final_count:,} lecture segments")
    print(f"   Expected: {len(local_ids):,}")

    if final_count >= len(local_ids):
        print("\n🎉 SUCCESS! All lecture segments uploaded to D1!")
        print("\n✅ D1 DATABASE NOW COMPLETE!")
    else:
        print(f"\n⚠️  Still missing: {len(local_ids) - final_count:,} chunks")

if __name__ == '__main__':
    main()
