#!/bin/bash
# Interactive installation guide for system dependencies

echo "=========================================="
echo "KoraFlow System Dependencies Installation"
echo "=========================================="
echo ""
echo "Homebrew installation requires interactive access."
echo ""
echo "Please run the following commands in your terminal:"
echo ""
echo "1. Install Homebrew:"
echo '   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
echo ""
echo "2. Add Homebrew to PATH (if needed):"
echo "   # For Apple Silicon Macs:"
echo '   echo '\''eval "$(/opt/homebrew/bin/brew shellenv)"'\'' >> ~/.zshrc'
echo '   eval "$(/opt/homebrew/bin/brew shellenv)"'
echo ""
echo "   # For Intel Macs:"
echo '   echo '\''eval "$(/usr/local/bin/brew shellenv)"'\'' >> ~/.zshrc'
echo '   eval "$(/usr/local/bin/brew shellenv)"'
echo ""
echo "3. Run the installation script:"
echo "   ./install_system_dependencies.sh"
echo ""
echo "4. Reinstall Drive:"
echo "   cd bench"
echo "   bench --site koraflow-site install-app drive"
echo ""
