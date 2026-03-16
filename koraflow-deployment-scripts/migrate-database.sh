#!/bin/bash
###############################################################################
# KoraFlow Database Migration (GCP to Oracle)
# Transfers data from Cloud SQL to Oracle MariaDB
###############################################################################

set -e

# Configuration
CONFIG_FILE="$HOME/.koraflow-config/deployment.conf"
source "$CONFIG_FILE"

# MariaDB credentials
DB_NAME="koraflow"
DB_USER="koraflow"

echo "--------------------------------------------------------"
echo "KoraFlow Database Migration Tool"
echo "--------------------------------------------------------"

read -p "Enter GCP Cloud SQL instance name: " GCP_INSTANCE
read -p "Enter GCP Project ID: " GCP_PROJECT
read -p "Enter Database name to migrate: " GCP_DB_NAME

echo "1. Exporting data from GCP..."
gcloud sql export sql $GCP_INSTANCE gs://koraflow-migrations/backup.sql --database=$GCP_DB_NAME --project=$GCP_PROJECT

echo "2. Downloading backup..."
gsutil cp gs://koraflow-migrations/backup.sql ./backup.sql

echo "3. Uploading to Oracle server..."
scp -i "$SSH_KEY_PATH" ./backup.sql "${SSH_USER}@${ORACLE_IP}:/tmp/"

echo "4. Importing to Oracle MariaDB..."
ssh -i "$SSH_KEY_PATH" "${SSH_USER}@${ORACLE_IP}" <<EOF
    sudo mysql -u root -p$MYSQL_ROOT_PASSWORD $DB_NAME < /tmp/backup.sql
    echo "Import complete!"
EOF

echo "5. Cleanup..."
rm ./backup.sql
echo "--------------------------------------------------------"
echo "Migration Complete!"
echo "--------------------------------------------------------"
