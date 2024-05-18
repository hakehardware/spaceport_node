import argparse
import yaml
import os
import sys

from src.logger import logger
from src.node import Node

def read_yaml_file(file_path):
    logger.info(f'Opening config from {file_path}')
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            return None

def validate_config(config):
    missing = []
    errors = []

    if 'host_ip' not in config:
        missing.append('host IP')

    if 'name' not in config:
        missing.append('name')

    if len(missing) != 0:
        logger.error(f"You have missing fields in your config: {', '.join(missing)}")

    if len(errors) != 0:
        for error in errors:
            logger.error(error)

    if len(errors) != 0 or len(missing) != 0:
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Load YAML configuration.')

    parser.add_argument(
        'config', 
        metavar='config.yml', 
        type=str,
        help='path to the YAML configuration file'
    )

    args = parser.parse_args()

    config = read_yaml_file(args.config)

    if not config:
        logger.error(f'Error loading config from {args.config}. Are you sure you put in the right location?')
        sys.exit(1)
        
    logger.info(f"Got Config: {config}")

    validate_config(config)

    hubble = Node(config)
    hubble.init()

if __name__ == "__main__":
    main()