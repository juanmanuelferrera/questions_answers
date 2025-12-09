#!/usr/bin/env python3
"""
Upload re-chunked data to production D1 in batches
"""

import sqlite3
import subprocess
import time

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def upload_in_batches():
    """Upload re-chunked data in manageable batches"""

    print("=" * 80)
    print("UPLOADING RE-CHUNKED DATA TO PRODUCTION D1 (BATCHED)")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Step 1: Delete old purport_paragraph chunks
    print("\nStep 1: Deleting old purport_paragraph chunks...")
    delete_sql = "DELETE FROM vedabase_chunks WHERE chunk_type = 'purport_paragraph';"

    result = subprocess.run([
        'npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
        '--remote',
        '--command', delete_sql
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("  ✓ Old purport_paragraph chunks deleted")
    else:
        print(f"  ✗ Error deleting old chunks:")
        print(result.stderr)
        return False

    # Step 2: Upload new purport_segment chunks in batches
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_segment'
        ORDER BY id
    """)

    all_chunks = cursor.fetchall()
    total_chunks = len(all_chunks)
    batch_size = 500  # Smaller batches for reliability
    total_batches = (total_chunks + batch_size - 1) // batch_size

    print(f"\nStep 2: Uploading {total_chunks} new purport_segment chunks...")
    print(f"Processing in {total_batches} batches of {batch_size}...")

    successful_batches = 0

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch = all_chunks[start_idx:end_idx]
        batch_num = batch_idx + 1

        # Create batch SQL
        sql_statements = []
        for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in batch:
            # Escape single quotes
            content = content.replace("'", "''")
            sql_statements.append(
                f"INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count) "
                f"VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index if chunk_index else 'NULL'}, '{content}', {word_count});"
            )

        batch_sql = '\n'.join(sql_statements)

        # Write to temp file
        temp_file = f'temp_batch_{batch_num}.sql'
        with open(temp_file, 'w') as f:
            f.write(batch_sql)

        # Upload batch
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = subprocess.run([
                    'npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
                    '--remote',
                    '--file', temp_file
                ], capture_output=True, text=True, timeout=120)

                if result.returncode == 0:
                    uploaded = min(end_idx, total_chunks)
                    print(f"  ✓ Batch {batch_num}/{total_batches}: {uploaded}/{total_chunks} chunks")
                    successful_batches += 1
                    break
                else:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️  Batch {batch_num} failed (attempt {attempt + 1}/{max_retries}), retrying...")
                        time.sleep(5)
                    else:
                        print(f"  ✗ Batch {batch_num} failed after {max_retries} attempts")
                        print(f"     Error: {result.stderr[:200]}")
                        return False
            except subprocess.TimeoutExpired:
                if attempt < max_retries - 1:
                    print(f"  ⚠️  Batch {batch_num} timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(5)
                else:
                    print(f"  ✗ Batch {batch_num} timed out")
                    return False

        # Clean up temp file
        import os
        os.remove(temp_file)

        # Rate limiting
        time.sleep(1)

    print("\n" + "=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  ✓ {successful_batches} batches uploaded successfully")
    print(f"  ✓ {total_chunks} new purport_segment chunks in production D1")
    print("=" * 80)

    conn.close()
    return True

if __name__ == '__main__':
    success = upload_in_batches()
    if not success:
        exit(1)
