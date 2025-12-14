#!/bin/bash
# Test full flow: query + synthesis

echo "=== STEP 1: Query Worker ==="
QUERY_RESULT=$(curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query":"spiritual habits","topK":3,"source":"all"}')

echo "Query returned $(echo "$QUERY_RESULT" | jq '.count') results"
echo ""

# Extract first result for testing
FIRST_RESULT=$(echo "$QUERY_RESULT" | jq '.results[0]')
echo "First result book: $(echo "$FIRST_RESULT" | jq -r '.vedabaseVerse.book_name')"
echo ""

echo "=== STEP 2: Synthesis Worker (first 500 chars) ==="
# Build sources array
SOURCES=$(echo "$QUERY_RESULT" | jq -c '[.results[0:2] | .[] | {
  verse: .vedabaseVerse,
  chunkType: .sectionType,
  chunkText: .chunkText,
  score: .score
}]')

curl -s -X POST https://philosophy-rag-synthesis.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"spiritual habits\",
    \"wordLimit\": 100,
    \"sources\": $SOURCES
  }" | head -c 500

echo ""
echo ""
echo "=== Done ==="
