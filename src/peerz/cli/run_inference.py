"""
A copy of run_dht.py from hivemind with the ReachabilityProtocol added:
https://github.com/learning-at-home/hivemind/blob/master/hivemind/hivemind_cli/run_dht.py

This script may be used for launching lightweight CPU machines serving as bootstrap nodes to a Peerz swarm.

This may be eventually merged to the hivemind upstream.
"""

import argparse
import time
from secrets import token_hex

from peerz.inference.inference import Inference


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "--initial_peers",
        nargs="*",
        help="Multiaddrs of the peers that will welcome you into the existing DHT. "
        "Example: /ip4/203.0.113.1/tcp/31337/p2p/XXXX /ip4/203.0.113.2/tcp/7777/p2p/YYYY",
    )
    parser.add_argument(
        "--question",
        help="question for inference",
    )

    args = parser.parse_args()

    inference = Inference(
        question=args.question
    )
    inference.run()


if __name__ == "__main__":
    main()
