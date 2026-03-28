#!/usr/bin/env python3
"""
Upload re-chunked data to production D1 in small batches
Uses wrangler d1 execute with inline SQL
"""

import sqlite3
import subprocess
import time

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100  # Small batches to avoid hitting size limits

def upload_to_d1():
    """Upload purport_segment chunks to production D1 in batches"""

    print("=" * 80)
    print("UPLOADING RE-CHUNKED DATA TO PRODUCTION D1")
    print("=" * 80)

    # Connect to local database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get all purport_segment chunks
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_segment'
        ORDER BY id
    """)

    chunks = cursor.fetchall()
    total_chunks = len(chunks)
    print(f"\nFound {total_chunks} purport_segment chunks to upload")

    # Calculate batches
    total_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Uploading in {total_batches} batches of {BATCH_SIZE}...")
    print(f"Estimated time: {total_batches * 5 / 60:.1f} minutes\n")

    successful_batches = 0

    for batch_idx in range(total_batches):
        i = batch_idx * BATCH_SIZE
        batch = chunks[i:i+BATCH_SIZE]
        batch_num = batch_idx + 1

        # Build INSERT statements for this batch
        inserts = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            # Escape single quotes in content
            safe_content = content.replace("'", "''")
            inserts.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index}, '{safe_content}', {word_count});"
            )

        sql_batch = "\n".join(inserts)

        print(f"[{batch_num}/{total_batches}] Uploading chunks {i}-{i+len(batch)}...", end=" ", flush=True)

        # Execute batch with wrangler
        try:
            result = subprocess.run([
                'npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                '--remote',
                '--command', sql_batch
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                print("✓ Success")
                successful_batches += 1
            else:
                print("✗ Failed")
                print(f"   Error: {result.stderr[:200]}")
                print(f"\n   Resume with: python3 upload_rechunked_to_d1_batched.py {i}")
                return False

        except subprocess.TimeoutExpired:
            print("✗ Timeout")
            print(f"   Resume with: python3 upload_rechunked_to_d1_batched.py {i}")
            return False

        # Small pause between batches
        if batch_num < total_batches:
            time.sleep(2)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE!")
    print("=" * 80)
    print(f"✓ {successful_batches} batches uploaded")
    print(f"✓ {total_chunks} purport_segment chunks in production D1")
    print("=" * 80)

    conn.close()
    return True

if __name__ == '__main__':
    import sys
    success = upload_to_d1()
    if not success:
        exit(1)
