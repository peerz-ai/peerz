import argparse
import configargparse
import sys
from peerz.cli.run_dht import args as dht_args, main as run_dht
from peerz.cli.run_server import args as server_args, main as run_server

def main():
    parser = configargparse.ArgParser(default_config_files=["config.yml"],
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    type_parser = parser.add_subparsers(dest='type')

    dht_parser = type_parser.add_parser('dht')
    server_parser = type_parser.add_parser('server')
    validator_parser = type_parser.add_parser('validator')

    dht_args(dht_parser)
    server_args(server_parser)

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
                print("validator:", args.type)

