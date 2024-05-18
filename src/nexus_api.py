from src.logger import logger
from datetime import datetime
import requests
base_url = 'http://192.168.69.101:5000/hello'

class NexusAPI:
    def update_node(event, is_register):
        logger.info(f"Nexus API: Updating Node")
        # requests.get(base_url)


    def update_server(event, is_register):

        logger.info(f"Nexus API: Updating Server")
        # requests.get(base_url)

    def create_event(event):
        logger.info(f"Nexus API: Creating Event")
        return True
    
    def insert_consensus(event):
        logger.info(f"Nexus API: Inserting Consensus")

    def insert_claim(event):
        logger.info(f"Nexus API: Inserting Claim")