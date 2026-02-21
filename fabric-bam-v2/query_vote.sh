export PATH=$PATH:/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/bin
export FABRIC_CFG_PATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ROOTCERT_FILE=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

BOOTH=$1
SEQ=$2

if [ -z "$BOOTH" ] || [ -z "$SEQ" ]; then
    echo "Usage: bash query_vote.sh <boothID> <sequence>"
    exit 1
fi

peer chaincode query -C mychannel -n auditcc -c "{\"Args\":[\"QueryReceipt\", \"$BOOTH\", \"$SEQ\"]}"
