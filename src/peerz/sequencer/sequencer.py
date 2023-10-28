from functools import partial

import os
import hivemind
import time
import threading
from typing import List
import json
from web3 import Web3

logger = hivemind.get_logger(__name__)

private_key = "---"


# Get the directory of the current script
script_dir = os.path.dirname(__file__)

# Construct the path to the JSON file relative to the script location
# For example, if the JSON file is in the parent directory of the script
abi_file_path = os.path.join(script_dir, 'abi.json')

# Load the ABI
with open(abi_file_path, 'r') as abi_file:
    contract_abi = json.load(abi_file)

# Setup Web3 connection (example with a local Ethereum node)
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545/'))

# Assuming you have the contract's address
contract_address = '0xa513E6E4b8f2a923D98304ec87F64353C4D5C853'

# Create the contract instance
contract = w3.eth.contract(address=contract_address, abi=contract_abi)


class Sequencer:
    def __init__(
        self,
        *,
        initial_peers: List[str],
        address: str,
        check_period: float = 60,
    ):
        logger.info("Connecting to DHT")
        self.check_period = check_period
        self.initial_peers = initial_peers
        self.updater = None
        self.address = address
        self.stop = threading.Event()
    def run(self):
        while True:
            try:
                dht = hivemind.DHT(self.initial_peers, client_mode=True, num_workers=32, start=True)
                data = dht.get("_peerz.validators")

                # get the addresses of the validators
                addresses = list(data.value.keys())
                print(data.value.values());
                first_validator_data = next(iter(data.value.values())).value
                peers = first_validator_data["peerIds"]
                throughputs = first_validator_data["throughputs"]
                layers = first_validator_data["layers"]
                signatures = [value.value["signature"] for value in data.value.values()]  # Skipping '0x'

                print("Peers:", peers)
                print("Throughputs:", throughputs)
                print("Layers:", layers)
                print("Signatures:", signatures)
                print("Addresses:", addresses)

                nonce = w3.eth.get_transaction_count(self.address)
                chain_id = w3.eth.chain_id

                # Correctly preparing the contract function call with parameters
                data = contract.encodeABI(fn_name='updateBalances', args=[peers, throughputs, layers, signatures, addresses])

                tx = {
                    'to': contract_address, 
                    'value': 0, 
                    'chainId': chain_id,  # Adjust according to your network
                    'maxFeePerGas': 2000000000,
                    'maxPriorityFeePerGas': 1000000000,
                    'gas': 100000,
                    'nonce': nonce,
                    'data': data,
                    'from': self.address  # This line is not necessary for buildTransaction and can be omitted
                }

                signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)

                # Send transaction
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                # Wait for transaction receipt
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                logger.info(f"Transaction successful with hash: {receipt.transactionHash.hex()}")

                logger.info("peerz have reached consensus")

            except Exception:
                logger.error("Failed to update signature", exc_info=True)

            time.sleep(max(self.check_period, 0))