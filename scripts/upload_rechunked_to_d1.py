#!/usr/bin/env python3
"""
Upload re-chunked data to production D1
This will:
1. Delete old purport_paragraph chunks that were split
2. Upload new purport_segment chunks
"""

import sqlite3
import subprocess

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def upload_rechunked_data():
    """Upload re-chunked data to production D1"""

    print("=" * 80)
    print("UPLOADING RE-CHUNKED DATA TO PRODUCTION D1")
    print("=" * 80)

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get purport_segment chunks (new chunks)
    cursor.execute("""
        SELECT id, verse_id, chunk_type, chunk_index, content, word_count
        FROM vedabase_chunks
        WHERE chunk_type = 'purport_segment'
        ORDER BY id
    """)

    new_chunks = cursor.fetchall()
    print(f"\nFound {len(new_chunks)} new purport_segment chunks to upload")

    # Create SQL statements
    sql_statements = []

    # First, delete old purport_paragraph chunks (they've been replaced)
    sql_statements.append("""
-- Delete old purport_paragraph chunks that were re-chunked
DELETE FROM vedabase_chunks WHERE chunk_type = 'purport_paragraph';
""")

    # Then insert new purport_segment chunks
    for chunk_id, verse_id, chunk_type, chunk_index, content, word_count in new_chunks:
        # Escape single quotes
        content = content.replace("'", "''")

        sql_statements.append(f"""
INSERT OR REPLACE INTO vedabase_chunks (id, verse_id, chunk_type, chunk_index, content, word_count)
VALUES ({chunk_id}, {verse_id}, '{chunk_type}', {chunk_index if chunk_index else 'NULL'}, '{content}', {word_count});
""")

    # Save to file
    sql_file = "rechunked_data.sql"
    with open(sql_file, 'w') as f:
        f.write('\n'.join(sql_statements))

    print(f"\nGenerated SQL file: {sql_file}")
    print(f"  - Delete old purport_paragraph chunks")
    print(f"  - Insert {len(new_chunks)} new purport_segment chunks")

    # Execute on production D1
    print("\nUploading to production D1...")
    result = subprocess.run([
        'npx', 'wrangler', 'd1', 'execute', 'philosophy-db',
        '--remote',
        '--file', sql_file
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\n" + "=" * 80)
        print("UPLOAD COMPLETE")
        print("=" * 80)
        print(f"  ✓ Re-chunked data uploaded to production D1")
        print(f"  ✓ {len(new_chunks)} new chunks in database")
        print("=" * 80)
    else:
        print(f"\n✗ Error uploading to D1:")
        print(result.stderr)
        return False

    conn.close()
    return True

if __name__ == '__main__':
    success = upload_rechunked_data()
    if not success:
        exit(1)
