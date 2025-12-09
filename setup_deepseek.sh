#!/bin/bash

# 🚀 DeepSeek Setup Script - Automated Setup
# This script helps you configure DeepSeek integration securely

set -e  # Exit on error

echo "🔐 DeepSeek Secure Setup"
echo "======================="
echo ""

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Error: wrangler CLI not found"
    echo "   Install with: npm install -g wrangler"
    exit 1
fi

echo "✅ Wrangler CLI found"
echo ""

# Step 1: Get DeepSeek API Key
echo "📋 STEP 1: Get your DeepSeek API Key"
echo "--------------------------------------"
echo ""
echo "1. Go to: https://platform.deepseek.com"
echo "2. Sign up (GitHub/Google/Email)"
echo "3. Navigate to: Profile → API Keys"
echo "4. Create new API key"
echo "5. Copy the key"
echo ""
echo "🎁 You'll get 5,000,000 free tokens (~1,450 queries)!"
echo ""

read -p "Press Enter when you have your DeepSeek API key ready..."
echo ""

# Step 2: Set DeepSeek Secret
echo "🔒 STEP 2: Configure DeepSeek API Key (Secure)"
echo "-----------------------------------------------"
echo ""
echo "Enter your DeepSeek API key:"
echo "(It will be stored securely in Cloudflare, encrypted)"
echo ""

npx wrangler secret put DEEPSEEK_API_KEY --config wrangler.synthesis.toml

echo ""
echo "✅ DeepSeek API key configured!"
echo ""

# Step 3: Set OpenAI Secret (Fallback)
echo "🔒 STEP 3: Configure OpenAI API Key (Fallback)"
echo "-----------------------------------------------"
echo ""
echo "Enter your OpenAI API key for fallback:"
echo "(Used if DeepSeek fails - ensures 100% uptime)"
echo ""

npx wrangler secret put OPENAI_API_KEY --config wrangler.synthesis.toml

echo ""
echo "✅ OpenAI API key configured!"
echo ""

# Step 4: Deploy
echo "🚀 STEP 4: Deploy Synthesis Worker"
echo "-----------------------------------"
echo ""

npx wrangler deploy --config wrangler.synthesis.toml

echo ""
echo "✅ Worker deployed successfully!"
echo ""

# Step 5: Get worker URL
echo "📍 STEP 5: Get Worker URL"
echo "-------------------------"
echo ""

WORKER_URL=$(npx wrangler deployments list --name vedabase-synthesis 2>/dev/null | grep "https://" | head -1 | awk '{print $2}')

if [ -z "$WORKER_URL" ]; then
    echo "⚠️  Could not automatically detect worker URL"
    echo "   Check Cloudflare dashboard for the URL"
else
    echo "✅ Your synthesis worker is live at:"
    echo "   $WORKER_URL"
fi

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Test the integration (see DEEPSEEK_SECURE_SETUP.md)"
echo "2. Compare 10-20 queries vs GPT-4o"
echo "3. Monitor your DeepSeek balance at: https://platform.deepseek.com/usage"
echo "4. Enjoy 89% cost savings! 💰"
echo ""
echo "💰 Cost Comparison:"
echo "   GPT-4o:       $0.012/query = $360/month (1k queries/day)"
echo "   DeepSeek:     $0.0013/query = $39/month (1k queries/day)"
echo "   Savings:      89% = $321/month saved!"
echo ""
echo "📚 Documentation:"
echo "   - Full guide: DEEPSEEK_SECURE_SETUP.md"
echo "   - Quick ref:  DEEPSEEK_SETUP.md"
echo ""
echo "🧪 Test command:"
echo "   curl -X POST $WORKER_URL \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d @test_deepseek.json"
echo ""
