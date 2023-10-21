from functools import partial

import json
from ecdsa import SigningKey, SECP256k1
from web3 import Web3
from eth_account.messages import encode_defunct, _hash_eip191_message
import binascii
from hivemind import DHT, get_dht_time, get_logger
import time
import threading
import hashlib
from typing import List

from peerz.validator.state_updater import StateUpdaterThread

logger = get_logger(__name__)

def prepare_data_for_signing(state):
    peerIds = [Web3.solidity_keccak(['string'], [str(item['peer_id'])]).hex() for item in state]
    throughputs = [item['throughput'] for item in state]
    layers = [item['layers'] for item in state]
    return peerIds, throughputs, layers

def sign_data(private_key, peerIds, throughputs, layers):
    w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545/'))
    private_key_bytes = binascii.unhexlify(private_key[2:])
    
    # Hash the encoded data using keccak
    hashed_data = Web3.solidity_keccak(['bytes32[]', 'uint256[]', 'uint256[]'], [peerIds, throughputs, layers])
    message = encode_defunct(hexstr=hashed_data.hex())

    # Sign the hash of the encoded data
    signed_message = w3.eth.account.sign_message(message, private_key=private_key_bytes)
    return signed_message.signature.hex()


class Validator:
    def __init__(
        self,
        *,
        initial_peers: List[str],
        address: str,
        private_key: str,
        check_period: float = 20,
    ):
        logger.info("Connecting to DHT")
        self.dht = DHT(initial_peers, start=True)
        self.address = address
        self.private_key=private_key
        self.check_period = check_period
        self.updater = None
        self.initial_peers = initial_peers
        self.stop = threading.Event()
    def run(self):
        logger.info("Starting updater")
        self.updater = StateUpdaterThread(self.dht, daemon=True, initial_peers=self.initial_peers)
        self.updater.start()
        self.updater.ready.wait()
        while True:
            try:
                peerIds, throughputs, layers = prepare_data_for_signing(self.updater.state)
                signature_hex = sign_data(self.private_key, peerIds, throughputs, layers)
                print(peerIds, throughputs, layers, signature_hex)

                self.dht.store(
                    key="_peerz.validators",
                    subkey=self.address,
                    value=dict(peerIds=peerIds, throughputs=throughputs, layers=layers, signature=signature_hex),
                    expiration_time=get_dht_time() + 3600,
                )
            except Exception:
                logger.error("Failed to update signature", exc_info=True)

            time.sleep(max(self.check_period, 0))


