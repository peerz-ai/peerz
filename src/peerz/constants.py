import torch

PUBLIC_INITIAL_PEERS = [
    # IPv4 DNS addresses
    "/ip4/127.0.0.1/tcp/55823/p2p/12D3KooWAHR4RM4GSq5zG2UvXHS5nwbjptfFS7Vz77MNrkC8VxFj"
]

# The reachability API is currently used only when connecting to the public swarm
REACHABILITY_API_URL = "http://localhost:5000"

DTYPE_MAP = dict(bfloat16=torch.bfloat16, float16=torch.float16, float32=torch.float32, auto="auto")

UPDATE_PERIOD = 20

RPC_URL = "https://rpc.ankr.com/eth_holesky"

PROTOCOL_ADDRESS = "0xAb4554595737f9A5aB8AF2dAcD867cBaa1FCe36F"