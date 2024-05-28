from src.logger import logger
import sys
from datetime import datetime, timezone
from src.utils import Utils
import re
from src.nexus_api import NexusAPI
import time

class StreamMonitor:
    @staticmethod
    def parse_log(log_str):
        log_pattern = re.compile(
            r'(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(?P<level>\w+)\s+(?P<data>.+)'
        )
        match = log_pattern.match(log_str)
        
        if match:
            return {
                'Event Datetime': Utils.normalize_date(match.group("datetime")),
                'Event Level': match.group("level"),
                'Event Data': match.group("data")
            }
        
        else:
            return None
        
    @staticmethod
    def parse_event(log, name):
        try:

            event = {
                'Event Name': None,
                'Event Type': None,
                'Event Level': log["Event Level"],
                'Event Datetime': log["Event Datetime"],
                'Event Source': name,
                'Event Data': None
            }

            if 'Idle' in log['Event Data']:
                event['Event Name'] = 'Idle'
                event['Event Type'] = 'Node'
                pattern = re.compile(
                    r'Idle \((?P<peers>\d+) peers\), best: #(?P<best>\d+).*finalized #(?P<finalized>\d+).*⬇ (?P<down_speed>\d+(?:\.\d+)?)(?P<down_unit>\s?[kKMmGg]?[iI]?[bB]/s) ⬆ (?P<up_speed>\d+(?:\.\d+)?)(?P<up_unit>\s?[kKMmGg]?[iI]?[bB]/s)'
                )
                match = pattern.search(log['Event Data'])

                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
                
                peers = match.group("peers")
                best = match.group("best")
                finalized = match.group("finalized")
                down_speed = match.group("down_speed")
                down_unit = match.group("down_unit")
                up_speed = match.group("up_speed")
                up_unit = match.group("up_unit")

                event['Event Data'] = {
                    'Status': 'Idle',
                    'Peers': int(peers),
                    'Best': int(best),
                    'Target': None,
                    'Finalized': int(finalized),
                    'BPS': None,
                    'Down Speed': float(down_speed),
                    'Up Speed': float(up_speed),
                    'Down Unit': down_unit,
                    'Up Unit': up_unit
                }
            
            if 'Preparing' in log['Event Data']:
                event['Event Name'] = 'Preparing'
                event['Event Type'] = 'Node'

                pattern = re.compile(
                    r'(?:(?P<bps>\d+\.\d+)\s+bps,\s*)?'  # Optional bps
                    r'target=#(?P<target>\d+)\s+\((?P<peers>\d+)\s+peers\),\s+'  # target and peers
                    r'best:\s+#(?P<best>\d+)\s+\([^)]*\),\s+'  # best
                    r'finalized\s+#(?P<finalized>\d+)\s+\([^)]*\),\s+'  # finalized
                    r'⬇\s+(?P<down>\d+(?:\.\d+)?)(?P<down_unit>kiB|MiB)/s\s+'  # download speed and unit
                    r'⬆\s+(?P<up>\d+(?:\.\d+)?)(?P<up_unit>kiB|MiB)/s'  # upload speed and unit
                )
                match = pattern.search(log['Event Data'])


                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
                
                log_dict = match.groupdict()
                bps = log_dict["bps"] if log_dict["bps"] else None
                target = log_dict["target"]
                peers = log_dict["peers"]
                best = log_dict["best"]
                finalized = log_dict["finalized"]
                down = log_dict["down"]
                down_unit = log_dict["down_unit"]
                up = log_dict["up"]
                up_unit = log_dict["up_unit"]

                event['Event Data'] = {
                    'Status': 'Preparing',
                    'Peers': int(peers),
                    'Best': int(best),
                    'Target': int(target),
                    'Finalized': int(finalized),
                    'BPS': float(bps) if bps else None,
                    'Down Speed': float(down),
                    'Up Speed': float(up),
                    'Down Unit': down_unit,
                    'Up Unit': up_unit
                }

            if 'Syncing' in log['Event Data']:
                event['Event Name'] = 'Syncing'
                event['Event Type'] = 'Node'

                pattern = re.compile(
                    r'Consensus: substrate: ⚙️  Syncing(?:\s+(?P<bps>\d+\.\d+) bps)?, target=#(?P<target>\d+) \((?P<peers>\d+) peers\), best: #(?P<best>\d+) \([^\)]+\), finalized #(?P<finalized>\d+) \([^\)]+\), ⬇ (?P<down_speed>\d+\.\d+)(?P<down_unit>[kKmMgG][iI]?[bB]/s) ⬆ (?P<up_speed>\d+\.\d+)(?P<up_unit>[kKmMgG][iI]?[bB]/s)'
                )

                # Match the pattern
                match = pattern.search(log['Event Data'])

                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
            
                bps = match.group("bps")
                target = match.group("target")
                peers = match.group("peers")
                best = match.group("best")
                finalized = match.group("finalized")
                down_speed = match.group("down_speed")
                down_unit = match.group("down_unit")
                up_speed = match.group("up_speed")
                up_unit = match.group("up_unit")

                event['Event Data'] = {
                    'Status': 'Syncing',
                    'Peers': int(peers),
                    'Best': int(best),
                    'Target': int(target),
                    'Finalized': int(finalized),
                    'BPS': float(bps) if bps else None,
                    'Down Speed': float(down_speed),
                    'Up Speed': float(up_speed),
                    'Down Unit': down_unit,
                    'Up Unit': up_unit
                }

            if 'Pending' in log['Event Data']:
                event['Event Name'] = 'Pending'
                event['Event Type'] = 'Node'

                pattern = re.compile(
                    r'Consensus: substrate: ⏳ Pending \((?P<peers>\d+) peers\), best: #(?P<best>\d+) \([^\)]+\), finalized #(?P<finalized>\d+) \([^\)]+\), ⬇ (?P<down_speed>\d+\.\d+)(?P<down_unit>[kKmMgG][iI]?[bB])/s ⬆ (?P<up_speed>\d+\.\d+)(?P<up_unit>[kKmMgG][iI]?[bB])/s'
                )

                # Match the pattern
                match = pattern.search(log['Event Data'])

                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
                
                peers = match.group("peers")
                best = match.group("best")
                finalized = match.group("finalized")
                down_speed = match.group("down_speed")
                down_unit = match.group("down_unit")
                up_speed = match.group("up_speed")
                up_unit = match.group("up_unit")

                event['Event Data'] = {
                    'Status': 'Pending',
                    'Peers': int(peers),
                    'Best': int(best),
                    'Target': None,
                    'Finalized': int(finalized),
                    'BPS': None,
                    'Down Speed': float(down_speed),
                    'Up Speed': float(up_speed),
                    'Down Unit': down_unit,
                    'Up Unit': up_unit
                }

            if 'Claimed' in log['Event Data']:
                event['Event Name'] = 'Claim'
                event['Event Type'] = 'Node'

                pattern = r'slot=(\d+)'
                match = re.search(pattern, log['Event Data'])

                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
                
                slot = int(match.group(1))

                event['Event Data'] = {
                    'Slot': slot,
                    'Claim Type': "Vote" if "vote" in log['Event Data'] else "Block"
                }

            if not event['Event Name']: return None
            else: return event

        except Exception as e:
            logger.error(f"Error in parse_event {log}:", exc_info=e)

    @staticmethod
    def handle_event(event):
        logger.info('Event Handled')
        # try:
        #     if event['Event Name'] in ['Idle', 'Preparing', 'Syncing']:
        #         NexusAPI.insert_consensus(self.nexus_url, event)
            
        #     if event['Event Name'] == 'Claim':
        #         NexusAPI.insert_claim(self.nexus_url, event)
            
        # except Exception as e:
        #     logger.error("Error handling event:", exc_info=e)

    @staticmethod
    def monitor_stream(container_data, docker_client, stop_event, nexus_url):
        container = docker_client.containers.get(container_data['Container ID'])

        if not container:
            logger.error('Unable to get container. Fatal')
            sys.exit(1)

        while not stop_event.is_set():
            try:
                container.reload()
                if container.status != 'running':
                    logger.warn(f"Container must be running, current status: {container.status}")
                    stop_event.wait(30)
                    continue

                response = NexusAPI.get_latest_events(nexus_url, container_data['Container Name'])
                if len(response.get('data')) > 0:
                    logger.info(f"Getting Logs Since: {response.get('data')[0].get('event_datetime')}")
                    start = datetime.strptime(response.get('data')[0].get('event_datetime'), "%Y-%m-%d %H:%M:%S")
                else: 
                    start = datetime.min.replace(tzinfo=timezone.utc)

                generator = container.logs(since=start, stdout=True, stderr=True, stream=True)
                for log in generator:
                    try:
                        if stop_event.is_set():
                            break

                        parsed_log = StreamMonitor.parse_log(log.decode('utf-8').strip())
                        if not parsed_log:
                            # logger.warn(f"Unable to parse log: {log}")
                            continue

                        event = StreamMonitor.parse_event(parsed_log, container_data['Container Name'])
                        if not event:
                            continue

                        created = NexusAPI.create_event(nexus_url, event)

                        if not created:
                            continue
                        
                        StreamMonitor.handle_event(event)

                    except Exception as e:
                        logger.error("Error in generator:", exc_info=e)

            except Exception as e:
                logger.error("Error in monitor_stream:", exc_info=e)