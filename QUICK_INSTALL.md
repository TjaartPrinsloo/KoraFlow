# Quick Installation Guide for System Dependencies

## ⚠️ Manual Steps Required

Homebrew installation requires interactive access (sudo password), so it must be done manually.

## Step-by-Step Instructions

### Step 1: Install Homebrew

Open a terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions. You'll be prompted for your password.

### Step 2: Add Homebrew to PATH

After installation, add Homebrew to your PATH:

**For Apple Silicon Macs (M1/M2/M3):**
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/opt/homebrew/bin/brew shellenv)"
```

**For Intel Macs:**
```bash
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zshrc
eval "$(/usr/local/bin/brew shellenv)"
```

### Step 3: Run Installation Script

Navigate to the KoraFlow directory and run:

```bash
cd /Users/tjaartprinsloo/Documents/KoraFlow
./install_system_dependencies.sh
```

This will automatically:
- Install `libmagic` for Drive
- Install `pkg-config` and `mariadb` for Insights
- Install Python packages: `python-magic`, `mysqlclient`, and `ibis-framework[mysql]`

### Step 4: Reinstall Drive

After the dependencies are installed, reinstall the Drive app:

```bash
cd bench
bench --site koraflow-site install-app drive
```

## Verification

To verify everything is working:

```bash
# Check Drive installation
cd bench
bench --site koraflow-site console
# In console: import magic; print("Drive libmagic: OK")

# Check Insights MySQL backend
# In console: import ibis; print("Insights MySQL:", ibis.mysql)
```

## Troubleshooting

If you encounter issues:

1. **Homebrew not found after installation:**
   - Make sure you added it to your PATH (Step 2)
   - Restart your terminal or run: `source ~/.zshrc`

2. **Permission errors:**
   - Make sure you're using the correct Homebrew path
   - Try: `sudo chown -R $(whoami) /opt/homebrew` (Apple Silicon)
   - Or: `sudo chown -R $(whoami) /usr/local` (Intel)

3. **mysqlclient build fails:**
   - Ensure MariaDB is installed: `brew list mariadb`
   - Check environment variables are set in the script

For more details, see `SYSTEM_DEPENDENCIES.md`.

