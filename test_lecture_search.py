#!/usr/bin/env python3
import requests
import json

# Test if lectures are searchable
response = requests.post(
    'https://philosophy-rag.joanmanelferrera-400.workers.dev',
    json={
        'query': 'general lecture location date',
        'topK': 3,
        'source': 'vedabase'
    }
)

data = response.json()

print(f"Query: {data['query']}")
print(f"Results found: {data['count']}\n")

for i, result in enumerate(data['results'][:3], 1):
    print(f"=== Result {i} ===")
    print(f"Score: {result['score']:.4f}")
    print(f"Source: {result['source']}")
    print(f"Type: {result['sectionType']}")

    if 'vedabaseVerse' in result:
        v = result['vedabaseVerse']
        print(f"Book: {v['book_code']} - {v['book_name']}")
        print(f"Chapter/Verse: {v['chapter']} {v['verse_number']}")

    text = result['chunkText'][:150]
    print(f"Text: {text}...")
    print()
