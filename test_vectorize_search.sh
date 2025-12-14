#!/bin/bash
# Test Vectorize search for "Janice Johnson"

echo "Testing Vectorize search for 'Janice Johnson'..."
echo ""

# First, get an embedding for "Janice Johnson" query
echo "Step 1: Getting embedding for query..."
EMBEDDING=$(curl -s https://api.openai.com/v1/embeddings \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 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" \
  -d '{
    "input": "Who is Janice Johnson",
    "model": "text-embedding-3-small"
  }' | jq -r '.data[0].embedding | @json')

echo "Embedding obtained (length: $(echo $EMBEDDING | jq 'length'))"
echo ""

# Save to temp file for wrangler
cat > temp_query_vector.json <<EOF
{
  "vector": $EMBEDDING,
  "topK": 10,
  "returnMetadata": true
}
EOF

echo "Step 2: Querying Vectorize index..."
npx wrangler vectorize query philosophy-vectors --file=temp_query_vector.json

rm temp_query_vector.json

echo ""
echo "Done!"
