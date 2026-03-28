#!/bin/bash
echo "Final system test..."
echo ""

# Get real data from query worker
QUERY_DATA=$(curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query":"spiritual habits","topK":2,"source":"all"}')

echo "Query results: $(echo "$QUERY_DATA" | jq '.count') results"

# Build sources
SOURCES=$(echo "$QUERY_DATA" | jq -c '[.results[0:1] | .[] | {
  verse: .vedabaseVerse,
  chunkType: .sectionType,
  chunkText: .chunkText,
  score: .score
}]')

echo "Testing synthesis (10 second timeout)..."
curl -m 10 -X POST https://vedabase-synthesis.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"spiritual habits\",\"wordLimit\":100,\"sources\":$SOURCES}" \
  2>&1 | head -c 800

echo ""
echo ""
echo "Complete!"
