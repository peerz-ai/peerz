from peerz.constants import RPC_URL
from web3 import Web3
from eth_account.messages import encode_defunct
import binascii

def prepare_data_for_signing(state):
    peerIds = [Web3.solidity_keccak(['string'], [str(item['peer_id'])]).hex() for item in state]
    throughputs = [item['throughput'] for item in state]
    layers = [item['layers'] for item in state]
    total = sum([layers[i] * throughputs[i] for i in range(len(layers))])
    return peerIds, throughputs, layers, total

def sign_data(private_key, peerIds, throughputs, layers, total):
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    private_key_bytes = binascii.unhexlify(private_key)
    
    # Hash the encoded data using keccak
    hashed_data = Web3.solidity_keccak(['bytes32[]', 'uint256[]', 'uint256[]', 'uint256'], [peerIds, throughputs, layers, total])
    message = encode_defunct(hexstr=hashed_data.hex())

    # Sign the hash of the encoded data
    signed_message = w3.eth.account.sign_message(message, private_key=private_key_bytes)
    return signed_message.signature.hex()
