import docker
import sys
import signal

import src.constants as constants

from src.logger import logger
from datetime import datetime, timedelta
from src.nexus_api import NexusAPI
from src.utils import Utils
from src.event_parse import EventParse

class Node:
    def __init__(self, config) -> None:
        self.host_ip = config['host_ip']
        self.name = config['name']
        self.docker_client = docker.from_env()
        self.container = None

    def set_container(self, container):
        try:
            network_mode = container.attrs.get('HostConfig').get('NetworkMode')

            self.container = {
                'Host IP': self.host_ip,
                'Container ID': container.id,
                'Image Version': container.image.labels["org.opencontainers.image.version"],
                'Container Status': container.status,
                'Container Started At': Utils.normalize_date(container.attrs.get('State').get('StartedAt')),
                'Container IP': container.attrs.get('NetworkSettings').get('Networks')[network_mode].get('IPAddress')
            }
        except Exception as e:
            logger.error("Error setting container:", exc_info=e)

    def get_container(self):
        try:
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if 'subspace/node' in container.image.tags[0]:
                    self.set_container(container)
                    logger.info(f"Found Container with ID: {self.container['Container ID']}")

            if not self.container:
                logger.error('No matching containers found. Are you sure you have docker running?')
                sys.exit(1)

        except Exception as e:
            logger.error(f'Error getting container:', exc_info=e)
            sys.exit(1)

    def check_container_version(self):
        try:
            if self.container.get('Image Version') != constants.VERSIONS.get('Node'):
                logger.warn(f"Expected version {constants.VERSIONS['Image']} for container ID {self.container.get('Container ID')}. Hubble may not run as expected, consider updating your container.")
        
        except Exception as e:
            logger.warn(f'Error checking container version:', exc_info=e)

    def signal_handler(self, sig, frame) -> None:
        print('SIGINT Received, shutting down stream...')
        # Perform any cleanup actions here if needed
        sys.exit(0)

    def log_stream_monitor(self):
        logger.info('Starting Log Stream Monitor')
        container = self.docker_client.containers.get(self.container['Container ID'])

        if not container:
            logger.error('Unable to get container. Fatal')
            sys.exit(1)

        signal.signal(signal.SIGINT, self.signal_handler)

        while True:
            try:
                container.reload()
                self.set_container(container)

                if container.status != 'running':
                    logger.warn(f"Container must be running, current status: {container.status}")
                    continue

                start_datetime = Utils.get_prev_date(90, 'minutes')
                logger.info(f"Getting logs since {start_datetime}")

                generator = container.logs(since=start_datetime, stdout=True, stderr=True, stream=True)

                for log in generator:
                    parsed_log = Utils.parse_log(log.decode('utf-8').strip())
                    if not parsed_log:
                        logger.warn(f"Unable to parse log: ", log.decode('utf-8').strip())
                        continue

                    event = EventParse.check_log(parsed_log, self.name)
                    if not event:
                        continue

                    NexusAPI.create_event(event)

            except Exception as e:
                logger.error("Error in Log Stream Monitor:", exc_info=e)

    def start(self):
        logger.info(f"Starting log monitor for {self.container.get('Container ID')}")
        event = {
            'Event Type': 'Register Node',
            'Level': 'INFO',
            'Age': 0,
            'Datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Host Name': self.name,
            'Data': self.container
        }
        NexusAPI.register(event)
        self.log_stream_monitor()

    def init(self):
        self.get_container()
        self.check_container_version()
        self.start()