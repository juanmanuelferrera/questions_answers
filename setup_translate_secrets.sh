#!/bin/bash
# Setup secrets for translate worker

echo "Setting up OPENAI_API_KEY for translate worker..."
echo "You can use the same API key as your synthesis worker"
echo ""

npx wrangler secret put OPENAI_API_KEY --config wrangler.translate.toml

echo ""
echo "✅ Secret setup complete!"
echo "The translate worker should now work properly."
