#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
INSTANCE_NAME="koraflow-db"
SERVICE_NAME="koraflow-app"
REPO_NAME="koraflow-repo"
IMAGE_TAG="latest"

echo "Using Project: $PROJECT_ID"

# 1. Enable APIs
echo "Enabling required APIs..."
gcloud services enable compute.googleapis.com run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# 2. Create database VM (e2-micro is free tier eligible)
if gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE > /dev/null 2>&1; then
    echo "Instance $INSTANCE_NAME already exists."
else
    echo "Creating VM instance $INSTANCE_NAME..."
    gcloud compute instances create $INSTANCE_NAME \
        --project=$PROJECT_ID \
        --zone=$ZONE \
        --machine-type=e2-micro \
        --image-family=debian-11 \
        --image-project=debian-cloud \
        --tags=koraflow-db-server
    
    # Allow traffic to DB ports (WARNING: This opens to public, strong passwords required)
    gcloud compute firewall-rules create allow-koraflow-db \
        --allow tcp:3306,tcp:6379 \
        --target-tags=koraflow-db-server
fi

# 3. Setup Database on VM
echo "Setting up Database on VM..."
DB_PASSWORD=$(openssl rand -base64 12)
REDIS_PASSWORD=$(openssl rand -base64 12)
echo "Generated DB_PASSWORD: $DB_PASSWORD"
echo "Generated REDIS_PASSWORD: $REDIS_PASSWORD"

# Copy docker-compose to VM
gcloud compute scp deploy/docker-compose.prod.yml $INSTANCE_NAME:~/docker-compose.yml --zone=$ZONE

# SSH to install Docker and start services
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="
    if ! command -v docker &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose
        sudo usermod -aG docker \$USER
    fi
    export DB_ROOT_PASSWORD='$DB_PASSWORD'
    export DB_PASSWORD='$DB_PASSWORD'
    export REDIS_PASSWORD='$REDIS_PASSWORD'
    sudo docker-compose up -d
"

# Get VM IP
VM_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "Database running at $VM_IP"

# 4. Create Artifact Registry Repository
if ! gcloud artifacts repositories describe $REPO_NAME --location=$REGION > /dev/null 2>&1; then
    gcloud artifacts repositories create $REPO_NAME --repository-format=docker --location=$REGION
fi

# 5. Build and Push Image
IMAGE_URI="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:$IMAGE_TAG"
echo "Building and pushing image to $IMAGE_URI..."
# Using Cloud Build to build in the cloud
gcloud builds submit --tag $IMAGE_URI .

# 6. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URI \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars="DB_HOST=$VM_IP,DB_PORT=3306,DB_USER=root,DB_PASSWORD=$DB_PASSWORD,REDIS_CACHE=redis://:$REDIS_PASSWORD@$VM_IP:6379,REDIS_QUEUE=redis://:$REDIS_PASSWORD@$VM_IP:6379,REDIS_SOCKETIO=redis://:$REDIS_PASSWORD@$VM_IP:6379"

echo "Deployment Complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region=$REGION --format='get(status.url)')"
echo "IMPORTANT: Save your DB credentials:"
echo "DB Password: $DB_PASSWORD"
echo "Redis Password: $REDIS_PASSWORD"
