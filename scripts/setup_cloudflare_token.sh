#!/bin/bash
# Setup Cloudflare API Token for Wrangler

echo "=========================================="
echo "Cloudflare API Token Setup"
echo "=========================================="
echo ""
echo "You need to create a Cloudflare API token to upload vectors."
echo ""
echo "Steps:"
echo "1. Go to: https://dash.cloudflare.com/profile/api-tokens"
echo "2. Click 'Create Token'"
echo "3. Use template: 'Edit Cloudflare Workers' OR create custom with:"
echo "   - Account: Vectorize: Write"
echo "   - Account: Workers Scripts: Edit"
echo "4. Copy the token when shown (you won't see it again!)"
echo "5. Paste it below:"
echo ""
read -sp "Enter your Cloudflare API Token: " token
echo ""

if [ -z "$token" ]; then
    echo "ERROR: No token provided"
    exit 1
fi

# Export for current session
export CLOUDFLARE_API_TOKEN="$token"

# Add to shell config for persistence
SHELL_CONFIG=""
if [ -f ~/.zshrc ]; then
    SHELL_CONFIG=~/.zshrc
elif [ -f ~/.bashrc ]; then
    SHELL_CONFIG=~/.bashrc
else
    SHELL_CONFIG=~/.bash_profile
fi

echo "" >> "$SHELL_CONFIG"
echo "# Cloudflare API Token (added $(date))" >> "$SHELL_CONFIG"
echo "export CLOUDFLARE_API_TOKEN='$token'" >> "$SHELL_CONFIG"

echo ""
echo "✓ Token saved to $SHELL_CONFIG"
echo "✓ Token exported for current session"
echo ""
echo "Now you can run:"
echo "  ./batch_upsert.sh"
echo ""
echo "Or manually:"
echo "  npx wrangler vectorize upsert philosophy-vectors --file=kb_for_upsert_part000.ndjson --batch-size=500"
echo ""
