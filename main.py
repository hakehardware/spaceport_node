import argparse

from src.logger import logger
from src.node import Node

def main():
    parser = argparse.ArgumentParser(description='SpacePort Node')

    parser.add_argument('-s', '--server', type=str, required=True, help='Server IP address')
    parser.add_argument('-n', '--nexus', type=str, required=True, help='Nexus URL')

    # Parse the arguments
    args = parser.parse_args()

    # Access the arguments
    host_ip = args.server
    nexus_url = args.nexus

    config = {
        'Host IP': host_ip,
        'Nexus URL': nexus_url
    }
        
    logger.info(f"Got Config: {config}")

    hubble = Node(config)
    hubble.init()

if __name__ == "__main__":
    main()