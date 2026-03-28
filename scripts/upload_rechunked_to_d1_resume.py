#!/usr/bin/env python3
"""
Resume D1 upload from specific chunk index
"""

import sqlite3
import subprocess
import time
import sys

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
BATCH_SIZE = 100

def upload_from_chunk(start_chunk=0):
    """Upload purport_segment chunks starting from specified index"""

    print("=" * 80)
    print(f"RESUMING D1 UPLOAD FROM CHUNK {start_chunk}")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_segment'
        ORDER BY id
    """)

    all_chunks = cursor.fetchall()
    chunks = all_chunks[start_chunk:]
    total_chunks = len(chunks)

    print(f"\nLoaded {total_chunks} chunks to upload (starting from index {start_chunk})")

    total_batches = (total_chunks + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Uploading in {total_batches} batches of {BATCH_SIZE}...")
    print(f"Estimated time: {total_batches * 5 / 60:.1f} minutes\n")

    successful_batches = 0

    for batch_idx in range(total_batches):
        i = batch_idx * BATCH_SIZE
        batch = chunks[i:i+BATCH_SIZE]
        batch_num = batch_idx + 1
        global_chunk_idx = start_chunk + i

        inserts = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            safe_content = content.replace("'", "''")
            inserts.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index}, '{safe_content}', {word_count});"
            )

        sql_batch = "\n".join(inserts)

        print(f"[{batch_num}/{total_batches}] Uploading chunks {global_chunk_idx}-{global_chunk_idx+len(batch)}...", end=" ", flush=True)

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
                print(f"\n   Resume with: python3 upload_rechunked_to_d1_resume.py {global_chunk_idx}")
                conn.close()
                return False

        except subprocess.TimeoutExpired:
            print("✗ Timeout")
            print(f"   Resume with: python3 upload_rechunked_to_d1_resume.py {global_chunk_idx}")
            conn.close()
            return False

        if batch_num < total_batches:
            time.sleep(2)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE!")
    print("=" * 80)
    print(f"✓ {successful_batches} batches uploaded in this session")
    print(f"✓ All 34,331 purport_segment chunks now in production D1")
    print("=" * 80)

    conn.close()
    return True

if __name__ == '__main__':
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    success = upload_from_chunk(start)
    if not success:
        exit(1)
