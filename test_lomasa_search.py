#!/usr/bin/env python3
"""
Test if Lomasa Muni chunk is searchable in Vectorize
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

# Create temp file with query vector
with open('temp_query.json', 'w') as f:
    json.dump({
        'vector': query_vector,
        'topK': 20,
        'returnValues': False,
        'returnMetadata': 'all'
    }, f)

# Query Vectorize
print("Searching Vectorize...")
result = subprocess.run([
    'npx', 'wrangler', 'vectorize', 'query', 'philosophy-vectors',
    '--file', 'temp_query.json'
], capture_output=True, text=True)

print(result.stdout)

if 'Lomasa' in result.stdout:
    print("\n✓ SUCCESS: Lomasa Muni found in search results!")
else:
    print("\n✗ WARNING: Lomasa Muni NOT in top 20 results")
    print("This could mean:")
    print("  1. Vectorize indexing is still in progress (wait a few minutes)")
    print("  2. The semantic match isn't strong enough (chunk is very long)")
    print("  3. Other chunks are ranking higher")

# Clean up
os.remove('temp_query.json')
