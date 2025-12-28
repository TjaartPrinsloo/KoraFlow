#!/bin/bash
# Node.js Installation Helper for KoraFlow

echo "=========================================="
echo "Node.js Installation Helper"
echo "=========================================="

# Load nvm if it exists
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    echo "Loading nvm..."
    \. "$NVM_DIR/nvm.sh"
    
    # Install Node.js LTS
    echo "Installing Node.js LTS..."
    nvm install --lts
    nvm use --lts
    nvm alias default node
    
    # Verify installation
    if command -v node &> /dev/null; then
        echo "✓ Node.js installed: $(node --version)"
        echo "✓ npm installed: $(npm --version)"
        
        # Install Yarn
        echo ""
        echo "Installing Yarn..."
        npm install -g yarn
        if command -v yarn &> /dev/null; then
            echo "✓ Yarn installed: $(yarn --version)"
        else
            echo "✗ Yarn installation failed"
            exit 1
        fi
    else
        echo "✗ Node.js installation failed"
        exit 1
    fi
else
    echo "nvm not found. Please install nvm first:"
    echo "  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo ""
echo "=========================================="
echo "Node.js setup complete!"
echo "=========================================="
echo ""
echo "To use Node.js in your current shell, run:"
echo "  export NVM_DIR=\"\$HOME/.nvm\""
echo "  [ -s \"\$NVM_DIR/nvm.sh\" ] && \. \"\$NVM_DIR/nvm.sh\""
echo "  nvm use --lts"
echo ""

