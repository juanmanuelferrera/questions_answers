#!/usr/bin/env python3
"""
Convert conversation embeddings to NDJSON format with proper metadata for wrangler upload
"""

import json

# Load embeddings
with open('conversation_embeddings.json', 'r') as f:
    embeddings = json.load(f)

# Convert to NDJSON with proper metadata
with open('conversation_embeddings.ndjson', 'w') as f:
    for item in embeddings:
        ndjson_item = {
            "id": str(item['id']),
            "values": item['embedding'],
            "metadata": {
                "source": "vedabase",
                "book_code": "conversations",
                "chunk_id": item['id'],
                "chunk_type": item['chunk_type'],
                "verse_id": item['verse_id']
            }
        }
        f.write(json.dumps(ndjson_item) + '\n')

print(f"✅ Converted {len(embeddings)} embeddings to NDJSON with proper metadata")
print("   Metadata fields: source, book_code, chunk_id, chunk_type, verse_id")
