#!/bin/bash
# Script to push KoraFlow to GitHub
# Make sure you've created the repository on GitHub first

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Pushing KoraFlow to GitHub"
echo "=========================================="
echo ""

# Check if remote already exists
if git remote get-url origin > /dev/null 2>&1; then
    echo "Remote 'origin' already exists:"
    git remote get-url origin
    echo ""
    read -p "Do you want to use this remote? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please set up the remote manually:"
        echo "  git remote set-url origin <your-repo-url>"
        exit 1
    fi
else
    echo "No remote 'origin' found."
    echo ""
    echo "Please provide your GitHub repository URL."
    echo "Example: https://github.com/yourusername/koraflow.git"
    echo "Or: git@github.com:yourusername/koraflow.git"
    echo ""
    read -p "Enter repository URL: " REPO_URL
    
    if [ -z "$REPO_URL" ]; then
        echo "Error: Repository URL is required"
        exit 1
    fi
    
    git remote add origin "$REPO_URL"
    echo "Remote 'origin' added: $REPO_URL"
fi

echo ""
echo "Pushing to GitHub..."
echo ""

# Push to main branch
git push -u origin main

echo ""
echo "=========================================="
echo "Successfully pushed to GitHub!"
echo "=========================================="
echo ""
echo "Your repository is now available at:"
git remote get-url origin | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//'
echo ""

