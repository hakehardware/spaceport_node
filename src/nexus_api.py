from src.logger import logger
from datetime import datetime
import requests
import sys
import json

class NexusAPI:
    def update_server(base_url, event):
        logger.info(f"Nexus API: Updating Server")
        local_url = f"{base_url}/insert/server"
        response = requests.post(local_url, json=event)
        logger.info(response.json())


    def update_container(base_url, event):
        logger.info(f"Nexus API: Updating Container")
        local_url = f"{base_url}/insert/container"
        response = requests.post(local_url, json=event)
        logger.info(response.json())


    def create_event(base_url, event):
        logger.info(f"Nexus API: Updating Container")
        local_url = f"{base_url}/insert/event"
        response = requests.post(local_url, json=event)
        if response.status_code == 201: return True
        else: return False
    
    def insert_consensus(base_url, event):
        # logger.info(f"Nexus API: Inserting Consensus")
        pass

    def insert_claim(base_url, event):
        pass
        # logger.info(f"Nexus API: Inserting Claim")