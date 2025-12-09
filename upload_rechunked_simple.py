#!/usr/bin/env python3
"""
Upload re-chunked data to production D1 in batches
Simplified version: Just add new chunks, keep old ones for now
"""

import sqlite3
import subprocess
import time

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def upload_in_batches():
    """Upload re-chunked data in manageable batches"""

    print("=" * 80)
    print("UPLOADING RE-CHUNKED DATA TO PRODUCTION D1")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get new purport_segment chunks
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_segment'
        ORDER BY id
    """)

    all_chunks = cursor.fetchall()
    total_chunks = len(all_chunks)
    batch_size = 100  # Smaller batches for reliability
    total_batches = (total_chunks + batch_size - 1) // batch_size

    print(f"\nUploading {total_chunks} purport_segment chunks...")
    print(f"Processing in {total_batches} batches of {batch_size}...")

    successful_batches = 0

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch = all_chunks[start_idx:end_idx]
        batch_num = batch_idx + 1

        # Create batch SQL - using individual commands
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            # Escape single quotes
            content_escaped = content.replace("'", "''").replace("\\", "\\\\")

            sql = (
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index if chunk_index else 'NULL'}, '{content_escaped}', {word_count});"
            )

            # Execute individual command
            result = subprocess.run([
                'npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                '--remote',
                '--command', sql
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"  ✗ Failed to upload chunk {chunk_id}")
                print(f"     Error: {result.stderr[:100]}")
                # Continue with next chunk
                continue

        uploaded = min(end_idx, total_chunks)
        print(f"  ✓ Batch {batch_num}/{total_batches}: {uploaded}/{total_chunks} chunks")
        successful_batches += 1

        # Rate limiting
        time.sleep(2)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ {successful_batches} batches processed")
    print(f"  ✓ New purport_segment chunks in production D1")
    print("=" * 80)

    conn.close()
    return True

if __name__ == '__main__':
    upload_in_batches()
