import docker
import sys
import threading
import src.constants as constants
 

from src.logger import logger
from src.nexus_api import NexusAPI
from src.utils import Utils
from src.event_parse import EventParse
from datetime import datetime

class Node:
    def __init__(self, config) -> None:
        self.host_ip = config['Host IP']
        self.docker_client = docker.from_env()
        self.container_id = None
        self.stop_event = threading.Event()
        self.nexus_url = config['Nexus URL']
        self.server = {}
        self.container = {}

    def get_node_container(self):
        try:
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if 'subspace/node' in container.image.tags[0]:
                    self.container_id = container.id
                    self.check_container_version(container.image.labels["org.opencontainers.image.version"])

                    logger.info(f"Got Container with ID: {self.container_id}")

            if not self.container_id:
                logger.error('No matching containers found. Are you sure you have docker running?')
                sys.exit(1)

        except Exception as e:
            logger.error(f'Error getting container:', exc_info=e)
            sys.exit(1)

    def check_container_version(self, container_image_version):
        try:
            if container_image_version != constants.VERSIONS.get('Image'):
                logger.warn(f"Expected version {constants.VERSIONS.get('Image')} for container ID {self.container_id}. Hubble may not run as expected, consider updating your container.")
        
        except Exception as e:
            logger.warn(f'Error checking container version:', exc_info=e)

    def signal_handler(self, sig, frame) -> None:
        print('SIGINT Received, shutting down stream...')
        self.stop_event.set()  # Signal the threads to stop

    # Resource Monitor
    def update_container(self, is_register):
        try:
            container = self.docker_client.containers.get(self.container_id)
            
            network_mode = container.attrs.get('HostConfig').get('NetworkMode')
            self.container['Container ID'] = container.id
            self.container['Container Name'] = container.name
            self.container['Server Name'] = self.server['Server Name']
            self.container['Container Image Version'] = container.image.labels["org.opencontainers.image.version"]
            self.container['Container Status'] = container.status
            self.container['Container Started At'] = Utils.normalize_date(container.attrs.get('State').get('StartedAt'))
            self.container['Container IP'] = container.attrs.get('NetworkSettings').get('Networks')[network_mode].get('IPAddress')
            self.container['Container Type'] = 'Node'


            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats']['usage']
            memory_limit = stats['memory_stats']['limit']
            total_usage = stats['cpu_stats']['cpu_usage']['total_usage']
            system_cpu_usage = stats['cpu_stats']['system_cpu_usage']
            online_cpus = stats['cpu_stats']['online_cpus']

            # Convert memory usage and limit to GiB
            memory_usage_gib = round(memory_usage / (1024 ** 3), 2)
            memory_limit_gib = round(memory_limit / (1024 ** 3), 2)

            # Calculate memory usage percentage
            memory_usage_percentage = round((memory_usage / memory_limit) * 100, 2)

            # Calculate CPU usage percentage
            cpu_delta = total_usage - stats['precpu_stats']['cpu_usage']['total_usage']
            system_cpu_delta = system_cpu_usage - stats['precpu_stats']['system_cpu_usage']
            cpu_usage_percentage = round((cpu_delta / system_cpu_delta) * online_cpus * 100, 2)

            self.container['Container Memory Usage'] = memory_usage_gib
            self.container['Container Memory Limit'] = memory_limit_gib
            self.container['Container Memory Usage Percent'] = memory_usage_percentage
            self.container['Container CPU Usage Percent'] = cpu_usage_percentage
            self.container['Container Number of CPUs'] = online_cpus

            event = {
                'Event Name': 'Register Container' if is_register else 'Update Container',
                'Event Type': 'Container',
                'Event Source': self.server['Server Name'],
                'Event Level': 'INFO',
                'Event Datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Event Data': self.container
            }

            NexusAPI.update_container(self.nexus_url, event)
            NexusAPI.create_event(self.nexus_url, event)

        except Exception as e:
            logger.error("Error updating node container resources:", exc_info=e)

    def update_server(self, is_register):
        try:

            server_info = self.docker_client.info()
            self.server['Server Name'] = server_info['Name']
            self.server['Server OS'] = server_info['OperatingSystem']
            self.server['Server CPUs'] = server_info['NCPU']
            self.server['Server Memory'] = round(server_info['MemTotal'] / (1024 ** 3), 2)
            self.server['Server IP'] = self.host_ip

            event = {
                'Event Name': 'Register Server' if is_register else 'Update Server',
                'Event Type': 'Server',
                'Event Source': self.server['Server Name'] ,
                'Event Level': 'INFO',
                'Event Datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Event Data': self.server
            }

            NexusAPI.update_server(self.nexus_url, event)
            NexusAPI.create_event(self.nexus_url, event)

        except Exception as e:
            logger.error("Error updating server resources:", exc_info=e)


    # Log Monitor
    def log_stream_monitor(self):
        logger.info('Starting Log Stream Monitor')
        container = self.docker_client.containers.get(self.container_id)

        if not container:
            logger.error('Unable to get container. Fatal')
            sys.exit(1)

        while not self.stop_event.is_set():
            try:
                container.reload()

                if container.status != 'running':
                    logger.warn(f"Container must be running, current status: {container.status}")
                    continue

                response = NexusAPI.get_events(self.nexus_url, self.container['Container Name'])
                if len(response.get('data')) > 0:
                    logger.info(response.get('data')[0].get('event_datetime'))
                    start = datetime.strptime(response.get('data')[0].get('event_datetime'), "%Y-%m-%d %H:%M:%S")
                else: 
                    start = datetime.min

                logger.info(f"Getting logs since {start}")

                generator = container.logs(since=start, stdout=True, stderr=True, stream=True)

                for log in generator:
                    try:
                        if self.stop_event.is_set():
                            break

                        parsed_log = Utils.parse_log(log.decode('utf-8').strip())
                        if not parsed_log:
                            logger.warn(f"Unable to parse log: {log}")
                            continue
                        
                        event = EventParse.check_log(parsed_log, self.container['Container Name'])
                        if not event:
                            continue
                            
                        created = NexusAPI.create_event(self.nexus_url, event)
                        
                        if not created:
                            continue
                        
                        logger.info(created)

                        self.handle_event(event)
                    except Exception as e:
                        logger.error("Error in Generator For Loop:", exc_info=e)

            except Exception as e:
                logger.error("Error in Log Stream Monitor:", exc_info=e)

    def handle_event(self, event):
        try:
            if event['Event Name'] in ['Idle', 'Preparing', 'Syncing']:
                NexusAPI.insert_consensus(self.nexus_url, event)
            
            if event['Event Name'] == 'Claim':
                NexusAPI.insert_claim(self.nexus_url, event)
            
        except Exception as e:
            logger.error("Error handling event:", exc_info=e)
        


    # Threads
    def start_log_monitor(self):
        logger.info(f"Starting log monitor for {self.container_id}")
        self.log_stream_monitor()

    def start_resource_monitor(self):
        while not self.stop_event.is_set():
            self.update_server(False)
            self.update_container(False)
            self.stop_event.wait(10)

    # Init
    def init(self):
        try:
            self.get_node_container()
            self.update_server(True)
            self.update_container(True)

            log_monitor_thread = threading.Thread(target=self.start_log_monitor)
            resource_monitor_thread = threading.Thread(target=self.start_resource_monitor)

            log_monitor_thread.start()
            resource_monitor_thread.start()

            log_monitor_thread.join()
            resource_monitor_thread.join()

        except KeyboardInterrupt:
            print("Stop signal received. Gracefully shutting down monitors.")
            self.stop_event.set()  # Ensure the stop event is set