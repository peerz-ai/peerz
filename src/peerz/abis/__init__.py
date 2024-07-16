import os
import json

script_dir = os.path.dirname(__file__)
abi_file_path = os.path.join(script_dir, '../abis/consensus.json')

consensus_abi = None

with open(abi_file_path, 'r') as abi_file:
    consensus_abi = json.load(abi_file)