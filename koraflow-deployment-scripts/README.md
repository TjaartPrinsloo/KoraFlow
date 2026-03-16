# 🚀 KoraFlow Oracle Cloud - One-Command Setup

**The easiest way to deploy KoraFlow to Oracle Cloud - completely automated!**

## ⚡ Super Quick Start (5 Minutes)

Just run this ONE command and everything is configured automatically:

```bash
./auto-setup-wizard.sh
```

The wizard will:
- ✅ Auto-detect your Oracle Cloud instances
- ✅ Discover existing configurations
- ✅ Generate all credentials
- ✅ Install everything
- ✅ Deploy your application
- ✅ Setup CI/CD pipeline

---

## 🔍 Features

- **Auto-Discovery**: Automatically finds compute instances in your tenancy.
- **Intelligent Detection**: Detects existing Frappe installations and preserves them.
- **Secure**: Generates cryptographically secure passwords and unique SSH keys.
- **Automated**: Full one-command setup for fresh installations.

## 🎯 Usage Options

### Option 1: Fully Automated (Recommended)

```bash
./auto-setup-wizard.sh
```

### Option 2: Manual Setup

```bash
./complete-setup.sh
```

### Option 3: Database Migration

```bash
./migrate-database.sh
```

---

## 📁 File Structure

```
koraflow-deployment-scripts/
├── auto-setup-wizard.sh         # ⭐ ONE-COMMAND setup (use this!)
├── complete-setup.sh            # Manual server setup
├── migrate-database.sh          # GCP to Oracle migration
├── quick-deploy.sh              # Fast manual deployments
├── github-actions-deploy.yml    # CI/CD pipeline
├── koraflow-oracle-migration-guide.md  # Detailed docs
└── README.md                    # This file
```

---

## 🔐 Security

The wizard stores all generated credentials in `~/.koraflow-config/CREDENTIALS.txt` with restricted permissions (`chmod 600`). **Backup this directory securely!**

---

## 📊 Cost Breakdown

Oracle Cloud Free Tier:
- 💰 **$0/month** - 4 OCPUs, 24GB RAM
- 💰 **$0/month** - 200GB storage

🚀 **Total Cost: $0/month!**
