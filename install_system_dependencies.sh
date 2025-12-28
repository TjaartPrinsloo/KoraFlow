#!/bin/bash
# KoraFlow System Dependencies Installation Script
# Installs system dependencies for Drive and Insights apps

set -e

echo "=========================================="
echo "KoraFlow System Dependencies Installation"
echo "=========================================="
echo ""

# Detect Homebrew path
if [ -f /opt/homebrew/bin/brew ]; then
    BREW_PATH="/opt/homebrew/bin/brew"
    BREW_PREFIX="/opt/homebrew"
elif [ -f /usr/local/bin/brew ]; then
    BREW_PATH="/usr/local/bin/brew"
    BREW_PREFIX="/usr/local"
else
    echo "Homebrew is not installed."
    echo ""
    echo "To install Homebrew, run:"
    echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo ""
    echo "After installing Homebrew, run this script again."
    exit 1
fi

echo "Homebrew found at: $BREW_PATH ✓"
echo ""

# Install libmagic for Drive
echo "Installing libmagic for Drive..."
$BREW_PATH install libmagic
echo "libmagic installed ✓"
echo ""

# Install pkg-config and MariaDB for Insights mysqlclient
echo "Installing pkg-config and MariaDB development libraries for Insights..."
$BREW_PATH install pkg-config mariadb
echo "pkg-config and MariaDB installed ✓"
echo ""

# Set environment variables for mysqlclient compilation
export PKG_CONFIG_PATH="$BREW_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH"
# Get MariaDB version to find correct header path
MARIADB_VERSION=$(brew list --versions mariadb | awk '{print $2}')
if [ -n "$MARIADB_VERSION" ]; then
    export MYSQLCLIENT_CFLAGS="-I$BREW_PREFIX/Cellar/mariadb/$MARIADB_VERSION/include/mysql"
else
    # Fallback: try common paths
    export MYSQLCLIENT_CFLAGS="-I$BREW_PREFIX/include/mariadb/mysql -I$BREW_PREFIX/Cellar/mariadb/*/include/mysql"
fi
export MYSQLCLIENT_LDFLAGS="-L$BREW_PREFIX/lib -lmariadb"

# Install python-magic for Drive
echo ""
echo "Installing python-magic for Drive..."
cd bench
./env/bin/pip install python-magic==0.4.27
echo "python-magic installed ✓"
echo ""

# Install mysqlclient Python package
echo "Installing mysqlclient Python package..."
./env/bin/pip install mysqlclient
echo "mysqlclient installed ✓"
echo ""

# Install ibis MySQL backend
echo "Installing ibis MySQL backend..."
./env/bin/pip install "ibis-framework[mysql]"
echo "ibis MySQL backend installed ✓"
echo ""

echo "=========================================="
echo "System dependencies installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Reinstall Drive app:"
echo "     cd bench"
echo "     bench --site koraflow-site install-app drive"
echo ""
echo "  2. Verify Insights MySQL backend:"
echo "     cd bench"
echo "     bench --site koraflow-site console"
echo "     # Then test: import ibis; ibis.mysql"
echo ""

