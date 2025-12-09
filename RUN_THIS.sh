#!/bin/bash
# FINAL STEP: Upload remaining 52K vectors for complete book filtering
# Run this script from your terminal

cd "$(dirname "$0")"

echo "=================================================="
echo "VEDABASE RAG - Final Vector Upload"
echo "=================================================="
echo ""
echo "This will upload 52,419 vectors across 12 files"
echo "Estimated time: 15-25 minutes"
echo ""
echo "Press ENTER to start, or Ctrl+C to cancel"
read

./batch_upsert.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ SUCCESS! All vectors uploaded"
    echo "=================================================="
    echo ""
    echo "Next steps:"
    echo "1. Wait 15-45 minutes for Vectorize indexing"
    echo "2. Test book filters (BG, SB1-10, KB)"
    echo "3. Verify with: npx wrangler vectorize info philosophy-vectors"
    echo ""
    echo "Expected final count: ~175,261 vectors"
    echo "=================================================="
else
    echo ""
    echo "=================================================="
    echo "❌ Upload failed - check errors above"
    echo "=================================================="
    echo ""
    echo "Troubleshooting:"
    echo "- If authentication error: run 'npx wrangler login'"
    echo "- Then run this script again"
    echo "=================================================="
fi
