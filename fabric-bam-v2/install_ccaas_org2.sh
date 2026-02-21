export PATH=$PATH:/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/bin
export FABRIC_CFG_PATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=Org2MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
export CORE_PEER_ADDRESS=localhost:9051

peer lifecycle chaincode install /mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/chaincode/auditcc/ccaas-pkg/auditcc.tar.gz
