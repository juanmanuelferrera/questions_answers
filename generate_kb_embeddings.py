#!/usr/bin/env python3
"""
Generate embeddings for KB books (Caitanya Caritamrita) chunks
Generates embeddings for the 3,868 KB chunks using OpenAI API
"""

import json
import sqlite3
import os
from pathlib import Path
from typing import List, Dict
import requests
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, will use system env vars

LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"

def generate_embeddings(texts: List[str], api_key: str, batch_size: int = 100) -> List[List[float]]:
    """Generate embeddings using OpenAI API"""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        response = requests.post(
            'https://api.openai.com/v1/embeddings',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'text-embedding-3-small',
                'input': batch
            }
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        data = response.json()
        embeddings = [item['embedding'] for item in data['data']]
        all_embeddings.extend(embeddings)

        print(f"  Generated embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        time.sleep(0.5)  # Rate limiting

    return all_embeddings

def main():
    print("=" * 80)
    print("GENERATING KB BOOK EMBEDDINGS")
    print("=" * 80)

    # Get OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    # Connect to local D1
    if not Path(LOCAL_DB).exists():
        print(f"Error: Database not found at {LOCAL_DB}")
        return

    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    # Get KB book IDs
    cursor.execute("SELECT id FROM vedabase_books WHERE code = 'kb'")
    kb_book_ids = [row[0] for row in cursor.fetchall()]

    print(f"\nFound KB book IDs: {kb_book_ids}")

    if not kb_book_ids:
        print("Error: Krishna Book (kb) not found in database")
        return

    # Get all KB chunks
    print("\nFetching KB chunks from database...")
    cursor.execute("""
        SELECT
            c.id,
            c.verse_id,
            c.chunk_type,
            c.content,
            v.book_id,
            b.code as book_code
        FROM vedabase_chunks c
        JOIN vedabase_verses v ON c.verse_id = v.id
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE v.book_id = ?
        ORDER BY c.id
    """, (kb_book_ids[0],))

    chunks = []
    for row in cursor.fetchall():
        chunks.append({
            'id': row[0],
            'verse_id': row[1],
            'chunk_type': row[2],
            'content': row[3],
            'book_id': row[4],
            'book_code': row[5]
        })

    conn.close()

    print(f"  Found {len(chunks)} KB chunks")

    # Generate embeddings
    print(f"\nGenerating embeddings using OpenAI (text-embedding-3-small)...")
    texts = [chunk['content'] for chunk in chunks]
    embeddings = generate_embeddings(texts, api_key, batch_size=100)

    print(f"  ✓ Generated {len(embeddings)} embeddings")

    # Prepare data for upload
    print("\nPreparing data for Vectorize upload...")
    vectors_data = []

    for i, chunk in enumerate(chunks):
        vectors_data.append({
            'id': chunk['id'],
            'verse_id': chunk['verse_id'],
            'chunk_type': chunk['chunk_type'],
            'book_code': chunk['book_code'],
            'embedding': embeddings[i]
        })

    # Save to file
    output_file = 'kb_embeddings_export.json'
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump({
            'chunks': vectors_data,
            'total': len(vectors_data)
        }, f, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {file_size:.2f} MB")

    # Calculate cost
    # text-embedding-3-small: $0.020 per 1M tokens
    # Estimate: ~200 tokens per chunk average
    estimated_tokens = len(chunks) * 200
    estimated_cost = (estimated_tokens / 1_000_000) * 0.020

    print("\n" + "=" * 80)
    print("EMBEDDING GENERATION COMPLETE")
    print("=" * 80)
    print(f"  Total chunks: {len(chunks)}")
    print(f"  Total embeddings: {len(embeddings)}")
    print(f"  Estimated tokens: {estimated_tokens:,}")
    print(f"  Estimated cost: ${estimated_cost:.4f}")
    print(f"  Output file: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
