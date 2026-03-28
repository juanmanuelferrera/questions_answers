#!/usr/bin/env python3
"""
Test Lomasa Muni query against live production system
This tests if the Vectorize embeddings are working even while D1 upload is incomplete
"""

import requests
import json

# Production URL
PROD_URL = "https://philosophy-rag.pages.dev"

def test_lomasa_query():
    """Test 'Who is Lomasa Muni?' query"""

    print("=" * 80)
    print("TESTING LOMASA MUNI QUERY - LIVE PRODUCTION")
    print("=" * 80)

    query = "Who is Lomasa Muni?"
    print(f"\nQuery: {query}")
    print(f"Testing against: {PROD_URL}\n")

    # Send query to production
    response = requests.post(
        f"{PROD_URL}/api/query",
        json={"question": query},
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        print("✓ Query successful!\n")
        print("=" * 80)
        print("RESPONSE:")
        print("=" * 80)
        print(result.get('answer', 'No answer returned'))
        print("\n" + "=" * 80)
        print("CHUNKS RETRIEVED:")
        print("=" * 80)

        chunks = result.get('chunks', [])
        print(f"Total chunks: {len(chunks)}\n")

        for i, chunk in enumerate(chunks[:5], 1):  # Show first 5 chunks
            print(f"\nChunk {i}:")
            print(f"  ID: {chunk.get('id')}")
            print(f"  Score: {chunk.get('score', 'N/A')}")
            print(f"  Content: {chunk.get('content', '')[:200]}...")

        # Check if Lomasa-specific chunk found
        lomasa_found = any('Lomasa' in chunk.get('content', '') for chunk in chunks)
        print("\n" + "=" * 80)
        if lomasa_found:
            print("✓ SUCCESS: Lomasa-specific chunks found in results!")
        else:
            print("⚠️  WARNING: No Lomasa-specific chunks in top results")
        print("=" * 80)
    else:
        print(f"✗ Query failed with status {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == '__main__':
    test_lomasa_query()
