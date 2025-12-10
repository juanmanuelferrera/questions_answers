#!/usr/bin/env python3
"""
Check if conversation embeddings exist in Vectorize
"""
import subprocess
import json

# Query Vectorize for conversations using wrangler
print("Checking if conversations exist in Vectorize...")
print()

# Try to query for a conversation vector by metadata
result = subprocess.run(
    ['npx', 'wrangler', 'vectorize', 'get-by-ids', 'lomasa-vectorize', '--ids', '187344'],
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode == 0 and result.stdout:
    print("✅ Found conversation vector in Vectorize!")
    print(result.stdout)
else:
    print("❌ No conversation vectors found in Vectorize")
    print(f"Error: {result.stderr if result.stderr else 'Vector not found'}")
