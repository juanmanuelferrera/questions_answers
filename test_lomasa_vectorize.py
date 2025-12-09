#!/usr/bin/env python3
"""
Test if Lomasa Muni chunk ranks in top results from Vectorize
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

load_dotenv()

# Create embedding for the query
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

query = "Who is Lomasa Muni?"
print(f"Testing query: {query}\n")

# Generate query embedding
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=[query],
    dimensions=1536
)

query_vector = response.data[0].embedding

# Create temp file with query vector - test with larger topK
with open('temp_query_lomasa.json', 'w') as f:
    json.dump({
        'vector': query_vector,
        'topK': 100,  # Test with 100 results
        'returnValues': False,
        'returnMetadata': 'all'
    }, f)

# Query Vectorize
print("Searching Vectorize for top 100 results...")
result = subprocess.run([
    'npx', 'wrangler', 'vectorize', 'query', 'philosophy-vectors',
    '--file', 'temp_query_lomasa.json'
], capture_output=True, text=True)

# Check if Lomasa chunk appears in results
lomasa_found = False
lomasa_position = None

lines = result.stdout.split('\n')
for i, line in enumerate(lines):
    if 'chunk_id' in line and '2985' in line:
        lomasa_found = True
        lomasa_position = i
        print(f"\n✓ SUCCESS: Chunk 2985 (Lomasa Muni) found in results!")
        print(f"Position in output: Line {i}")
        # Print surrounding context
        print("\nContext:")
        for j in range(max(0, i-2), min(len(lines), i+3)):
            print(lines[j])
        break

if not lomasa_found:
    print(f"\n✗ WARNING: Chunk 2985 (Lomasa Muni) NOT in top 100 results")
    print("\nThis confirms the chunk is being outranked by other content.")
    print("\nPossible solutions:")
    print("  1. Re-chunk large purports (split the 1,750-char chunk)")
    print("  2. Add hybrid search (semantic + keyword)")
    print("  3. Wait longer for Vectorize indexing")
    print("\nTop 10 results metadata:")
    # Try to show what's ranking higher
    in_results = False
    result_count = 0
    for line in lines:
        if 'matches' in line.lower() or 'results' in line.lower():
            in_results = True
        if in_results and 'chunk_id' in line:
            print(f"  {line.strip()}")
            result_count += 1
            if result_count >= 10:
                break

# Clean up
os.remove('temp_query_lomasa.json')

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
