package main

import (
	"encoding/json"
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

type AuditReceipt struct {
	Booth string `json:"booth"`
	Seq   string `json:"seq"`
	Hash  string `json:"hash"`
	Sig   string `json:"sig"`
	Ts    string `json:"ts"`
}

type AuditCC struct {
	contractapi.Contract
}

func (s *AuditCC) AppendReceipt(ctx contractapi.TransactionContextInterface, booth, seq, hash, sig, ts string) error {
	receipt := AuditReceipt{Booth: booth, Seq: seq, Hash: hash, Sig: sig, Ts: ts}
	receiptJSON, _ := json.Marshal(receipt)
	return ctx.GetStub().PutState(fmt.Sprintf("%s-%s", booth, seq), receiptJSON)
}

func (s *AuditCC) QueryReceipt(ctx contractapi.TransactionContextInterface, booth, seq string) (*AuditReceipt, error) {
    fmt.Printf("Querying for booth: %s, seq: %s\n", booth, seq)
	receiptJSON, err := ctx.GetStub().GetState(fmt.Sprintf("%s-%s", booth, seq))
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if receiptJSON == nil {
		return nil, fmt.Errorf("receipt %s-%s does not exist", booth, seq)
	}

	var receipt AuditReceipt
	err = json.Unmarshal(receiptJSON, &receipt)
	if err != nil {
		return nil, err
	}

	return &receipt, nil
}

func (s *AuditCC) GetAllReceipts(ctx contractapi.TransactionContextInterface) ([]*AuditReceipt, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var receipts []*AuditReceipt
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var receipt AuditReceipt
		err = json.Unmarshal(queryResponse.Value, &receipt)
		if err == nil {
			receipts = append(receipts, &receipt)
		}
	}

	return receipts, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&AuditCC{})
	if err != nil {
		panic(err)
	}
	if err := chaincode.Start(); err != nil {
		panic(err)
	}
}
