# 🚀 KoraFlow Oracle Cloud - One-Command Setup

**The easiest way to deploy KoraFlow to Oracle Cloud - completely automated!**

## ⚡ Super Quick Start (5 Minutes)

Just run this ONE command and everything is configured automatically:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/koraflow-deployment-scripts/main/auto-setup-wizard.sh | bash
```

That's it! The wizard will:
- ✅ Auto-detect your Oracle Cloud instances
- ✅ Discover existing configurations
- ✅ Generate all credentials
- ✅ Install everything
- ✅ Deploy your application
- ✅ Setup CI/CD pipeline

**No manual configuration needed!**

---

## 📹 What the Wizard Does

The auto-setup wizard is an intelligent script that:

1. **Installs OCI CLI** (if not present)
2. **Auto-discovers** your Oracle Cloud instances
3. **Detects** existing Frappe installations
4. **Generates** secure passwords automatically
5. **Configures** SSH access
6. **Installs** all dependencies
7. **Deploys** your application
8. **Sets up** automated deployments

### Before You Run

You'll need:
- An Oracle Cloud account (free tier works!)
- A running compute instance (or the wizard can help you create one)
- Your GitHub repository URL (optional)

### What You'll Get

After running the wizard:
- ✅ Fully configured KoraFlow installation
- ✅ All credentials auto-generated and saved
- ✅ SSH access configured
- ✅ Automated deployment pipeline
- ✅ Complete documentation

---

## 🎯 Usage Options

### Option 1: Fully Automated (Recommended)

```bash
# Download and run the wizard
curl -sSL https://YOUR_REPO/auto-setup-wizard.sh -o setup.sh
chmod +x setup.sh
./setup.sh

# Follow the interactive prompts
# The wizard will discover everything automatically!
```

### Option 2: Manual Setup (Advanced Users)

If you prefer manual control, use the individual scripts:

```bash
# Download all scripts
git clone YOUR_REPO
cd koraflow-deployment-scripts

# 1. Edit configuration
nano complete-setup.sh

# 2. Run on Oracle server
./complete-setup.sh

# 3. Migrate database
./migrate-database.sh

# 4. Setup CI/CD
cp github-actions-deploy.yml .github/workflows/
```

---

## 📋 Detailed Guide

See the [Complete Migration Guide](koraflow-oracle-migration-guide.md) for detailed instructions.

---

## 🔍 Auto-Discovery Features

The wizard automatically finds:

### Oracle Cloud Resources
- ✅ All compute instances in your tenancy
- ✅ Public IP addresses
- ✅ Instance states (running/stopped)
- ✅ Instance configurations (shape, OCPUs, RAM)

### Existing Installations
- ✅ Frappe installations
- ✅ Site names and configurations
- ✅ Database credentials
- ✅ Running services

### Network Configuration
- ✅ SSH connectivity
- ✅ Port accessibility
- ✅ Firewall rules

---

## 💾 What Gets Created

After running the wizard, you'll find:

```
~/.koraflow-config/
├── deployment.conf          # Main configuration file
├── CREDENTIALS.txt          # All your passwords (KEEP SAFE!)
├── install-on-oracle.sh     # Installation script
└── deploy-app.sh            # Deployment script
```

### Sample Credentials Output

```
Instance Information:
  Public IP:     132.145.xxx.xxx
  Instance Name: koraflow-production
  SSH Key:       ~/.ssh/koraflow_oracle

Application:
  Site URL:      http://132.145.xxx.xxx
  Admin User:    Administrator
  Admin Pass:    [auto-generated]

Database:
  Root Password: [auto-generated]
  User Password: [auto-generated]
```

---

## 🎬 Interactive Experience

The wizard provides a beautiful interactive experience:

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██╗  ██╗ ██████╗ ██████╗  █████╗ ███████╗██╗      ██████╗ ██╗ ║
║   ██║ ██╔╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██║     ██╔═══██╗██║ ║
║   █████╔╝ ██║   ██║██████╔╝███████║█████╗  ██║     ██║   ██║██║ ║
║   ██╔═██╗ ██║   ██║██╔══██╗██╔══██║██╔══╝  ██║     ██║   ██║██║ ║
║   ██║  ██╗╚██████╔╝██║  ██║██║  ██║██║     ███████╗╚██████╔╝██║ ║
║   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝ ║
║                                                                  ║
║           Oracle Cloud Auto-Setup & Deployment Wizard           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

✓ Checking prerequisites...
✓ OCI CLI is installed
✓ Discovering Oracle Cloud resources...
✓ Found 1 compute instance(s)
✓ Auto-selected instance: koraflow-production
✓ Public IP: 132.145.xxx.xxx
✓ SSH connection successful
```

---

## 🔧 Configuration Questions

The wizard will ask you:

1. **Select Instance** (if you have multiple)
   - Shows all your compute instances
   - Displays status, shape, and state
   - Auto-selects if only one exists

2. **GitHub Repository** (optional)
   - Your custom app repository URL
   - Branch to deploy (default: main)

3. **Domain Name**
   - Your domain or use IP for testing
   - Can be changed later

4. **API Keys** (optional)
   - Xero credentials
   - The Courier Guy API key
   - Google Maps API key
   - Can be added later in config

---

## 🚀 Deployment After Setup

Once setup is complete, deploying updates is automatic:

### Automatic Deployment (GitHub Actions)

```bash
# Just push to GitHub!
git add .
git commit -m "Update feature"
git push origin main

# GitHub Actions automatically:
# ✓ Pulls code to Oracle server
# ✓ Runs database migrations
# ✓ Builds assets
# ✓ Restarts services
```

### Manual Deployment

```bash
# Use the generated deploy script
bash ~/.koraflow-config/deploy-app.sh

# Or use the quick deploy helper
./quick-deploy.sh production
```

---

## 📁 Complete File Structure

After running the wizard:

```
koraflow-deployment-scripts/
├── auto-setup-wizard.sh         # ⭐ ONE-COMMAND setup (use this!)
├── complete-setup.sh            # Manual server setup
├── migrate-database.sh          # GCP to Oracle migration
├── quick-deploy.sh              # Fast manual deployments
├── github-actions-deploy.yml    # CI/CD pipeline
├── koraflow-oracle-migration-guide.md  # Detailed docs
└── README.md                    # This file

~/.koraflow-config/              # Auto-generated by wizard
├── deployment.conf              # Your configuration
├── CREDENTIALS.txt              # All passwords
├── install-on-oracle.sh         # Generated install script
└── deploy-app.sh                # Generated deploy script
```

---

## 🎯 Which Script Should I Use?

### Use `auto-setup-wizard.sh` if:
- ✅ You want everything automated
- ✅ You're setting up for the first time
- ✅ You have an Oracle Cloud account ready
- ✅ You want the easiest experience

### Use `complete-setup.sh` if:
- You want more manual control
- You need to customize before installation
- You're an advanced user

### Use `migrate-database.sh` if:
- You're migrating from GCP Cloud SQL
- You have existing data to transfer

### Use `quick-deploy.sh` if:
- You've already completed setup
- You need fast manual deployments
- You want deployment helpers

---

## 🔐 Security

The wizard:
- ✅ Generates cryptographically secure passwords
- ✅ Creates unique SSH keys
- ✅ Stores credentials in `chmod 600` files
- ✅ Never transmits credentials to external servers
- ✅ Keeps everything on your local machine

**Important:** Backup your `~/.koraflow-config/` directory securely!

---

## 🐛 Troubleshooting

### Wizard won't start
```bash
# Check if you have bash
bash --version

# Make script executable
chmod +x auto-setup-wizard.sh

# Run with verbose output
bash -x auto-setup-wizard.sh
```

### Can't connect to Oracle
```bash
# Verify OCI CLI is configured
oci iam region list

# Check instance is running
oci compute instance list --compartment-id YOUR_TENANCY_ID
```

### SSH connection fails
```bash
# Check security list allows port 22
# Check SSH key is added to instance
# Try manual SSH:
ssh -i ~/.ssh/koraflow_oracle ubuntu@YOUR_IP
```

See [Complete Migration Guide](koraflow-oracle-migration-guide.md#troubleshooting) for more help.

---

## 💡 Pro Tips

1. **Run on macOS or Linux** - The wizard works best on Unix-like systems

2. **Use the wizard multiple times** - It's safe to re-run if something fails

3. **Check existing installations** - The wizard detects and preserves existing setups

4. **Save your config** - Backup `~/.koraflow-config/` after setup

5. **Test before production** - Use a staging instance first

---

## 🎓 Learning Path

### Beginner
1. Run `auto-setup-wizard.sh`
2. Follow the prompts
3. Access your application
4. Start using KoraFlow!

### Intermediate
1. Run the wizard
2. Review generated scripts
3. Customize `deployment.conf`
4. Setup GitHub Actions

### Advanced
1. Use manual scripts
2. Customize installation
3. Implement custom deployment strategies
4. Setup monitoring and backups

---

## 📊 Cost Breakdown

### Oracle Cloud (Free Tier - Forever)
- 💰 **$0/month** - 4 OCPUs, 24GB RAM
- 💰 **$0/month** - 200GB storage
- 💰 **$0/month** - 10TB/month bandwidth

### Total Cost
💰 **$0/month** - Completely free!

---

## 🎉 Success Checklist

After running the wizard, you should have:

- [ ] Oracle Cloud instance configured
- [ ] SSH access working
- [ ] Frappe/ERPNext installed
- [ ] Your custom app deployed
- [ ] All services running
- [ ] Admin credentials saved
- [ ] GitHub Actions configured (optional)
- [ ] SSL ready to enable
- [ ] Backup system in place

---

## 🆘 Support & Resources

### Documentation
- [Complete Migration Guide](koraflow-oracle-migration-guide.md)
- [Frappe Documentation](https://frappeframework.com/docs)
- [Oracle Cloud Docs](https://docs.oracle.com/cloud)

### Community
- [Frappe Forum](https://discuss.erpnext.com)
- [ERPNext Community](https://discuss.erpnext.com)

### Need Help?
1. Check the troubleshooting section
2. Review logs: `~/.koraflow-config/wizard.log`
3. Search the Frappe forum
4. Check Oracle Cloud status

---

## 🔄 Update & Maintenance

### Update the wizard
```bash
curl -sSL https://YOUR_REPO/auto-setup-wizard.sh -o auto-setup-wizard.sh
chmod +x auto-setup-wizard.sh
```

### Update your deployment
```bash
# Automatic (if GitHub Actions configured)
git push origin main

# Manual
bash ~/.koraflow-config/deploy-app.sh
```

### Backup your data
```bash
ssh -i ~/.ssh/koraflow_oracle frappe@YOUR_IP
cd ~/frappe-bench
bench --site YOUR_SITE backup --with-files
```

---

## 📝 Changelog

### Version 2.0 - Auto-Setup Wizard
- ✨ **NEW:** One-command automated setup
- ✨ Auto-discovery of Oracle Cloud resources
- ✨ Intelligent configuration detection
- ✨ Interactive wizard interface
- ✨ Auto-generated credentials

### Version 1.0 - Manual Scripts
- Initial release
- Manual configuration scripts
- GitHub Actions workflow
- Database migration tools

---

## 🎯 Quick Reference

### One-Line Setup
```bash
curl -sSL https://YOUR_REPO/auto-setup-wizard.sh | bash
```

### Access Your App
```bash
# Open in browser
http://YOUR_ORACLE_IP

# SSH to server
ssh -i ~/.ssh/koraflow_oracle ubuntu@YOUR_IP
```

### Deploy Updates
```bash
# Auto (GitHub)
git push origin main

# Manual
bash ~/.koraflow-config/deploy-app.sh
```

### View Credentials
```bash
cat ~/.koraflow-config/CREDENTIALS.txt
```

---

**🚀 Ready to get started? Run the wizard now!**

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_REPO/koraflow-deployment-scripts/main/auto-setup-wizard.sh -o setup.sh && chmod +x setup.sh && ./setup.sh
```

---

**Last Updated:** February 12, 2026  
**Version:** 2.0 (Auto-Setup Wizard)  
**Compatible:** Frappe v15, ERPNext v15, Ubuntu 22.04, Oracle Cloud ARM
