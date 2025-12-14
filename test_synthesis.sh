#!/bin/bash
# Test synthesis for spiritual habits query

echo "Testing synthesis for: 'what are the most important habits to succeed in spiritual life'"
echo ""

# First get the search results
SEARCH_RESULTS=$(curl -s -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "what are the most important habits to succeed in spiritual life",
    "topK": 5,
    "source": "all"
  }')

echo "Search returned $(echo "$SEARCH_RESULTS" | jq '.count') results"
echo ""

# Now test synthesis
echo "Testing synthesis..."
echo ""

curl -s -X POST https://philosophy-rag-synthesis.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d @- <<EOF | cat
{
  "query": "what are the most important habits to succeed in spiritual life",
  "wordLimit": 150,
  "sources": $(echo "$SEARCH_RESULTS" | jq -c '[.results[] | {
    chunkText: .chunkText,
    score: .score,
    sectionType: .sectionType,
    verse: {
      book: .vedabaseVerse.book_code,
      book_name: .vedabaseVerse.book_name,
      chapter: .vedabaseVerse.chapter,
      verse_number: .vedabaseVerse.verse_number
    }
  }]')
}
EOF

echo ""
echo ""
echo "Done!"
