#!/bin/bash
# Wrapper script to run bench_setup.sh with proper environment

# Load nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# Use Node.js 18 (compatible with Frappe v13)
nvm use 18 || nvm install 18 && nvm use 18

# Add bench to PATH
export PATH="$HOME/Library/Python/3.9/bin:$PATH"

# Run bench setup
cd "$(dirname "$0")"
./bench_setup.sh

