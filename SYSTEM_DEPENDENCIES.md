# System Dependencies Installation Guide

This guide explains how to install system dependencies required for **Drive** and **Insights** apps to function fully.

## Overview

- **Drive** requires `libmagic` system library for file type detection
- **Insights** requires `mysqlclient` Python package, which needs MariaDB development libraries

## Prerequisites

You need **Homebrew** (macOS package manager) installed. If you don't have it:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions. After installation, you may need to add Homebrew to your PATH:

```bash
# For Apple Silicon Macs (M1/M2/M3):
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"

# For Intel Macs:
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/usr/local/bin/brew shellenv)"
```

## Installation

Run the installation script:

```bash
./install_system_dependencies.sh
```

This script will:
1. Check for Homebrew installation
2. Install `libmagic` (for Drive)
3. Install `pkg-config` and `mariadb` (for Insights)
4. Install Python packages: `python-magic`, `mysqlclient`, and `ibis-framework[mysql]`

## Manual Installation

If you prefer to install manually:

### For Drive

```bash
# Install libmagic
brew install libmagic

# Install python-magic (already in requirements)
cd bench
./env/bin/pip install python-magic==0.4.27
```

### For Insights

```bash
# Install system dependencies
brew install pkg-config mariadb

# Set environment variables
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"  # Apple Silicon
# OR
export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"     # Intel

export MYSQLCLIENT_CFLAGS="-I/opt/homebrew/include/mariadb"  # Apple Silicon
# OR
export MYSQLCLIENT_CFLAGS="-I/usr/local/include/mariadb"       # Intel

export MYSQLCLIENT_LDFLAGS="-L/opt/homebrew/lib -lmariadb"  # Apple Silicon
# OR
export MYSQLCLIENT_LDFLAGS="-L/usr/local/lib -lmariadb"      # Intel

# Install Python packages
cd bench
./env/bin/pip install mysqlclient
./env/bin/pip install "ibis-framework[mysql]"
```

## After Installation

### Reinstall Drive App

```bash
cd bench
bench --site koraflow-site install-app drive
```

### Verify Insights MySQL Backend

```bash
cd bench
bench --site koraflow-site console
```

Then in the Python console:
```python
import ibis
ibis.mysql  # Should not raise an error
```

## Troubleshooting

### "libmagic not found" error

Ensure `libmagic` is installed:
```bash
brew list libmagic
```

If not installed:
```bash
brew install libmagic
```

### "mysqlclient build failed" error

1. Ensure MariaDB is installed:
   ```bash
   brew list mariadb
   ```

2. Set environment variables (see Manual Installation above)

3. Try installing mysqlclient again:
   ```bash
   cd bench
   ./env/bin/pip install mysqlclient
   ```

### "pkg-config not found" error

Install pkg-config:
```bash
brew install pkg-config
```

## Current Status

- ✅ `python-magic==0.4.27` is already installed in the bench environment
- ⚠️ `libmagic` system library needs to be installed via Homebrew
- ✅ Insights Python dependencies are installed (ibis, pandas, httpx, etc.)
- ⚠️ `mysqlclient` requires system libraries (MariaDB development headers)

## Notes

- Drive will work partially without `libmagic`, but file type detection will fail
- Insights will work with other database backends (SQLite, DuckDB, PostgreSQL) without `mysqlclient`
- Full functionality requires all system dependencies to be installed

