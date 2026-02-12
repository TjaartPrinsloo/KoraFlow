#!/bin/bash
set -e

# Default to false
ALLOW_PROD_MIGRATE=${ALLOW_PROD_MIGRATE:-false}
ENVIRONMENT=${ENVIRONMENT:-dev}

echo "Starting migration checks for environment: $ENVIRONMENT"

if [[ "$ENVIRONMENT" == "production" ]]; then
    if [[ "$ALLOW_PROD_MIGRATE" != "true" ]]; then
        echo "❌ CRITICAL ERROR: Attempted to run migration on PRODUCTION without explicit override."
        echo "To migrate production, you must set ALLOW_PROD_MIGRATE=true in the deployment configuration."
        echo "This is a safety lock to prevent data loss or corruption."
        exit 1
    else
        echo "⚠️  WARNING: Production migration override detected. Proceeding with caution..."
        # In a real scenario, we might pause here or check for a recent backup timestamp
    fi
fi

# Run the actual migration
echo "Running bench migrate..."
bench migrate
