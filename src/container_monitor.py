from src.logger import logger
from src.utils import Utils
from datetime import datetime, timezone
from src.nexus_api import NexusAPI

class ContainerMonitor:
    @staticmethod
    def get_container_resources(container_id, docker_client, server_ip):
        try:
            server_info = docker_client.info()
            container = docker_client.containers.get(container_id)

            network_mode = container.attrs.get('HostConfig').get('NetworkMode')

            stats = container.stats(stream=False)
            memory_usage = stats['memory_stats']['stats']['active_anon'] + stats['memory_stats']['stats']['active_file']
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
            cpu_usage_percentage = round((cpu_delta / system_cpu_delta) * 100, 2)

            resources = {
                'Server Name': server_info['Name'],
                'Server OS': server_info['OperatingSystem'],
                'Server CPUs': server_info['NCPU'],
                'Server Memory': round(server_info['MemTotal'] / (1024 ** 3), 2),
                'Server IP': server_ip,
                'Container ID': container_id,
                'Container Name': container.name,
                'Container Image': container.image.labels["org.opencontainers.image.version"],
                'Container Status': container.status,
                'Container Started At': Utils.normalize_date(container.attrs.get('State').get('StartedAt')),
                'Container IP': container.attrs.get('NetworkSettings').get('Networks')[network_mode].get('IPAddress'),
                'Container Type': 'Node',
                'Container Memory Usage': memory_usage_gib,
                'Container Memory Limit': memory_limit_gib,
                'Container Memory Usage Percent': memory_usage_percentage,
                'Container CPU Usage Percent': cpu_usage_percentage,
                'Container Number of CPUs': online_cpus,
            }

            return resources

        except Exception as e:
            logger.error("Error updating node container resources:", exc_info=e)

    @staticmethod
    def update_container_resources(is_register, container, nexus_url):
        event = {
            'Event Name': 'Register Container' if is_register else 'Update Container',
            'Event Type': 'Container',
            'Event Source': container['Container Name'],
            'Event Level': 'INFO',
            'Event Datetime': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
            'Event Data': container
        }

        # NexusAPI.update_container(nexus_url, event)
        NexusAPI.create_event(nexus_url, event)