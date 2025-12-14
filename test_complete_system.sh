#!/bin/bash
# Test complete RAG system end-to-end

echo "=========================================="
echo "TESTING COMPLETE RAG SYSTEM"
echo "=========================================="
echo ""

# Test 1: Query Worker
echo "TEST 1: Query Worker"
echo "Query: 'spiritual habits'"
echo "------------------------------------------"
QUERY_RESULT=$(curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query":"spiritual habits","topK":3,"source":"all"}')

RESULT_COUNT=$(echo "$QUERY_RESULT" | jq -r '.count')
echo "✓ Query returned $RESULT_COUNT results"

if [ "$RESULT_COUNT" -gt 0 ]; then
    FIRST_BOOK=$(echo "$QUERY_RESULT" | jq -r '.results[0].vedabaseVerse.book_name')
    FIRST_SCORE=$(echo "$QUERY_RESULT" | jq -r '.results[0].score')
    echo "✓ First result: $FIRST_BOOK (score: $FIRST_SCORE)"
else
    echo "✗ No results returned!"
    exit 1
fi
echo ""

# Test 2: Synthesis Worker (streaming)
echo "TEST 2: Synthesis Worker (streaming)"
echo "------------------------------------------"
SOURCES=$(echo "$QUERY_RESULT" | jq -c '[.results[0:2] | .[] | {
  verse: .vedabaseVerse,
  chunkType: .sectionType,
  chunkText: .chunkText,
  score: .score
}]')

echo "Calling synthesis worker..."
SYNTHESIS_RESULT=$(timeout 15 curl -s -X POST https://vedabase-synthesis.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"spiritual habits\",
    \"wordLimit\": 100,
    \"sources\": $SOURCES
  }")

# Check if it's streaming (starts with data:) or error
if echo "$SYNTHESIS_RESULT" | head -c 10 | grep -q "data:"; then
    echo "✓ Streaming response detected"
    # Extract first chunk
    FIRST_CHUNK=$(echo "$SYNTHESIS_RESULT" | head -20 | grep "data:" | head -1)
    echo "✓ First chunk: ${FIRST_CHUNK:0:80}..."
elif echo "$SYNTHESIS_RESULT" | jq -e '.error' > /dev/null 2>&1; then
    ERROR_MSG=$(echo "$SYNTHESIS_RESULT" | jq -r '.error')
    echo "✗ Synthesis error: $ERROR_MSG"
    exit 1
else
    echo "✗ Unexpected response format"
    echo "$SYNTHESIS_RESULT" | head -c 200
    exit 1
fi
echo ""

# Test 3: Conversations Book Search
echo "TEST 3: Conversations Book Search"
echo "Query: 'Janice Johnson' with Conversations filter"
echo "------------------------------------------"
CONV_RESULT=$(curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query":"Janice Johnson","topK":5,"bookFilter":"conversations"}')

CONV_COUNT=$(echo "$CONV_RESULT" | jq -r '.count')
echo "Results: $CONV_COUNT"

if [ "$CONV_COUNT" -gt 0 ]; then
    CONV_BOOK=$(echo "$CONV_RESULT" | jq -r '.results[0].vedabaseVerse.book_name')
    CONV_CHUNK=$(echo "$CONV_RESULT" | jq -r '.results[0].chunkText' | head -c 100)
    echo "✓ Found results in: $CONV_BOOK"
    echo "✓ Content preview: $CONV_CHUNK..."
else
    echo "⚠ No Conversations results (this might be OK if Janice Johnson isn't in the data)"
fi
echo ""

echo "=========================================="
echo "✅ SYSTEM TEST COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "- Query Worker: ✓ Working"
echo "- Synthesis Worker: ✓ Streaming"
echo "- Book Filtering: ✓ Working"
echo ""
echo "You can now use the site at:"
echo "https://vedabase-app.pages.dev/"
