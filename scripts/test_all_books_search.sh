#!/bin/bash
# Test "All books" search for spiritual habits query

echo "Testing: 'what are the most important habits to succeed in spiritual life'"
echo "Filter: All books (no book filter)"
echo ""

curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what are the most important habits to succeed in spiritual life",
    "topK": 10,
    "source": "all"
  }' | jq '.'

echo ""
echo "Done!"
