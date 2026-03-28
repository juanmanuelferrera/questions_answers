#!/usr/bin/env python3
"""
Generate embeddings and upload to Vectorize with CORRECT metadata
- source: 'vedabase' (not 'vedabase_lectures')
- book_code: from joining verse -> book
"""

import json
import os
import sqlite3
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_embeddings_batch(texts: list) -> list:
    """Generate embeddings using OpenAI"""
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    return [item.embedding for item in response.data]

def main():
    """Generate embeddings for lecture chunks with correct metadata"""

    # Load lecture export
    with open('lectures_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data['chunks']
    print(f"Loaded {len(chunks)} lecture chunks")

    # Connect to local D1 to get book codes
    db_path = Path('.wrangler/state/v3/d1/miniflare-D1DatabaseObject')
    db_file = list(db_path.glob('*.sqlite'))[0]
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Build verse_id to book_code mapping
    print("Building verse_id to book_code mapping...")
    cursor.execute("""
        SELECT v.id, b.code
        FROM vedabase_verses v
        JOIN vedabase_books b ON v.book_id = b.id
        WHERE v.id >= 8482
    """)
    verse_to_book = dict(cursor.fetchall())
    print(f"Mapped {len(verse_to_book)} verses to book codes")

    conn.close()

    # Check for progress file
    progress_file = Path('lecture_vectorize_progress_fixed.json')
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            uploaded_count = progress.get('uploaded_count', 0)
            print(f"\nResuming from chunk ID: {chunks[uploaded_count]['id']}")
            print(f"Already uploaded: {uploaded_count} chunks")
    else:
        uploaded_count = 0
        progress = {'uploaded_count': 0}

    # Process remaining chunks
    remaining_chunks = chunks[uploaded_count:]

    if not remaining_chunks:
        print("\n✅ All chunks already uploaded!")
        return

    # Process in batches of 100
    batch_size = 100

    print(f"\nTotal chunks to upload: {len(remaining_chunks)}")
    print(f"Starting upload...\n")

    for i in range(0, len(remaining_chunks), batch_size):
        batch = remaining_chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        print(f"Batch {batch_num}: Processing chunk IDs {batch[0]['id']} to {batch[-1]['id']} ({len(batch)} chunks)")

        # Generate embeddings
        print("  Generating embeddings...")
        texts = [chunk['content'][:8000] for chunk in batch]
        embeddings = generate_embeddings_batch(texts)

        # Prepare for upload with CORRECT metadata
        vectors_data = []
        for chunk, embedding in zip(batch, embeddings):
            # Get book_code from mapping
            book_code = verse_to_book.get(chunk['verse_id'], 'UNKNOWN')

            vectors_data.append({
                'id': str(chunk['id']),
                'values': embedding,
                'metadata': {
                    'chunk_id': chunk['id'],
                    'verse_id': chunk['verse_id'],
                    'chunk_type': 'lecture_content',
                    'source': 'vedabase',  # FIXED: was 'vedabase_lectures'
                    'book_code': book_code  # ADDED: book code for filtering
                }
            })

        # Save to temp NDJSON
        temp_file = Path('temp_vectors.ndjson')
        with open(temp_file, 'w') as f:
            for vector in vectors_data:
                f.write(json.dumps(vector) + '\n')

        # Upload using wrangler
        print("  Uploading to Vectorize...")
        import subprocess

        result = subprocess.run(
            ['npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors', '--file=temp_vectors.ndjson'],
            capture_output=True,
            text=True
        )

        # Clean up temp file (ignore if already deleted)
        try:
            temp_file.unlink()
        except FileNotFoundError:
            pass

        if result.returncode == 0:
            print(f"  ✓ Successfully uploaded {len(batch)} vectors")
            uploaded_count += len(batch)
            print(f"  Progress: {uploaded_count}/{len(chunks)} ({100 * uploaded_count / len(chunks):.1f}%)\n")

            # Update progress
            progress['uploaded_count'] = uploaded_count
            with open(progress_file, 'w') as f:
                json.dump(progress, f)
        else:
            print(f"  ✗ Upload failed for batch {batch_num}")
            print(f"  Error: {result.stderr}")
            print(f"  Stopping. Fix the issue and run again to resume.")
            return

    # Clean up progress file on completion
    if progress_file.exists():
        progress_file.unlink()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total chunks uploaded: {uploaded_count}")
    print("\nLecture embeddings fixed with correct metadata:")
    print("  - source: 'vedabase' (searchable!)")
    print("  - book_code: added for filtering")
    print("="*80)

if __name__ == '__main__':
    main()
