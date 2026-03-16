#!/bin/bash
set -e

# Configuration
export SUPPRESS_LABEL_WARNING=True
COMPARTMENT_ID=$(grep tenancy ~/.oci/config | cut -d'=' -f2 | tr -d ' ')
REGION="af-johannesburg-1"
IMAGE_ID="ocid1.image.oc1.af-johannesburg-1.aaaaaaaayhkamt6lmgzwyq7y44qulzbu2du7hwcftdfmi6wdoakagwngvxpa"
SSH_PUB_KEY=$(cat ~/.ssh/koraflow_oracle.pub)

echo "Using Compartment: $COMPARTMENT_ID"

# 1. Get or Create VCN
echo "Checking VCN..."
VCN_ID=$(oci network vcn list --compartment-id "$COMPARTMENT_ID" --display-name "koraflow-vcn" --all | jq -r '.data[0].id // empty')

if [ -z "$VCN_ID" ]; then
    echo "Creating VCN..."
    VCN_JSON=$(oci network vcn create --compartment-id "$COMPARTMENT_ID" --cidr-block "10.0.0.0/16" --display-name "koraflow-vcn" --dns-label "koraflowvcn" --wait-for-state AVAILABLE)
    VCN_ID=$(echo "$VCN_JSON" | jq -r '.data.id')
fi
echo "Using VCN: $VCN_ID"

# 2. Get or Create Internet Gateway
echo "Checking Internet Gateway..."
IG_ID=$(oci network internet-gateway list --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-ig" --all | jq -r '.data[0].id // empty')

if [ -z "$IG_ID" ]; then
    echo "Creating Internet Gateway..."
    IG_JSON=$(oci network internet-gateway create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --is-enabled true --display-name "koraflow-ig" --wait-for-state AVAILABLE)
    IG_ID=$(echo "$IG_JSON" | jq -r '.data.id')
fi
echo "Using Internet Gateway: $IG_ID"

# 3. Get or Create Route Table
echo "Checking Route Table..."
# We look for our custom one, or we could update the default. Let's stick to creating/using 'koraflow-rt'
RT_ID=$(oci network route-table list --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-rt" --all | jq -r '.data[0].id // empty')

if [ -z "$RT_ID" ]; then
    echo "Creating Route Table..."
    RT_JSON=$(oci network route-table create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-rt" --route-rules '[{"cidrBlock":"0.0.0.0/0","networkEntityId":"'"$IG_ID"'"}]' --wait-for-state AVAILABLE)
    RT_ID=$(echo "$RT_JSON" | jq -r '.data.id')
fi
echo "Using Route Table: $RT_ID"

# 4. Get or Create Security List
echo "Checking Security List..."
SL_ID=$(oci network security-list list --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-sl" --all | jq -r '.data[0].id // empty')

if [ -z "$SL_ID" ]; then
    echo "Creating Security List..."
    SL_JSON=$(oci network security-list create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-sl" --egress-security-rules '[{"destination":"0.0.0.0/0","protocol":"all"}]' --ingress-security-rules '[{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":22,"min":22}}},{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":80,"min":80}}},{"protocol":"6","source":"0.0.0.0/0","tcpOptions":{"destinationPortRange":{"max":443,"min":443}}},{"protocol":"1","source":"0.0.0.0/0","icmpOptions":{"type":3,"code":4}}]' --wait-for-state AVAILABLE)
    SL_ID=$(echo "$SL_JSON" | jq -r '.data.id')
fi
echo "Using Security List: $SL_ID"

# 5. Get or Create Subnet
echo "Checking Subnet..."
SUBNET_ID=$(oci network subnet list --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --display-name "koraflow-public-subnet" --all | jq -r '.data[0].id // empty')

if [ -z "$SUBNET_ID" ]; then
    echo "Creating Subnet..."
    SUBNET_JSON=$(oci network subnet create --compartment-id "$COMPARTMENT_ID" --vcn-id "$VCN_ID" --cidr-block "10.0.1.0/24" --display-name "koraflow-public-subnet" --dns-label "public" --route-table-id "$RT_ID" --security-list-ids "[\"$SL_ID\"]" --wait-for-state AVAILABLE)
    SUBNET_ID=$(echo "$SUBNET_JSON" | jq -r '.data.id')
fi
echo "Using Subnet: $SUBNET_ID"

# 6. Get or Launch Instance
echo "Checking Compute Instance..."
INSTANCE_ID=$(oci compute instance list --compartment-id "$COMPARTMENT_ID" --display-name "koraflow-production" --all | jq -r '.data[0].id // empty')

if [ -z "$INSTANCE_ID" ]; then
    echo "Launching Compute Instance (VM.Standard.A1.Flex, 4 OCPU, 24GB RAM)..."
    AD_NAME=$(oci iam availability-domain list --compartment-id "$COMPARTMENT_ID" | jq -r '.data[0].name')
    INSTANCE_JSON=$(oci compute instance launch --compartment-id "$COMPARTMENT_ID" --availability-domain "$AD_NAME" --shape "VM.Standard.A1.Flex" --shape-config '{"ocpus":4,"memoryInGBs":24}' --image-id "$IMAGE_ID" --subnet-id "$SUBNET_ID" --display-name "koraflow-production" --assign-public-ip true --ssh-authorized-keys-file ~/.ssh/koraflow_oracle.pub --wait-for-state RUNNING)
    INSTANCE_ID=$(echo "$INSTANCE_JSON" | jq -r '.data.id')
fi

# Get Public IP (wait for it if not assigned yet)
PUBLIC_IP=$(oci compute instance list-vnics --instance-id "$INSTANCE_ID" | jq -r '.data[0]."public-ip"')
while [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" == "null" ]; do
    echo "Waiting for Public IP..."
    sleep 5
    PUBLIC_IP=$(oci compute instance list-vnics --instance-id "$INSTANCE_ID" | jq -r '.data[0]."public-ip"')
done

echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "Setup Complete!"
