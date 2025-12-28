# Bench Setup Requirements

## Current Status

The Bench setup script requires:
- ✅ Bench CLI: Installed successfully
- ❌ Python 3.10+: Currently have Python 3.9.6
- ❌ Redis: Not installed

## Issue

Frappe Framework version-14 requires Python 3.10 or higher. The current system has Python 3.9.6.

## Solutions

### Option 1: Install Python 3.10+ (Recommended)

**Using Homebrew (if available):**
```bash
brew install python@3.10
# or
brew install python@3.11
```

**Using pyenv:**
```bash
# Install pyenv if not already installed
curl https://pyenv.run | bash

# Install Python 3.10
pyenv install 3.10.12
pyenv global 3.10.12
```

**Download from python.org:**
- Visit https://www.python.org/downloads/
- Download Python 3.10+ for macOS
- Install and update PATH

### Option 2: Use Frappe Version 13 (Supports Python 3.9)

Modify `bench_setup.sh` to use version-13 instead of version-14:
```bash
bench init --frappe-branch version-13 bench
```

### Option 3: Install Redis (Also Required)

Redis is required for Frappe/Bench:

**Using Homebrew:**
```bash
brew install redis
brew services start redis
```

**Manual Installation:**
- Download from https://redis.io/download
- Or use Docker: `docker run -d -p 6379:6379 redis`

## Next Steps

Once Python 3.10+ is installed:

1. Update the script to use the correct Python version
2. Install Redis
3. Run `./bench_setup.sh` again

## Alternative: Docker-based Setup

Consider using Frappe's Docker setup if local installation is problematic:
- https://github.com/frappe/frappe_docker

