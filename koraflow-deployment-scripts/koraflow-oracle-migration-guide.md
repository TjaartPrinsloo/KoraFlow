# KoraFlow Oracle Cloud Migration Guide

This guide details the process of migrating KoraFlow from Google Cloud Platform (GCP) to Oracle Cloud Infrastructure (OCI).

## Pre-migration Checklist

- [ ] Active Oracle Cloud Account
- [ ] OCI Compute Instance (ARM/A1 Flex recommended)
- [ ] OCI CLI configured on local machine
- [ ] SSH Access to Oracle instance

## Migration Steps

### 1. Automated Setup

The easiest way to set up your Oracle environment is using the setup wizard:

```bash
./auto-setup-wizard.sh
```

Follow the interactive prompts to discover your instances and generate credentials.

### 2. Manual Server Setup (Optional)

If you prefer manual control:

```bash
./complete-setup.sh
```

### 3. Database Migration

Transfer your data from GCP Cloud SQL:

```bash
./migrate-database.sh
```

### 4. CI/CD Pipeline

Set up automatic deployments:
1. Copy `github-actions-deploy.yml` to `.github/workflows/`.
2. Configure GitHub Secrets:
   - `ORACLE_HOST`: Your instance Public IP.
   - `SSH_PRIVATE_KEY`: Your generated SSH private key.

## Troubleshooting

### SSH Connectivity
- Ensure port 22 is open in the VCN Security List.
- Verify the SSH key is added to the instance metadata.

### Frappe Installation
- Logs are located at `~/frappe-bench/logs/`.
- Use `bench start` for manual debugging.

## Support

For issues, please refer to the [Frappe Forum](https://discuss.erpnext.com) or Oracle Cloud documentation.
