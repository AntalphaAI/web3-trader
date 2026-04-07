#!/bin/bash
# Web3 Trader Skill Installer
# Usage: curl -fsSL install.sh | bash

set -e

SKILL_NAME="web3-trader"
SKILL_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"
CONFIG_DIR="$HOME/.web3-trader"

echo "🦐 Installing Web3 Trader Skill..."
echo

# Check if OpenClaw workspace exists
if [ ! -d "$HOME/.openclaw/workspace" ]; then
    echo "❌ OpenClaw workspace not found at $HOME/.openclaw/workspace"
    echo "   Please install OpenClaw first: https://docs.openclaw.ai"
    exit 1
fi

# Create config directory
echo "📁 Creating config directory..."
mkdir -p "$CONFIG_DIR"

# Copy example config if not exists
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo "📝 Creating config file..."
    cp "$SKILL_DIR/references/config.example.yaml" "$CONFIG_DIR/config.yaml"
    echo "   ✏️  Edit $CONFIG_DIR/config.yaml with your 0x API key"
else
    echo "✅ Config already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd "$SKILL_DIR"
pip3 install -r requirements.txt --quiet

# Set permissions
chmod 600 "$CONFIG_DIR/config.yaml" 2>/dev/null || true

echo
echo "✅ Installation complete!"
echo
echo "📋 Next steps:"
echo "   1. Get 0x API key: https://0x.org/dashboard"
echo "   2. Edit config: nano $CONFIG_DIR/config.yaml"
echo "   3. Test it: python3 $SKILL_DIR/scripts/trader_cli.py tokens"
echo "   4. Query price: python3 $SKILL_DIR/scripts/trader_cli.py price --from USDT --to ETH --amount 1000"
echo
