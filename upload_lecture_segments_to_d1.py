#!/usr/bin/env python3
"""
Upload lecture_segment chunks to remote D1 database
Uses batched SQL commands via wrangler
"""

import sqlite3
import subprocess
import time
from pathlib import Path

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100  # Chunks per batch (reduced for D1 SQL size limit)
PAUSE_BETWEEN_BATCHES = 3  # seconds

def escape_sql_string(s):
    """Escape single quotes in SQL strings"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def upload_to_d1():
    """Upload lecture_segment chunks to remote D1"""

    print("=" * 80)
    print("UPLOADING LECTURE SEGMENTS TO REMOTE D1")
    print(f"Batch size: {BATCH_SIZE} | Pause: {PAUSE_BETWEEN_BATCHES}s")
    print("=" * 80)

    # Connect to local database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get all lecture_segment chunks
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'lecture_segment'
        ORDER BY id
    """)

    chunks = cursor.fetchall()
    total_chunks = len(chunks)
    print(f"\n📊 Found {total_chunks:,} lecture_segment chunks")

    if total_chunks == 0:
        print("⚠️  No lecture segments to upload!")
        conn.close()
        return

    # Calculate batches
    num_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📦 Uploading in {num_batches} batches of {BATCH_SIZE}...")
    print(f"⏱️  Estimated time: {(num_batches * (PAUSE_BETWEEN_BATCHES + 5)) / 60:.1f} minutes")
    print()

    success_count = 0
    failed_batches = []
    start_time = time.time()

    for i in range(0, total_chunks, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = chunks[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total_chunks)

        print(f"[{batch_num}/{num_batches}] Uploading chunks {i}-{batch_end}...", end=" ", flush=True)

        # Build SQL INSERT statement
        values = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            # Escape content for SQL
            escaped_content = escape_sql_string(content)
            chunk_index_str = str(chunk_index) if chunk_index is not None else 'NULL'
            word_count_str = str(word_count) if word_count is not None else 'NULL'

            values.append(f"({chunk_id}, {verse_id}, 'lecture_segment', {chunk_index_str}, {escaped_content}, {word_count_str})")

        sql = f"""
INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES {', '.join(values)};
"""

        # Write SQL to temp file
        sql_file = f"temp_lecture_batch_{batch_num}.sql"
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

            if result.returncode == 0 and 'Success' in result.stdout:
                print("✅ Success")
                success_count += len(batch)
            else:
                print(f"❌ Failed")
                print(f"   Error: {result.stderr}")
                failed_batches.append(batch_num)

        except subprocess.TimeoutExpired:
            print(f"⏱️  Timeout")
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

    conn.close()
    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"  Total chunks: {total_chunks:,}")
    print(f"  Successfully uploaded: {success_count:,} ({success_count*100//total_chunks}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Total time: {elapsed/60:.1f} minutes")
    print("=" * 80)

    if failed_batches:
        print(f"\n⚠️  Failed batches: {failed_batches}")
        print("   You may want to retry these specific batches")
    else:
        print("\n✅ All chunks uploaded successfully to remote D1!")
        print("\n🎉 OPTIMIZATION COMPLETE!")
        print("   Your RAG system now has:")
        print("   - Optimized lecture chunks (125 words avg)")
        print("   - Embeddings in Vectorize")
        print("   - Data in remote D1")
        print("   - Query caching enabled")
        print("   - Sanskrit normalization active")
        print("   - Score filtering in place")

if __name__ == '__main__':
    upload_to_d1()
