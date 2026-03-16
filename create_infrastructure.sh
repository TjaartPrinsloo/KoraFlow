#!/bin/bash
set -e

# Configuration
COMPARTMENT_ID=$(grep tenancy ~/.oci/config | cut -d'=' -f2 | tr -d ' ')
REGION="af-johannesburg-1"
IMAGE_ID="ocid1.image.oc1.af-johannesburg-1.aaaaaaaayhkamt6lmgzwyq7y44qulzbu2du7hwcftdfmi6wdoakagwngvxpa" # Ubuntu 22.04 aarch64
SSH_PUB_KEY=$(cat ~/.ssh/koraflow_oracle.pub)

echo "Using Compartment: $COMPARTMENT_ID"

# 1. Create VCN
echo "Creating VCN..."
VCN_JSON=$(oci network vcn create --compartment-id "$COMPARTMENT_ID" --cidr-block "10.0.0.0/16" --display-name "koraflow-vcn" --dns-label "koraflowvcn" --wait-for-state AVAILABLE)
VCN_ID=$(echo "$VCN_JSON" | jq -r '.data.id')
echo "VCN Created: $VCN_ID"

# 2. Create Internet Gateway
echo "Creating Internet Gateway..."
IG_JSON=$(oci network internet-gateway create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --enabled true --display-name "koraflow-ig" --wait-for-state AVAILABLE)
IG_ID=$(echo "$IG_JSON" | jq -r '.data.id')
echo "Internet Gateway Created: $IG_ID"

# 3. Create Route Table
echo "Creating Route Table..."
# We need to update the default route table or create a new one. Let's create a new one to be clean.
RT_JSON=$(oci network route-table create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-rt" --route-rules '[{"cidrBlock":"0.0.0.0/0","networkEntityId":"'"$IG_ID"'"}]' --wait-for-state AVAILABLE)
RT_ID=$(echo "$RT_JSON" | jq -r '.data.id')
echo "Route Table Created: $RT_ID"

# 4. Create Security List
echo "Creating Security List..."
SL_JSON=$(oci network security-list create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-sl" --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all"}]' --ingress-security-rules '[{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":22,"min":22}}},{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":80,"min":80}}},{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":443,"min":443}}},{"protocol":"1","source":"0.0.0.0/0","icmpOptions":{"type":3,"code":4}}]' --wait-for-state AVAILABLE)
SL_ID=$(echo "$SL_JSON" | jq -r '.data.id')
echo "Security List Created: $SL_ID"

# 5. Create Subnet
echo "Creating Subnet..."
SUBNET_JSON=$(oci network subnet create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --cidr-block "10.0.1.0/24" --display-name "koraflow-public-subnet" --dns-label "public" --route-table-id "$RT_ID" --security-list-ids "[\"$SL_ID\"]" --wait-for-state AVAILABLE)
SUBNET_ID=$(echo "$SUBNET_JSON" | jq -r '.data.id')
echo "Subnet Created: $SUBNET_ID"

# 6. Launch Instance
echo "Launching Compute Instance (VM.Standard.A1.Flex, 4 OCPU, 24GB RAM)..."
INSTANCE_JSON=$(oci compute instance launch --compartment-id "$COMPARTMENT_ID" --availability-domain "$(oci iam availability-domain list --compartment-id "$COMPARTMENT_ID" | jq -r '.data[0].name')" --shape "VM.Standard.A1.Flex" --shape-config '{"ocpus":4,"memoryInGBs":24}' --image-id "$IMAGE_ID" --subnet-id "$SUBNET_ID" --display-name "koraflow-production" --assign-public-ip true --ssh-authorized-keys "$SSH_PUB_KEY" --wait-for-state RUNNING)
INSTANCE_ID=$(echo "$INSTANCE_JSON" | jq -r '.data.id')
PUBLIC_IP=$(oci compute instance list-vnics --instance-id "$INSTANCE_ID" | jq -r '.data[0]."public-ip"')

echo "Instance Launched: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Setup Complete!"
