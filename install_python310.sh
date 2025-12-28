#!/bin/bash
# Python 3.10+ Installation Helper for KoraFlow

echo "=========================================="
echo "Python 3.10+ Installation Helper"
echo "=========================================="

# Check current Python version
CURRENT_PYTHON=$(python3 --version 2>&1 | awk '{print $2}')
echo "Current Python version: $CURRENT_PYTHON"

# Check if Python 3.10+ is already available
if python3.10 --version &>/dev/null; then
    echo "✓ Python 3.10+ already available"
    exit 0
fi

if python3.11 --version &>/dev/null; then
    echo "✓ Python 3.11+ already available"
    exit 0
fi

if python3.12 --version &>/dev/null; then
    echo "✓ Python 3.12+ already available"
    exit 0
fi

echo ""
echo "Python 3.10+ is required for Frappe v15 but not found."
echo ""
echo "Installation options:"
echo ""
echo "Option 1: Install via official Python installer (Recommended)"
echo "  1. Download from: https://www.python.org/downloads/"
echo "  2. Install Python 3.10 or later"
echo "  3. Run this script again to verify"
echo ""
echo "Option 2: Install via Homebrew (if available)"
echo "  brew install python@3.10"
echo ""
echo "Option 3: Install via pyenv"
echo "  curl https://pyenv.run | bash"
echo "  pyenv install 3.10.0"
echo "  pyenv global 3.10.0"
echo ""
echo "After installation, ensure 'python3' points to Python 3.10+"
echo ""

