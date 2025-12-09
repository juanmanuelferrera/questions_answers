#!/usr/bin/env python3
"""
Delete old letter embeddings from Vectorize
"""

import requests
import os
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Cloudflare configuration
ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')
API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
VECTORIZE_INDEX = 'vedabase-embeddings'

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def delete_embeddings():
    """Delete letter embeddings from Vectorize"""

    print("=" * 80)
    print("DELETING OLD LETTER EMBEDDINGS FROM VECTORIZE")
    print("=" * 80)

    # Get actual letter chunk IDs from database
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM vedabase_books WHERE code = 'LETTERS'
    """)
    result = cursor.fetchone()

    if not result:
        print("Error: LETTERS book not found")
        return False

    book_id = result[0]

    cursor.execute("""
        SELECT c.id
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        WHERE v.book_id = ?
        ORDER BY c.id
    """, (book_id,))

    chunk_ids = [row[0] for row in cursor.fetchall()]
    conn.close()

    total_embeddings = len(chunk_ids)
    print(f"\nFound {total_embeddings} letter chunks to delete")

    # Delete in batches using Cloudflare API
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{VECTORIZE_INDEX}/delete-by-ids"
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }

    batch_size = 1000  # API max
    total_deleted = 0

    for i in range(0, len(chunk_ids), batch_size):
        batch = chunk_ids[i:i+batch_size]
        vector_ids = [f"letters_{chunk_id}" for chunk_id in batch]

        try:
            response = requests.post(url, headers=headers, json={"ids": vector_ids})
            response.raise_for_status()

            total_deleted += len(vector_ids)
            batch_num = i//batch_size + 1
            total_batches = (len(chunk_ids)-1)//batch_size + 1
            print(f"  ✓ Batch {batch_num}/{total_batches}: Deleted {len(vector_ids)} vectors ({total_deleted}/{total_embeddings})")

        except Exception as e:
            print(f"  ✗ Error deleting batch: {e}")
            if hasattr(e, 'response'):
                print(f"  Response: {e.response.text}")
            return False

    print("\n" + "=" * 80)
    print("DELETION COMPLETE")
    print("=" * 80)
    print(f"  ✓ {total_deleted} letter embeddings deleted from Vectorize")
    print("=" * 80)

    return True

if __name__ == '__main__':
    success = delete_embeddings()
    if not success:
        exit(1)
