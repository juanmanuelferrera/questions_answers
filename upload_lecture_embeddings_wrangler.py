#!/usr/bin/env python3
"""
Generate embeddings and upload to Vectorize using the same method as original vedabase upload
"""

import json
import os
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
    """Generate embeddings for lecture chunks"""

    # Load lecture export
    with open('lectures_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data['chunks']
    print(f"Loaded {len(chunks)} lecture chunks")

    # Check for progress file
    progress_file = Path('lecture_vectorize_progress.json')
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            uploaded_count = progress.get('uploaded_count', 0)
            print(f"\nResuming from chunk ID: {uploaded_count + 1}")
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
    total_batches = (len(remaining_chunks) + batch_size - 1) // batch_size

    print(f"\nTotal chunks to upload: {len(remaining_chunks)}")
    print(f"Starting upload...\n")

    for i in range(0, len(remaining_chunks), batch_size):
        batch = remaining_chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1

        print(f"Batch {batch_num}: Processing chunk IDs {batch[0]['id']} to {batch[-1]['id']} ({len(batch)} chunks)")

        # Generate embeddings
        print("  Generating embeddings...")
        texts = [chunk['content'][:8000] for chunk in batch]  # Truncate if needed
        embeddings = generate_embeddings_batch(texts)

        # Prepare for upload (save to temp file for wrangler)
        vectors_data = []
        for chunk, embedding in zip(batch, embeddings):
            vectors_data.append({
                'id': str(chunk['id']),
                'values': embedding,
                'metadata': {
                    'chunk_id': chunk['id'],
                    'verse_id': chunk['verse_id'],
                    'chunk_type': 'lecture_content',
                    'source': 'vedabase_lectures'
                }
            })

        # Save to temp NDJSON (newline-delimited JSON)
        temp_file = Path('temp_vectors.ndjson')
        with open(temp_file, 'w') as f:
            for vector in vectors_data:
                f.write(json.dumps(vector) + '\n')

        # Upload using wrangler (same as original vedabase script)
        print("  Uploading to Vectorize...")
        import subprocess

        result = subprocess.run(
            ['npx', 'wrangler', 'vectorize', 'insert', 'philosophy-vectors', '--file=temp_vectors.ndjson'],
            capture_output=True,
            text=True
        )

        temp_file.unlink()  # Clean up

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
    print("\nVedabase RAG is now complete with lectures!")
    print("="*80)

if __name__ == '__main__':
    main()
