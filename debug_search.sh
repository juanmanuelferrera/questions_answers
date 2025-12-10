#!/bin/bash

echo "Testing different search scenarios for Janice Johnson..."
echo ""

echo "1. Without book filter (like 'All Books'):"
curl -s -X POST 'https://philosophy-rag.joanmanelferrera-400.workers.dev' \
  -H 'Content-Type: application/json' \
  -d '{"query":"Janice Johnson","topK":20,"source":"vedabase"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'   Results: {data[\"count\"]}')
"

echo ""
echo "2. With conversations filter:"
curl -s -X POST 'https://philosophy-rag.joanmanelferrera-400.workers.dev' \
  -H 'Content-Type: application/json' \
  -d '{"query":"Janice Johnson","topK":20,"source":"vedabase","bookFilter":"conversations"}' | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'   Results: {data[\"count\"]}')
if data['count'] > 0:
    print(f'   First result book: {data[\"results\"][0][\"vedabaseVerse\"][\"book_code\"]}')
"

echo ""
echo "3. Check if Conversations book exists in /vedabase-books:"
curl -s 'https://philosophy-rag.joanmanelferrera-400.workers.dev/vedabase-books' | python3 -c "
import json, sys
data = json.load(sys.stdin)
conv_books = [b for b in data['books'] if 'conv' in b['code'].lower() or 'conv' in b['name'].lower()]
print(f'   Conversation books found: {len(conv_books)}')
for b in conv_books:
    print(f'      - {b[\"code\"]}: {b[\"name\"]}')
"
