#!/usr/bin/env python3
"""
Upload Vedabase embeddings to Vectorize using wrangler CLI.
Generates embeddings and uploads via wrangler vectorize insert.
"""

import os
import sqlite3
import json
import time
import sys
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

# Configuration
LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
PROGRESS_FILE = "vectorize_upload_progress.json"
BATCH_SIZE = 100  # Upload 100 vectors at a time
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
VECTORIZE_INDEX = "philosophy-vectors"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def load_progress() -> Dict[str, Any]:
    """Load progress from file if it exists."""
    if Path(PROGRESS_FILE).exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_chunk_id': 0,
        'total_uploaded': 0,
        'started_at': datetime.now().isoformat(),
        'last_updated': None
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
        print(f"  Error generating embeddings: {e}")
        raise

def upload_to_vectorize_cli(vectors: List[Dict[str, Any]]) -> bool:
    """Upload vectors to Vectorize using wrangler CLI."""
    # Create NDJSON file for wrangler
    ndjson_file = "temp_vectors.ndjson"

    try:
        with open(ndjson_file, 'w') as f:
            for vec in vectors:
                vector_data = {
                    "id": f"vedabase_chunk_{vec['chunk_id']}",
                    "values": vec['embedding'],
                    "metadata": {
                        "source": "vedabase",
                        "chunk_id": vec['chunk_id'],
                        "verse_id": vec['verse_id'],
                        "book_code": vec['book_code'],
                        "book_name": vec['book_name'],
                        "chapter": vec['chapter'] or "",
                        "verse_number": vec['verse_number'],
                        "chunk_type": vec['chunk_type'],
                        "chunk_index": vec['chunk_index'] or 0,
                        "word_count": vec['word_count']
                    }
                }
                f.write(json.dumps(vector_data) + '\n')

        # Upload using wrangler
        env = os.environ.copy()
        if 'CLOUDFLARE_API_TOKEN' in env:
            del env['CLOUDFLARE_API_TOKEN']

        result = subprocess.run(
            ['npx', 'wrangler', 'vectorize', 'insert', VECTORIZE_INDEX,
             '--file', ndjson_file],
            capture_output=True,
            text=True,
            timeout=120,
            env=env
        )

        # Clean up temp file
        Path(ndjson_file).unlink()

        if result.returncode == 0:
            return True
        else:
            print(f"  Wrangler error: {result.stderr}")
            return False

    except Exception as e:
        print(f"  Error uploading to Vectorize: {e}")
        if Path(ndjson_file).exists():
            Path(ndjson_file).unlink()
        return False

def main():
    """Main execution function."""
    print("=" * 80)
    print("Vedabase Embeddings Upload to Vectorize")
    print("=" * 80)

    # Check for OpenAI API key
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
    print(f"\nTotal chunks to upload: {total_chunks:,}")

    # Load progress
    progress = load_progress()
    print(f"Resuming from chunk ID: {progress['last_chunk_id']}")
    print(f"Already uploaded: {progress['total_uploaded']:,} chunks")
    print()

    # Process in batches
    batch_num = 1

    try:
        while True:
            # Fetch next batch
            chunks = get_chunks_batch(conn, progress['last_chunk_id'], BATCH_SIZE)

            if not chunks:
                print("\nAll chunks uploaded!")
                break

            print(f"Batch {batch_num}: Processing chunk IDs {chunks[0]['id']} to {chunks[-1]['id']} ({len(chunks)} chunks)")

            # Generate embeddings
            texts = [chunk['content'] for chunk in chunks]
            print(f"  Generating embeddings...")
            embeddings = generate_embeddings(client, texts)

            # Prepare vectors
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

            # Upload to Vectorize
            print(f"  Uploading to Vectorize...")
            if upload_to_vectorize_cli(vectors):
                print(f"  ✓ Successfully uploaded {len(vectors)} vectors")
                progress['last_chunk_id'] = chunks[-1]['id']
                progress['total_uploaded'] += len(vectors)
                save_progress(progress)

                # Progress report
                percent_complete = (progress['total_uploaded'] / total_chunks) * 100
                print(f"  Progress: {progress['total_uploaded']:,}/{total_chunks:,} ({percent_complete:.1f}%)")
            else:
                print(f"  ✗ Upload failed for batch {batch_num}")
                print("  Stopping. Fix the issue and run again to resume.")
                break

            print()
            batch_num += 1

            # Rate limiting: wait 1 second between batches
            time.sleep(1)

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
    print(f"Total chunks uploaded: {progress['total_uploaded']:,}")
    print(f"Started at: {progress['started_at']}")
    print(f"Completed at: {datetime.now().isoformat()}")
    print("\nVedabase RAG is now ready for queries!")
    print("=" * 80)

if __name__ == "__main__":
    main()
