import re
import time

from src.logger import logger
DISPLAY = ['Claimed']

class EventParse:
    @staticmethod
    def check_log(log, name):
        try:
            if 'Idle' in log['Event Data']:
                # pattern = re.compile(
                #     r'Idle \((?P<peers>\d+) peers\), best: #(?P<best>\d+).*finalized #(?P<finalized>\d+).*⬇ (?P<down_speed>\d+(?:\.\d+)?)(?P<down_unit>kiB|MiB)?/s ⬆ (?P<up_speed>\d+(?:\.\d+)?)(?P<up_unit>kiB|MiB)?/s'
                # )
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
                
                event = {
                    'Event Name': 'Idle',
                    'Event Type': 'Node',
                    'Event Level': log["Event Level"],
                    'Event Datetime': log["Event Datetime"],
                    'Event Source': name,
                    'Event Data': {
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
                }
                if event['Event Name'] in DISPLAY:
                    logger.info(event)
                return event
                
            if 'Preparing' in log['Event Data']:
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

                event = {
                    'Event Name': 'Preparing',
                    'Event Type': 'Node',
                    'Event Level': log["Event Level"],
                    'Event Datetime': log["Event Datetime"],
                    'Event Source': name,
                    'Event Data': {
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
                }
                if event['Event Name'] in DISPLAY:
                    logger.info(event)
                return event

            if 'Syncing' in log['Event Data']:
                #logger.info(log['Event Data'])

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

                event = {
                    'Event Name': 'Syncing',
                    'Event Type': 'Node',
                    'Event Level': log["Event Level"],
                    'Event Datetime': log["Event Datetime"],
                    'Event Source': name,
                    'Event Data': {
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
                }
                if event['Event Name'] in DISPLAY:
                    logger.info(event)
                return event

            if 'Pending' in log['Event Data']:
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

                event = {
                    'Event Name': 'Pending',
                    'Event Type': 'Node',
                    'Event Level': log["Event Level"],
                    'Event Datetime': log["Event Datetime"],
                    'Event Source': name,
                    'Event Data': {
                        'Status': 'Pending',
                        'Peers': int(peers),
                        'Best': int(best),
                        'Finalized': int(finalized),
                        'Down Speed': float(down_speed),
                        'Up Speed': float(up_speed),
                        'Down Unit': down_unit,
                        'Up Unit': up_unit
                    }
                }
                if event['Event Name'] in DISPLAY:
                    logger.info(event)

                return event
            
            if 'Claimed' in log['Event Data'] :
                pattern = r'slot=(\d+)'
                match = re.search(pattern, log['Event Data'])

                if not match:
                    logger.error(f"No match for: {log['Event Data']}")
                    time.sleep(5)
                    return None
                
                slot = int(match.group(1))
                event = {
                    'Event Name': 'Claim',
                    'Event Type': 'Node',
                    'Event Level': log["Event Level"],
                    'Event Datetime': log["Event Datetime"],
                    'Event Source': name,
                    'Event Data': {
                        'Slot': slot,
                        'Claim Type': "Vote" if "vote" in log['Event Data'] else "Block"
                    }
                }

                if event['Event Name'] in DISPLAY:
                    logger.info(event)

                return event
                
            return None

        except Exception as e:
            logger.error(f"Error in Event Parse {log}:", exc_info=e)

