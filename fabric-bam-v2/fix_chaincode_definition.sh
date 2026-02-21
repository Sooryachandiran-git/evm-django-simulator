#!/bin/bash
# Registration script for CCAAS Chaincode
export FABRIC_BASE="/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples"
export PATH="$FABRIC_BASE/bin:$PATH"
export FABRIC_CFG_PATH="$FABRIC_BASE/config"
export PKG_ID="auditcc_1.0:d14048b5d6c9a896c1f72b26a7b79c0086fd601054875f26df5890be5117b3b2"
export ORDERER_CA="$FABRIC_BASE/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

echo "1. Installing package on Org1..."
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ROOTCERT_FILE=$FABRIC_BASE/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=$FABRIC_BASE/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051
export CORE_PEER_TLS_ENABLED=true
peer lifecycle chaincode install /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/chaincode/auditcc/ccaas-pkg/auditcc.tar.gz

echo "2. Approving for Org1..."
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile $ORDERER_CA --channelID mychannel --name auditcc --version 1.0 --package-id $PKG_ID --sequence 1

echo "3. Installing and Approving for Org2..."
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_TLS_ROOTCERT_FILE=$FABRIC_BASE/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=$FABRIC_BASE/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051
peer lifecycle chaincode install /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/chaincode/auditcc/ccaas-pkg/auditcc.tar.gz
peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile $ORDERER_CA --channelID mychannel --name auditcc --version 1.0 --package-id $PKG_ID --sequence 1

echo "4. Committing to Channel..."
peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile $ORDERER_CA --channelID mychannel --name auditcc --version 1.0 --sequence 1 --peerAddresses localhost:7051 --tlsRootCertFiles $FABRIC_BASE/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt --peerAddresses localhost:9051 --tlsRootCertFiles $FABRIC_BASE/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

echo "Definition complete. Proceeding to restart container..."
