import torch

PUBLIC_INITIAL_PEERS = [
    # IPv4 DNS addresses
    "/ip4/127.0.0.1/tcp/58378/p2p/12D3KooWQrcDwFAhRwSDrZpuspKmu63iy5FzWEoEdM1gZdMdHzCd"
]

# The reachability API is currently used only when connecting to the public swarm
REACHABILITY_API_URL = "http://localhost:5000"

DTYPE_MAP = dict(bfloat16=torch.bfloat16, float16=torch.float16, float32=torch.float32, auto="auto")

UPDATE_PERIOD = 20