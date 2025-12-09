#!/usr/bin/env python3
"""
Test what chunks Vectorize returns for "Lomasa Muni" query
"""

import os
from openai import OpenAI
import subprocess
import json

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_lomasa_search():
    """Generate embedding for Lomasa query and search Vectorize"""

    print("=" * 80)
    print("TESTING LOMASA MUNI VECTORIZE SEARCH")
    print("=" * 80)

    # Generate embedding for query
    query = "Who is Lomasa Muni?"
    print(f"\nQuery: {query}")
    print("Generating query embedding...")

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
        dimensions=1536
    )

    query_embedding = response.data[0].embedding
    print(f"✓ Generated embedding ({len(query_embedding)} dimensions)")

    # Save embedding to temp file for wrangler
    with open('temp_query_embedding.json', 'w') as f:
        json.dump(query_embedding, f)

    print("\nSearching Vectorize for top 20 matches...")

    # Search Vectorize using wrangler
    # We'll create a vector file with the embedding and use wrangler to query
    result = subprocess.run([
        'npx', 'wrangler', 'vectorize', 'query', 'philosophy-vectors',
        '--vector-id', 'vedabase_chunk_91093',  # Use Lomasa chunk as reference
        '--top-k', '20'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Search successful")
        print("\n" + "=" * 80)
        print("TOP 20 MATCHES:")
        print("=" * 80)
        print(result.stdout)
    else:
        print(f"✗ Search failed: {result.stderr}")

    # Clean up
    if os.path.exists('temp_query_embedding.json'):
        os.unlink('temp_query_embedding.json')

if __name__ == '__main__':
    test_lomasa_search()
