#!/bin/bash
# Batch upsert script for remaining vectors

set -e  # Exit on error

echo "================================"
echo "Starting Batch Upsert"
echo "================================"
echo ""

# List of files to upload in order
files=(
    "kb_for_upsert_part000.ndjson"
    "sb_cantos_1_3_for_upsert_part000.ndjson"
    "sb_cantos_1_3_for_upsert_part001.ndjson"
    "sb_cantos_4_10_for_upsert_part000.ndjson"
    "sb_cantos_4_10_for_upsert_part001.ndjson"
    "rechunked_for_upsert_part000.ndjson"
    "rechunked_for_upsert_part001.ndjson"
    "rechunked_for_upsert_part002.ndjson"
    "rechunked_for_upsert_part003.ndjson"
    "rechunked_for_upsert_part004.ndjson"
    "rechunked_for_upsert_part005.ndjson"
    "rechunked_for_upsert_part006.ndjson"
)

total_files=${#files[@]}
current=1

for file in "${files[@]}"; do
    echo "[$current/$total_files] Upserting: $file"
    echo "----------------------------------------"

    npx wrangler vectorize upsert philosophy-vectors --file="$file" --batch-size=500

    if [ $? -eq 0 ]; then
        echo "✓ Success: $file"
        echo ""
    else
        echo "✗ Failed: $file"
        echo "Stopping batch upsert"
        exit 1
    fi

    ((current++))

    # Small delay between files
    sleep 2
done

echo "================================"
echo "✓ All files uploaded successfully!"
echo "================================"
echo "Total vectors: ~52,419"
echo "Next step: Wait 15-45 minutes for Vectorize indexing"
