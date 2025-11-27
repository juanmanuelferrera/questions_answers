#!/usr/bin/env python3
"""
Generate embeddings for Vedabase chunks and upload to Cloudflare Vectorize.

This script:
1. Reads chunks from local D1 database
2. Generates embeddings in batches (respecting OpenAI rate limits)
3. Uploads directly to Vectorize via Cloudflare API
4. Tracks progress and supports resuming
"""

import os
import sqlite3
import json
import time
import sys
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import requests
from openai import OpenAI

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration
LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
PROGRESS_FILE = "vedabase_embedding_progress.json"
BATCH_SIZE = 100  # Process 100 chunks at a time
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# Cloudflare configuration (from environment variables)
ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID")
VECTORIZE_INDEX_ID = os.getenv("CLOUDFLARE_VECTORIZE_INDEX_ID", "philosophy-vectors")
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_progress() -> Dict[str, Any]:
    """Load progress from file if it exists."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_chunk_id': 0,
        'total_processed': 0,
        'total_uploaded': 0,
        'started_at': datetime.now().isoformat(),
        'last_updated': None,
        'batches_completed': []
    }

def save_progress(progress: Dict[str, Any]):
    """Save progress to file."""
    progress['last_updated'] = datetime.now().isoformat()
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_chunks_batch(conn: sqlite3.Connection, last_chunk_id: int, batch_size: int) -> List[Dict[str, Any]]:
    """Fetch a batch of chunks from the database."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            c.id,
            c.verse_id,
            c.chunk_type,
            c.chunk_index,
            c.content,
            c.word_count,
            v.book_id,
            v.chapter,
            v.verse_number,
            b.code as book_code,
            b.name as book_name
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE c.id > ?
        ORDER BY c.id
        LIMIT ?
    """, (last_chunk_id, batch_size))

    chunks = []
    for row in cursor.fetchall():
        chunks.append({
            'id': row[0],
            'verse_id': row[1],
            'chunk_type': row[2],
            'chunk_index': row[3],
            'content': row[4],
            'word_count': row[5],
            'book_id': row[6],
            'chapter': row[7],
            'verse_number': row[8],
            'book_code': row[9],
            'book_name': row[10]
        })

    return chunks

def generate_embeddings(client: OpenAI, texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI API."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            dimensions=EMBEDDING_DIMENSIONS
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        raise

def upload_to_vectorize(vectors: List[Dict[str, Any]]) -> bool:
    """Upload vectors to Cloudflare Vectorize."""
    if not ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
        print("Warning: Cloudflare credentials not set. Skipping Vectorize upload.")
        return False

    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{VECTORIZE_INDEX_ID}/insert"

    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Format vectors for Vectorize API
    formatted_vectors = []
    for vec in vectors:
        formatted_vectors.append({
            "id": f"vedabase_chunk_{vec['chunk_id']}",
            "values": vec['embedding'],
            "metadata": {
                "source": "vedabase",
                "chunk_id": vec['chunk_id'],
                "verse_id": vec['verse_id'],
                "book_code": vec['book_code'],
                "book_name": vec['book_name'],
                "chapter": vec['chapter'],
                "verse_number": vec['verse_number'],
                "chunk_type": vec['chunk_type'],
                "chunk_index": vec['chunk_index'],
                "word_count": vec['word_count']
            }
        })

    try:
        response = requests.post(url, headers=headers, json={"vectors": formatted_vectors})
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error uploading to Vectorize: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False

def process_batch(client: OpenAI, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a batch of chunks: generate embeddings and prepare for upload."""
    # Extract texts for embedding
    texts = [chunk['content'] for chunk in chunks]

    # Generate embeddings
    print(f"  Generating embeddings for {len(texts)} chunks...")
    embeddings = generate_embeddings(client, texts)

    # Combine chunks with embeddings
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        vectors.append({
            'chunk_id': chunk['id'],
            'verse_id': chunk['verse_id'],
            'book_code': chunk['book_code'],
            'book_name': chunk['book_name'],
            'chapter': chunk['chapter'],
            'verse_number': chunk['verse_number'],
            'chunk_type': chunk['chunk_type'],
            'chunk_index': chunk['chunk_index'],
            'word_count': chunk['word_count'],
            'embedding': embedding
        })

    return vectors

def main():
    """Main execution function."""
    print("=" * 80)
    print("Vedabase Embedding Generation & Upload")
    print("=" * 80)

    # Check for required environment variables
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Connect to database
    if not Path(LOCAL_DB).exists():
        print(f"Error: Database not found at {LOCAL_DB}")
        sys.exit(1)

    conn = sqlite3.connect(LOCAL_DB)

    # Get total chunk count
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM vedabase_chunks")
    total_chunks = cursor.fetchone()[0]
    print(f"\nTotal chunks to process: {total_chunks:,}")

    # Load progress
    progress = load_progress()
    print(f"Resuming from chunk ID: {progress['last_chunk_id']}")
    print(f"Already processed: {progress['total_processed']:,} chunks")
    print()

    # Process in batches
    batch_num = len(progress['batches_completed']) + 1

    try:
        while True:
            # Fetch next batch
            chunks = get_chunks_batch(conn, progress['last_chunk_id'], BATCH_SIZE)

            if not chunks:
                print("\nAll chunks processed!")
                break

            print(f"Batch {batch_num}: Processing chunk IDs {chunks[0]['id']} to {chunks[-1]['id']} ({len(chunks)} chunks)")

            # Generate embeddings
            vectors = process_batch(client, chunks)

            # Upload to Vectorize
            print(f"  Uploading to Vectorize...")
            upload_success = upload_to_vectorize(vectors)

            if upload_success:
                print(f"  ✓ Successfully uploaded {len(vectors)} vectors")
            else:
                print(f"  ⚠ Vectorize upload skipped (credentials not set)")

            # Update progress
            progress['last_chunk_id'] = chunks[-1]['id']
            progress['total_processed'] += len(chunks)
            progress['total_uploaded'] += len(vectors) if upload_success else 0
            progress['batches_completed'].append({
                'batch_num': batch_num,
                'chunk_ids': f"{chunks[0]['id']}-{chunks[-1]['id']}",
                'count': len(chunks),
                'uploaded': upload_success,
                'timestamp': datetime.now().isoformat()
            })
            save_progress(progress)

            # Progress report
            percent_complete = (progress['total_processed'] / total_chunks) * 100
            print(f"  Progress: {progress['total_processed']:,}/{total_chunks:,} ({percent_complete:.1f}%)")
            print()

            # Rate limiting: wait 1 second between batches to respect OpenAI limits
            if chunks:  # If there are more chunks to process
                time.sleep(1)

            batch_num += 1

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        print(f"Resume by running this script again.")
        save_progress(progress)
        sys.exit(0)

    except Exception as e:
        print(f"\n\nError: {e}")
        print("Progress saved. Fix the issue and run again to resume.")
        save_progress(progress)
        raise

    finally:
        conn.close()

    # Final summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total chunks processed: {progress['total_processed']:,}")
    print(f"Total vectors uploaded: {progress['total_uploaded']:,}")
    print(f"Batches completed: {len(progress['batches_completed'])}")
    print(f"Started at: {progress['started_at']}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("\nVedabase RAG is now ready for queries!")
    print("=" * 80)

if __name__ == "__main__":
    main()
