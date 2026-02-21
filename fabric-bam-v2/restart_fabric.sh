#!/bin/bash
# High-reliability startup script for Fabric on Windows/WSL
export FABRIC_SAMPLES_DIR="/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples"
export PATH="$FABRIC_SAMPLES_DIR/bin:$PATH"
export FABRIC_CFG_PATH="$FABRIC_SAMPLES_DIR/config"

cd "$FABRIC_SAMPLES_DIR/test-network"

echo "Stopping any existing network..."
./network.sh down

echo "Pruning Docker volumes to clear old ledger data..."
docker volume prune -f

echo "Starting fresh Fabric network and creating channel..."
./network.sh up createChannel
