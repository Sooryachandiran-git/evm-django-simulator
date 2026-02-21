import requests
import hashlib
import ecdsa
import time
import asyncio
import os
import json
import subprocess

# Configs
DJANGO_URL = "http://localhost:8000/signals/TN-01-001/"
FABRIC_BASE = "/mnt/c/Users/12b23/Desktop/REC/E_VOTING/evm-blockchain-django/fabric-bam-v2/fabric-samples"
FABRIC_BIN_PATH = f"{FABRIC_BASE}/bin"
FABRIC_CFG_PATH = f"{FABRIC_BASE}/config"
ORDERER_CA = f"{FABRIC_BASE}/test-network/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem"

# ECDSA Keypair
sk = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
vk = sk.verifying_key
print(f"BAM Public Key: {vk.to_string().hex()}")

def sign_signal(signal):
    data = f"{signal.get('sequence',0)}{signal.get('candidateID','')}{signal.get('timestamp','')}"
    h = hashlib.sha256(data.encode()).digest()
    sig = sk.sign(h)
    return sig.hex()

async def submit_receipt_via_cli(signal):
    sig_hex = sign_signal(signal)
    ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    
    # Extract identity fields correctly from the new signal structure
    booth = signal.get('boothID', signal.get('booth', 'TN-01-001'))
    seq = str(signal.get('sequence', 0))
    candidate = signal.get('candidateID', 'UNKNOWN')
    
    # Args for Chaincode
    args = [booth, seq, candidate, sig_hex, ts]
    args_json = json.dumps({"function":"AppendReceipt", "Args": args})
    
    # Multi-peer configuration to satisfy endorsement policy
    PEER0_ORG1_CA = f"{FABRIC_BASE}/test-network/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
    PEER0_ORG2_CA = f"{FABRIC_BASE}/test-network/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
    
    PEER_CONNS = (
        f"--peerAddresses localhost:7051 --tlsRootCertFiles {PEER0_ORG1_CA} "
        f"--peerAddresses localhost:9051 --tlsRootCertFiles {PEER0_ORG2_CA}"
    )

    # Create a small temp script to avoid quoting issues with parentheses in $PATH
    script_content = f"""#!/bin/bash
export PATH=\"$PATH\":{FABRIC_BIN_PATH}
export FABRIC_CFG_PATH={FABRIC_CFG_PATH}
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID=Org1MSP
export CORE_PEER_TLS_ROOTCERT_FILE={PEER0_ORG1_CA}
export CORE_PEER_MSPCONFIGPATH={FABRIC_BASE}/test-network/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=localhost:7051

peer chaincode invoke -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile {ORDERER_CA} -C mychannel -n auditcc {PEER_CONNS} -c '{args_json}'
"""
    
    temp_script_name = f"invoke_{seq}.sh"
    temp_script_path = os.path.join(os.getcwd(), temp_script_name)
    
    with open(temp_script_path, "w", newline='\n') as f:
        f.write(script_content)
    
    wsl_script_path = temp_script_path.replace("C:", "/mnt/c").replace("\\", "/")
    cmd = ["wsl", "-d", "Ubuntu", "bash", wsl_script_path]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            print(f"Receipt BLOCK ADDED: Seq {seq}, Booth {booth}, Candidate {candidate}")
        else:
            print(f"Fabric Invoke Error: {stderr.decode()}")
    except Exception as e:
        print(f"Subprocess error: {e}")
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)

async def main_loop():
    last_seq = 0
    print("BAM Simulator Started. Polling Django...")
    while True:
        try:
            resp = requests.get(DJANGO_URL, timeout=10).json()
            
            signal_list = []
            if isinstance(resp, dict) and "signals" in resp:
                signal_list = resp["signals"]
            elif isinstance(resp, list):
                signal_list = resp
            else:
                signal_list = [resp]

            for signal_wrapper in signal_list:
                if "raw_signal" in signal_wrapper:
                     try:
                        signal = json.loads(signal_wrapper["raw_signal"])
                     except json.JSONDecodeError:
                        continue
                else:
                    signal = signal_wrapper

                seq_val = signal.get('sequence')
                if seq_val is None: continue
                seq = int(seq_val)
                
                if seq > last_seq:
                    print(f"Processing new vote signal: {signal}")
                    await submit_receipt_via_cli(signal)
                    last_seq = seq
        except Exception as e:
            # print(f"Poll error: {e}")
            pass
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main_loop())
