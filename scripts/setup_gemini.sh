#!/bin/bash
#
# Setup script for Gemini 2.0 Flash API
#
# This script helps you configure the GEMINI_API_KEY for the synthesis worker
#

echo "========================================================================"
echo "GEMINI 2.0 FLASH SETUP"
echo "========================================================================"
echo ""
echo "Gemini 2.0 Flash offers:"
echo "  - 1 Million token context window (handles ALL RAG sources)"
echo "  - Excellent IAST character preservation"
echo "  - Free tier: 15 RPM, 1M TPM, 1500 RPD"
echo "  - Cost: $0.075/1M input, $0.30/1M output (40x cheaper than Claude)"
echo ""
echo "========================================================================"
echo ""

# Step 1: Get API Key
echo "Step 1: Get your Gemini API Key"
echo "----------------------------------------"
echo "1. Go to: https://aistudio.google.com/apikey"
echo "2. Click 'Get API key' or 'Create API key'"
echo "3. Copy the API key"
echo ""
read -p "Paste your Gemini API key here: " GEMINI_KEY

if [ -z "$GEMINI_KEY" ]; then
  echo "Error: No API key provided"
  exit 1
fi

# Step 2: Set the secret in Cloudflare
echo ""
echo "Step 2: Setting GEMINI_API_KEY in Cloudflare Workers"
echo "----------------------------------------"
echo "$GEMINI_KEY" | npx wrangler secret put GEMINI_API_KEY --name vedabase-synthesis

if [ $? -eq 0 ]; then
  echo ""
  echo "========================================================================"
  echo "✓ GEMINI API KEY CONFIGURED SUCCESSFULLY"
  echo "========================================================================"
  echo ""
  echo "Next steps:"
  echo "1. Deploy the synthesis worker: npx wrangler deploy --config wrangler.synthesis.toml"
  echo "2. Test with a query on your web app"
  echo ""
  echo "The synthesis worker will now use Gemini 2.0 Flash with 1M token context!"
  echo "========================================================================"
else
  echo ""
  echo "Error: Failed to set API key in Cloudflare"
  exit 1
fi
