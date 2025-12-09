#!/usr/bin/env python3
"""
Debug why Lomasa chunk isn't appearing in query results
"""

import os
from openai import OpenAI
import json

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def test_lomasa_embedding():
    """Test if "Lomasa Muni" query embedding is similar to chunk 91093 embedding"""

    print("=" * 80)
    print("DEBUGGING LOMASA MUNI QUERY")
    print("=" * 80)

    # 1. Generate query embedding
    queries = [
        "Who is Lomasa Muni?",
        "What are Lomasa Muni activities?",
        "Lomasa Muni",
        "Tell me about Lomasa"
    ]

    print("\nGenerating embeddings for different query variations...\n")

    for query in queries:
        print(f"Query: '{query}'")

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=query,
            dimensions=1536
        )

        query_embedding = response.data[0].embedding

        # Load the Lomasa chunk embedding to compare
        print("  Loading chunk 91093 embedding from rechunked_embeddings.json...")

        with open('rechunked_embeddings.json', 'r') as f:
            embeddings = json.load(f)

        # Find chunk 91093
        lomasa_chunk = None
        for emb in embeddings:
            if emb['id'] == 'vedabase_chunk_91093':
                lomasa_chunk = emb
                break

        if lomasa_chunk:
            # Calculate cosine similarity
            import numpy as np

            query_vec = np.array(query_embedding)
            chunk_vec = np.array(lomasa_chunk['values'])

            similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))

            print(f"  Similarity to chunk 91093: {similarity:.4f}")

            # Check metadata
            print(f"  Chunk metadata: {lomasa_chunk.get('metadata', {})}")
        else:
            print("  ERROR: Chunk 91093 not found in embeddings file!")

        print()

if __name__ == '__main__':
    test_lomasa_embedding()
