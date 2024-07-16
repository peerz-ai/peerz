from peerz.constants import PROTOCOL_ADDRESS, RPC_URL
from peerz.abis import consensus_abi
from web3 import Web3

def contract():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    contract_address = PROTOCOL_ADDRESS
    return w3.eth.contract(address=contract_address, abi=consensus_abi)
