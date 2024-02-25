import argparse

from peerz.inference.inference import Inference

def args(parser: argparse.ArgumentParser):
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

    return parser
    
def main(args: argparse.Namespace):
    inference = Inference(
        initial_peers=args.initial_peers,
        question=args.question
    )
    inference.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    args(parser)
    main(parser.parse_args())
