import re

from src.logger import logger

class EventParse:
    @staticmethod
    def check_log(log, name):
        if 'Idle' in log['Event Data']:
            pattern = r'Idle \((\d+) peers\), best: #(\d+).*finalized #(\d+).*⬇ (\d+(?:\.\d+)?)(?:kiB|MiB)?/s ⬆ (\d+(?:\.\d+)?)(?:kiB|MiB)?/s'
            match = re.search(pattern, log['Event Data'])

            if match:

                peers, best, finalized, down_speed, up_speed = match.groups()
                
                event = {
                    'Event Name': 'Idle Node',
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
                        'Up Speed': float(up_speed)
                    }
                }

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
                    'Status': 'Syncing',
                    'Peers': int(peers),
                    'Best': int(best),
                    'Target': int(target),
                    'Finalized': int(finalized),
                    'BPS': float(bps) if bps else None,
                    'Down Speed': float(down),
                    'Up Speed': float(up)
                }
            }

            return event

        if 'Claimed' in log['Event Data'] :
            pattern = r'slot=(\d+)'
            match = re.search(pattern, log['Event Data'])

            if match:
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
                return event
            
        return None



