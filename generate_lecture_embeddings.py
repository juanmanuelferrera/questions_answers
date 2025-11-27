#!/usr/bin/env python3
"""
Generate and upload embeddings for lecture chunks to Vectorize
"""

import json
import os
import requests
from pathlib import Path
from openai import OpenAI

# Load environment variables
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

def upload_to_vectorize(vectors: list, account_id: str, api_token: str, index_name: str = 'vedabase-index'):
    """Upload vectors to Cloudflare Vectorize"""
    url = f'https://api.cloudflare.com/client/v4/accounts/{account_id}/vectorize/v2/indexes/{index_name}/insert'

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json={'vectors': vectors})

    if response.status_code != 200:
        raise Exception(f"Vectorize upload failed: {response.text}")

    return response.json()

def main():
    """Generate and upload lecture embeddings"""

    # Load lecture export
    with open('lectures_export.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data['chunks']
    print(f"Loaded {len(chunks)} chunks to process")

    # Get credentials
    account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
    api_token = os.getenv('CLOUDFLARE_API_TOKEN')

    if not account_id or not api_token:
        raise Exception("Missing CLOUDFLARE_ACCOUNT_ID or CLOUDFLARE_API_TOKEN in .env")

    # Process in batches of 100
    batch_size = 100
    total_uploaded = 0

    # Check for progress file
    progress_file = Path('lecture_embedding_progress.json')
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            start_index = progress.get('last_chunk_index', 0) + 1
            print(f"Resuming from chunk {start_index}")
    else:
        start_index = 0
        progress = {'last_chunk_index': -1}

    for i in range(start_index, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        # Prepare texts for embedding
        texts = [chunk['content'] for chunk in batch]

        print(f"\nBatch {batch_num}/{total_batches}: Processing {len(batch)} chunks ({i+1}-{min(i+batch_size, len(chunks))})...")

        # Generate embeddings
        print("  Generating embeddings...")
        embeddings = generate_embeddings_batch(texts)

        # Prepare vectors for Vectorize
        vectors = []
        for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
            vectors.append({
                'id': str(chunk['id']),
                'values': embedding,
                'metadata': {
                    'chunk_id': chunk['id'],
                    'verse_id': chunk['verse_id'],
                    'chunk_type': chunk['chunk_type'],
                    'source': 'vedabase_lectures'
                }
            })

        # Upload to Vectorize
        print("  Uploading to Vectorize...")
        result = upload_to_vectorize(vectors, account_id, api_token)

        total_uploaded += len(batch)
        print(f"  ✓ Successfully uploaded {len(batch)} vectors")
        print(f"  Progress: {total_uploaded}/{len(chunks)} ({100 * total_uploaded / len(chunks):.1f}%)")

        # Update progress
        progress['last_chunk_index'] = i + len(batch) - 1
        with open(progress_file, 'w') as f:
            json.dump(progress, f)

    # Clean up progress file
    if progress_file.exists():
        progress_file.unlink()

    print(f"\n✅ All embeddings generated and uploaded!")
    print(f"   Total chunks processed: {total_uploaded}")
    print(f"   Vedabase RAG now includes lectures!")

if __name__ == '__main__':
    main()
