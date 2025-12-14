#!/bin/bash
echo "Testing synthesis worker..."

curl -X POST https://vedabase-synthesis.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test",
    "wordLimit": 50,
    "sources": [{
      "verse": {"book_name": "Test Book"},
      "chunkType": "test",
      "chunkText": "Test content about spiritual practices and meditation.",
      "score": 0.9
    }]
  }' 2>&1 | head -c 500

echo ""
echo "Done"
