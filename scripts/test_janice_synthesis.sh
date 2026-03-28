#!/bin/bash

# Step 1: Get search results from query worker
echo "=== STEP 1: Getting search results from query worker ==="
SEARCH_RESULTS=$(curl -s -X POST "https://philosophy-rag.joanmanelferrera-400.workers.dev" \
  -H "Content-Type: application/json" \
  -d '{"query":"Janice Johnson","topK":5,"source":"vedabase","bookFilter":"conversations"}')

echo "$SEARCH_RESULTS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f\"Found {data['count']} results\")
for i, r in enumerate(data['results'][:3], 1):
    print(f\"  [{i}] Score: {r['score']:.3f} - {r['sectionType']}\")
    print(f\"      Book: {r['vedabaseVerse']['book_name']}\")
    print(f\"      Preview: {r['chunkText'][:80]}...\")
"

# Step 2: Format sources for synthesis
echo ""
echo "=== STEP 2: Preparing synthesis request ==="
SYNTHESIS_REQUEST=$(echo "$SEARCH_RESULTS" | python3 -c "
import json, sys
data = json.load(sys.stdin)

sources = []
for r in data['results'][:5]:
    sources.append({
        'verse': r['vedabaseVerse'],
        'chunkType': r['sectionType'],
        'chunkText': r['chunkText'],
        'score': r['score']
    })

synthesis_req = {
    'query': 'Who is Janice Johnson?',
    'sources': sources,
    'wordLimit': 200,
    'bookContext': 'Conversations'
}

print(json.dumps(synthesis_req, indent=2))
" > /tmp/synthesis_request.json)

echo "Synthesis request prepared with $(cat /tmp/synthesis_request.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)['sources']))" ) sources"

# Step 3: Send to synthesis worker
echo ""
echo "=== STEP 3: Calling synthesis worker ==="
echo "Streaming response:"
echo "---"

curl -s -X POST "https://vedabase-synthesis.joanmanelferrera-400.workers.dev" \
  -H "Content-Type: application/json" \
  -d @/tmp/synthesis_request.json | head -100

echo ""
echo "---"
echo "Test complete!"
