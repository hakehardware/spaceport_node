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
        self.host_ip = config['host_ip']
        self.name = config['name']
        self.docker_client = docker.from_env()
        self.container_id = None
        self.stop_event = threading.Event()
        self.nexus_url = 'http://192.168.69.101:5000'

    def get_node_container(self):
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

    def check_container_version(self):
        try:
            if self.node_container.get('Image Version') != constants.VERSIONS.get('Image'):
                logger.warn(f"Expected version {constants.VERSIONS.get('Image')} for container ID {self.node.get('Container ID')}. Hubble may not run as expected, consider updating your container.")
        
        except Exception as e:
            logger.warn(f'Error checking container version:', exc_info=e)

    def signal_handler(self, sig, frame) -> None:
        print('SIGINT Received, shutting down stream...')
        self.stop_event.set()  # Signal the threads to stop


    # Resource Monitor
    def update_node(self, is_register):
        try:
            node_container = {}
            container = self.docker_client.containers.get(self.container_id)
            network_mode = container.attrs.get('HostConfig').get('NetworkMode')
            node_container['Name'] = self.name
            node_container['Host IP'] = self.host_ip
            node_container['Container ID'] = container.id
            node_container['Image Version'] = container.image.labels["org.opencontainers.image.version"]
            node_container['Container Status'] = container.status
            node_container['Container Started At'] = Utils.normalize_date(container.attrs.get('State').get('StartedAt'))
            node_container['Container IP'] = container.attrs.get('NetworkSettings').get('Networks')[network_mode].get('IPAddress')



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

            node_container['Memory Usage'] = memory_usage_gib
            node_container['Memory Limit'] = memory_limit_gib
            node_container['Memory Usage Percent'] = memory_usage_percentage
            node_container['CPU Usage Percent'] = cpu_usage_percentage
            node_container['Number of CPUs'] = online_cpus

            event = {
                'Event Name': 'Register Node' if is_register else 'Update Node',
                'Event Type': 'Node',
                'Event Source': self.name,
                'Event Level': 'INFO',
                'Event Datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Event Data': node_container
            }

            NexusAPI.update_node(event, is_register)
            NexusAPI.create_event(event)

        except Exception as e:
            logger.error("Error updating node container resources:", exc_info=e)

    def update_server(self, is_register):
        try:
            server  = {}

            server_info = self.docker_client.info()
            server['Operating System'] = server_info['OperatingSystem']
            server['CPUs'] = server_info['NCPU']
            server['Memory'] = round(server_info['MemTotal'] / (1024 ** 3), 2)
            server['Name'] = server_info['Name']

            event = {
                'Event Name': 'Register Server' if is_register else 'Update Server',
                'Event Type': 'Server',
                'Event Source': self.name,
                'Event Level': 'INFO',
                'Event Datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Event Data': server
            }

            NexusAPI.update_server(event, is_register)
            NexusAPI.create_event(event)

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

                start_datetime = Utils.get_prev_date(5, 'minutes')
                logger.info(f"Getting logs since {start_datetime}")

                generator = container.logs(since=start_datetime, stdout=True, stderr=True, stream=True)

                for log in generator:
                    if self.stop_event.is_set():
                        break

                    parsed_log = Utils.parse_log(log.decode('utf-8').strip())
                    if not parsed_log:
                        logger.warn(f"Unable to parse log: ", log.decode('utf-8').strip())
                        continue

                    event = EventParse.check_log(parsed_log, self.name)
                    if not event:
                        continue

                    created = NexusAPI.create_event(event)
                    
                    if not created:
                        continue

                    self.handle_event(event)

            except Exception as e:
                logger.error("Error in Log Stream Monitor:", exc_info=e)

    def handle_event(self, event):
        try:
            if event['Event Name'] in ['Idle Node', 'Preparing']:
                response = NexusAPI.insert_consensus(event)
                return
            
            if event['Event Name'] == 'Claim':
                response = NexusAPI.insert_claim(event)
                return
            

        except Exception as e:
            logger.error("Error handling event:", exc_info=e)
        


    # Threads
    def start_log_monitor(self):
        logger.info(f"Starting log monitor for {self.container_id}")
        self.log_stream_monitor()

    def start_resource_monitor(self):
        register = True
        while not self.stop_event.is_set():
            self.update_node(register)
            self.update_server(register)
            register = False
            self.stop_event.wait(10)

    # Init
    def init(self):
        try:
            self.get_node_container()
            self.check_container_version()

            log_monitor_thread = threading.Thread(target=self.start_log_monitor)
            resource_monitor_thread = threading.Thread(target=self.start_resource_monitor)

            log_monitor_thread.start()
            resource_monitor_thread.start()

            log_monitor_thread.join()
            resource_monitor_thread.join()

        except KeyboardInterrupt:
            print("Stop signal received. Gracefully shutting down monitors.")
            self.stop_event.set()  # Ensure the stop event is set