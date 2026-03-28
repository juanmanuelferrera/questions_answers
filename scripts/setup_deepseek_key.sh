#!/bin/bash
# Setup DeepSeek API Key for Synthesis Worker

echo "🚀 DeepSeek API Key Setup"
echo "========================="
echo ""
echo "If you don't have a DeepSeek API key yet:"
echo "1. Visit: https://platform.deepseek.com"
echo "2. Sign up (free - 5M tokens included!)"
echo "3. Go to API Keys → Create API Key"
echo "4. Copy your key (starts with sk-)"
echo ""
echo "Ready to add your DeepSeek API key..."
echo ""

# Set the secret
npx wrangler secret put DEEPSEEK_API_KEY --name vedabase-synthesis

echo ""
echo "✅ DeepSeek API key configured!"
echo ""
echo "💰 Cost Savings:"
echo "   DeepSeek:    $0.0013/query (89% savings)"
echo "   vs GPT-4o:   $0.012/query"
echo ""
echo "Next steps:"
echo "1. Deploy: npx wrangler deploy --config wrangler.synthesis.toml"
echo "2. Test your first query!"
echo ""
