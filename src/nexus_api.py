from src.logger import logger
from datetime import datetime
import requests
import sys
import json
import time

class NexusAPI:
    def update_server(base_url, event):
        local_url = f"{base_url}/insert/server"
        response = NexusAPI.push(local_url, event)
        logger.info(response.json())


    def update_container(base_url, event):
        local_url = f"{base_url}/insert/container"
        response = NexusAPI.push(local_url, event)
        logger.info(response.json())


    def create_event(base_url, event):
        local_url = f"{base_url}/insert/event"
        response = NexusAPI.push(local_url, event)
        if response.status_code == 201: return response.json()
        else: return False

    def get_events(base_url, name):
        local_url = f"{base_url}/get/events?event_source={name}"
        response = requests.get(local_url)
        json_data = response.json()

        if response.status_code < 300:
            return json_data
        else:
            logger.error(f"Nexus API: Error getting events {json_data.get('message')}")
            return None
        
    def insert_consensus(base_url, event):
        local_url = f"{base_url}/insert/consensus"
        response = NexusAPI.push(local_url, event)
        logger.info(response.json())

    def insert_claim(base_url, event):
        local_url = f"{base_url}/insert/claim"
        response = NexusAPI.push(local_url, event)
        logger.info(response.json())


    def push(local_url, event):
        max_retries = 10
        retries = 0

        while True:
            try:
                response = requests.post(local_url, json=event)
                if response.status_code >= 300:
                    logger.error(response.json())
                    time.sleep(10)
                    
                return response

            except Exception as e:
                if retries == max_retries:
                    logger.error('Max retries reached. Exiting...')
                    sys.exit(1)
                retries+=1
                logger.error(f"Retries: {retries}, Max allowed: {max_retries}")
                time.sleep(1)
            
