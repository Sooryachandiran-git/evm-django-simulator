export PATH=$PATH:/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/bin
export FABRIC_CFG_PATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export PKG_ID="auditcc_1.0:d14048b5d6c9a896c1f72b26a7b79c0086fd601054875f26df5890be5117b3b2"

# Org1 Approve
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --channelID mychannel --name auditcc --version 1.0 --package-id $PKG_ID --sequence 1

# Org2 Approve
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode approveformyorg -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --channelID mychannel --name auditcc --version 1.0 --package-id $PKG_ID --sequence 1

# Commit
peer lifecycle chaincode commit -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --channelID mychannel --name auditcc --version 1.0 --sequence 1 --peerAddresses localhost:7051 --tlsRootCertFiles /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt --peerAddresses localhost:9051 --tlsRootCertFiles /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
