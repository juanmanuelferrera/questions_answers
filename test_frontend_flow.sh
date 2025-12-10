#!/bin/bash

echo "=== Simulating Frontend Search for 'Janice Johnson' ==="
echo ""
echo "Step 1: Frontend sends search with topK=100 (5x multiplier for book filter)"
echo "        Query: Janice Johnson"
echo "        TopK: 100 (20 * 5 for book filter)"
echo "        BookFilter: conversations"
echo ""

RESPONSE=$(curl -s -X POST 'https://philosophy-rag.joanmanelferrera-400.workers.dev' \
  -H 'Content-Type: application/json' \
  -d '{"query":"Janice Johnson","topK":100,"source":"vedabase","bookFilter":"conversations"}')

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Results returned: {data[\"count\"]}')
print()
if data['count'] == 0:
    print('❌ PROBLEM: Query worker returned 0 results!')
    print('   Frontend would show: No results found')
else:
    print(f'✅ Query worker returned {data[\"count\"]} results')
    print()
    print('Top 3 results:')
    for i, r in enumerate(data['results'][:3], 1):
        print(f'  [{i}] Score: {r[\"score\"]:.3f}')
        print(f'      Type: {r[\"sectionType\"]}')
        print(f'      Preview: {r[\"chunkText\"][:60]}...')
        print()
"
