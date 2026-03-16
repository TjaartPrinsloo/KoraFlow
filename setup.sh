#!/usr/bin/env bash
# ─── Frappe Agent Setup ───────────────────────────────────────────────────────
set -e

echo ""
echo "┌─────────────────────────────────────────────┐"
echo "│         Frappe Agent — Setup Script          │"
echo "└─────────────────────────────────────────────┘"
echo ""

# ── 1. Install Ollama if missing ─────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
    echo "▶ Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✓ Ollama already installed: $(ollama --version)"
fi

# ── 2. Start Ollama service ──────────────────────────────────────────────────
if ! pgrep -x ollama &>/dev/null; then
    echo "▶ Starting Ollama service..."
    ollama serve &>/tmp/ollama.log &
    sleep 3
fi

# ── 3. Select and pull model ─────────────────────────────────────────────────
# Detect available RAM and pick best model
TOTAL_RAM_GB=$(awk '/MemTotal/ { printf "%.0f", $2/1024/1024 }' /proc/meminfo 2>/dev/null || echo "16")

echo ""
echo "Detected RAM: ~${TOTAL_RAM_GB}GB"

if [ "$TOTAL_RAM_GB" -ge 48 ]; then
    MODEL="qwen2.5-coder:32b"
elif [ "$TOTAL_RAM_GB" -ge 20 ]; then
    MODEL="qwen2.5-coder:14b"
else
    MODEL="qwen2.5-coder:7b"
fi

echo "▶ Pulling model: $MODEL (best fit for your hardware)"
ollama pull "$MODEL"

# Write selected model to config
echo "$MODEL" > .ollama_model
echo "✓ Model saved to .ollama_model"

# ── 4. Install Python dependencies ───────────────────────────────────────────
echo ""
echo "▶ Installing Python dependencies..."
pip install -r requirements.txt --quiet

# ── 5. Make scripts executable ───────────────────────────────────────────────
chmod +x agent.py
chmod +x mcp_server/server.py

# ── 6. Smoke test ────────────────────────────────────────────────────────────
echo ""
echo "▶ Running smoke test..."
python agent.py --model "$MODEL" --no-check \
    "In one sentence, confirm you are ready to help with Frappe development."

echo ""
echo "┌─────────────────────────────────────────────────────────────────┐"
echo "│  ✓ Setup complete!                                               │"
echo "│                                                                  │"
echo "│  Start the agent REPL:  python agent.py                         │"
echo "│  Single prompt:         python agent.py \"your question\"          │"
echo "│  Start MCP server:      python mcp_server/server.py             │"
echo "│                                                                  │"
echo "│  See README.md for Claude Code MCP integration instructions.    │"
echo "└─────────────────────────────────────────────────────────────────┘"
