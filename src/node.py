import docker
import sys
import threading
import src.constants as constants
from src.container_monitor import ContainerMonitor
from src.stream_monitor import StreamMonitor
from src.logger import logger
from src.nexus_api import NexusAPI
from src.utils import Utils
from src.event_parse import EventParse
from datetime import datetime

class Node:
    def __init__(self, config) -> None:
        self.host_ip = config['Host IP']
        self.nexus_url = config['Nexus URL']
        self.docker_client = docker.from_env()
        self.container_id = None
        self.stop_event = threading.Event()
        self.container = {
            'Container ID': None
        }

    def get_container(self):
        try:
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if 'subspace/node' in container.image.tags[0]:
                    self.container_id = container.id
                    logger.info(f"Got Container with ID: {self.container_id}")

            if not self.container_id:
                logger.error('No matching containers found. Are you sure you have docker running?')
                sys.exit(1)

        except Exception as e:
            logger.error(f'Error getting container:', exc_info=e)
            sys.exit(1)
        
    def start_stream_monitor(self):
        logger.info("Starting Log Monitor")
        StreamMonitor.monitor_stream(self.container, self.docker_client, self.stop_event, self.nexus_url)

    def start_container_monitor(self):
        while not self.stop_event.is_set():
            self.stop_event.wait(10)
            self.container = ContainerMonitor.get_container_resources(self.container_id, self.docker_client, self.host_ip)
            ContainerMonitor.update_container_resources(False, self.container, self.nexus_url)

    def start_metrics_monitor(self):
        logger.info("Starting Metrics Monitor")
        pass

    # Init
    def init(self):
        try:
            self.get_container()
            logger.info("Getting initial container resources")
            self.container = ContainerMonitor.get_container_resources(self.container_id, self.docker_client, self.host_ip)
            logger.info("Registering container")
            ContainerMonitor.update_container_resources(True, self.container, self.nexus_url)

            log_monitor_thread = threading.Thread(target=self.start_stream_monitor)
            resource_monitor_thread = threading.Thread(target=self.start_container_monitor)
            metrics_monitor_thread = threading.Thread(target=self.start_metrics_monitor)

            log_monitor_thread.start()
            resource_monitor_thread.start()
            metrics_monitor_thread.start()

            log_monitor_thread.join()
            resource_monitor_thread.join()
            metrics_monitor_thread.join()

        except KeyboardInterrupt:
            print("Stop signal received. Gracefully shutting down monitors.")
            self.stop_event.set()  # Ensure the stop event is set