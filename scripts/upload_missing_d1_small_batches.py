#!/usr/bin/env python3
"""
Upload missing lecture segments with small batches (10 chunks) and robust retry logic
"""

import sqlite3
import subprocess
import time
import json
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 50  # Optimized batch size
PAUSE_BETWEEN_BATCHES = 2  # Reduced pause
MAX_RETRIES = 3  # Retry failed batches

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
            # Parse JSON output - look for the count value
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if '"count"' in line:
                    # Extract number after "count":
                    import re
                    match = re.search(r'"count":\s*(\d+)', line)
                    if match:
                        return int(match.group(1))
        return 0
    except Exception as e:
        print(f"Error getting remote count: {e}")
        return 0

def get_all_chunk_ids():
    """Get all lecture_segment chunk IDs from local DB"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vedabase_chunks WHERE chunk_type = 'lecture_segment' ORDER BY id")
    chunk_ids = [row[0] for row in cursor.fetchall()]

    conn.close()
    return chunk_ids

def get_chunks_by_ids(chunk_ids):
    """Get chunk data for specific IDs"""
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(chunk_ids))
    cursor.execute(f"""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE id IN ({placeholders})
        ORDER BY id
    """, chunk_ids)

    chunks = cursor.fetchall()
    conn.close()
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
            sql_file = f"temp_batch_{batch_num}.sql"
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

            # Cleanup temp file
            Path(sql_file).unlink(missing_ok=True)

            # Check for success
            if result.returncode == 0 and 'success' in result.stdout.lower():
                return True, None
            else:
                error = result.stderr if result.stderr else result.stdout
                if attempt < MAX_RETRIES - 1:
                    print(f"Retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                return False, error

        except subprocess.TimeoutExpired:
            if attempt < MAX_RETRIES - 1:
                print(f"Timeout, retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                time.sleep(2 ** attempt)
                continue
            return False, "Timeout"
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                print(f"Error, retry {attempt + 1}/{MAX_RETRIES}...", end=" ", flush=True)
                time.sleep(2 ** attempt)
                continue
            return False, str(e)

    return False, "Max retries exceeded"

def main():
    print("=" * 80)
    print("UPLOADING MISSING LECTURE SEGMENTS (SMALL BATCHES)")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s | Max retries: {MAX_RETRIES}")
    print("=" * 80)
    print()

    # Get current count
    print("📊 Checking current D1 status...")
    remote_count = get_remote_chunk_count()
    print(f"   Remote D1 has: {remote_count:,} lecture segments")

    # Get all local chunk IDs
    print("📂 Loading local chunk IDs...")
    all_chunk_ids = get_all_chunk_ids()
    total_chunks = len(all_chunk_ids)
    print(f"   Local DB has: {total_chunks:,} lecture segments")

    missing_count = total_chunks - remote_count
    print(f"   Estimated missing: {missing_count:,} chunks")
    print()

    # Upload all chunks (using INSERT OR REPLACE, so duplicates are fine)
    num_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 Uploading in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Estimated time: {(num_batches * (PAUSE_BETWEEN_BATCHES + 2)) / 60:.1f} minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch_chunk_ids = all_chunk_ids[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_chunks)

        print(f"[{batch_num}/{num_batches}] Chunks {i+1}-{batch_end}...", end=" ", flush=True)

        # Get chunk data
        batch_data = get_chunks_by_ids(batch_chunk_ids)

        # Upload batch
        success, error = upload_batch(batch_data, batch_num)

        if success:
            print("✅")
            success_count += len(batch_data)
        else:
            print(f"❌ {error[:50] if error else 'Unknown error'}")
            failed_batches.append(batch_num)

        # Pause between batches
        if batch_num < num_batches:
            time.sleep(PAUSE_BETWEEN_BATCHES)

        # Progress update every 100 batches
        if batch_num % 100 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / elapsed * 60 if elapsed > 0 else 0
            remaining = (num_batches - batch_num) / rate if rate > 0 else 0
            print(f"   Progress: {batch_num}/{num_batches} ({batch_num*100//num_batches}%) | Rate: {rate:.1f} batches/min | ETA: {remaining:.1f} min")

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Total chunks: {total_chunks:,}")
    print(f"  Batches processed: {num_batches}")
    print(f"  Successfully uploaded: {success_count:,}")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches ({len(failed_batches)}): {failed_batches[:20]}{'...' if len(failed_batches) > 20 else ''}")
    else:
        print("\n✅ All batches completed!")

    # Final verification
    print("\n🔍 Verifying final count...")
    final_count = get_remote_chunk_count()
    print(f"   D1 now has: {final_count:,} lecture segments")
    print(f"   Expected: {total_chunks:,}")

    if final_count >= total_chunks:
        print("\n🎉 SUCCESS! All lecture segments uploaded to D1!")
    else:
        print(f"\n⚠️  Still missing: {total_chunks - final_count:,} chunks")

if __name__ == '__main__':
    main()
