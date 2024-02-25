import argparse
import configargparse
import sys
from peerz.cli.run_dht import args as dht_args, main as run_dht
from peerz.cli.run_server import args as server_args, main as run_server
from peerz.cli.run_validator import args as validator_args, main as run_validator
from peerz.cli.run_sequencer import args as sequencer_args, main as run_sequencer
from peerz.cli.run_inference import args as inference_args, main as run_inference

def main():
    parser = configargparse.ArgParser(default_config_files=["config.yml"],
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    type_parser = parser.add_subparsers(dest='type', required=True, help='Type of peerz to run')

    dht_parser = type_parser.add_parser('dht', help='Bootstrap a DHT node')
    server_parser = type_parser.add_parser('server', help='Run a server')
    validator_parser = type_parser.add_parser('validator', help='Run a validator')
    sequencer_parser = type_parser.add_parser('sequencer', help='Run a sequencer')
    inference_parser = type_parser.add_parser('inference', help='Run inference')

    dht_args(dht_parser)
    server_args(server_parser)
    validator_args(validator_parser)
    sequencer_args(sequencer_parser)
    inference_args(inference_parser)

    if not sys.argv[1:] or sys.argv[1] in ('-h', '--help'):
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.type:
        match args.type:
            case "dht":
                run_dht(args)
            case "server":
                run_server(args)
            case "validator":
                run_validator(args)
            case "sequencer":
                run_sequencer(args)
            case "inference":
                run_inference(args)

