# Blockchain Audit Integration (Hyperledger Fabric)

This document explains how to set up and run the blockchain audit layer for the EVM Simulator. This layer uses **Hyperledger Fabric** to create an immutable record of every vote signal captured by the Ballot Audit Module (BAM).

## Prerequisites

1.  **Windows 10/11 with WSL2 (Ubuntu 20.04/22.04 recommended)**.
2.  **Docker Desktop** (with WSL2 integration enabled).
3.  **Hyperledger Fabric Binaries** (Included in `fabric-samples/bin`).
4.  **Python 3.9+** (For the BAM Simulator).

---

## Setup & Execution Flow

To start the system from scratch, follow these steps in separate terminals.

### 1. Reset and Start Fabric Ledger (Terminal 1 - WSL)
Wipe all previous blocks and start the fresh network nodes.
```powershell
cd C:\Users\12b23\Desktop\REC\E_VOTING\evm-blockchain-django\fabric-bam-v2
wsl -d Ubuntu bash ./restart_fabric.sh
```
*Wait for it to say `Channel 'mychannel' created`.*

### 2. Define Chaincode & Start Container (Terminal 2 - WSL/Docker)
Register the smart contract on the ledger and start the logic container.
```powershell
# In WSL
cd /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2
./fix_chaincode_definition.sh

# Start the Chaincode Container (In PowerShell/Docker)
docker rm -f auditcc.org1.example.com
docker run -d --name auditcc.org1.example.com --network fabric_test \
  -e CORE_CHAINCODE_ID_NAME=auditcc_1.0:d14048b5d6c9a896c1f72b26a7b79c0086fd601054875f26df5890be5117b3b2 \
  -e CHAINCODE_SERVER_ADDRESS=0.0.0.0:9999 auditcc-image
```

### 3. Start BAM Simulator (Terminal 3 - PowerShell)
Bridges the Django votes to the Fabric ledger.
```powershell
cd C:\Users\12b23\Desktop\REC\E_VOTING\evm-blockchain-django\fabric-bam-v2\bam-sim
.\venv\Scripts\activate
python bam_simulator.py
```
*Note: If dependencies are missing, run `pip install requests ecdsa pyserial`.*

---

## Verification Scripts

Use these scripts in WSL to check the state of the blockchain:

- **List All Receipts**: `./list_all.sh` (Shows all votes on the ledger)
- **Get Ledger Info**: `./get_ledger_info.sh` (Shows current block height)
- **Query Specific Vote**: `./query_vote.sh <BOOTH_ID> <SEQUENCE>`

---

## Architecture details
- **Chaincode**: `auditcc` (written in Go)
- **BAM**: Listens to Django's `signals` endpoint and invokes Fabric CLI via WSL.
- **Consensus**: Solo Raft (Default Test Network)
