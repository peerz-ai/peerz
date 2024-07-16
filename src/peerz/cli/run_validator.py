import argparse

from hivemind import DHT, get_logger
from peerz.validator.state_updater import StateUpdaterThread
from peerz.validator.validator import Validator

logger = get_logger(__name__)

def args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--initial_peers",
        nargs="*",
        help="Multiaddrs of the peers that will welcome you into the existing DHT. "
        "Example: /ip4/203.0.113.1/tcp/31337/p2p/XXXX /ip4/203.0.113.2/tcp/7777/p2p/YYYY",
    )
    parser.add_argument(
        "--address",
        help="address of the validator",
        required=True,
    )
    parser.add_argument(
        "--private_key",
        help="private key of the validator",
        required=True,
    )
    return parser
    
def main(args: argparse.Namespace):
    dht = DHT(args.initial_peers, start=True)
    updater = StateUpdaterThread(dht, daemon=True, initial_peers=args.initial_peers)
    updater.start()
    updater.ready.wait()
    validator = Validator(
        dht=dht,
        updater=updater,
        address=args.address,
        private_key=args.private_key,
    )
    validator.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args(parser)
    main(parser.parse_args())
