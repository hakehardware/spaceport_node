from datetime import datetime, timedelta
import re

class Utils:
    @staticmethod
    def normalize_date(date_str):
        # Truncate the fractional seconds to 6 digits
        truncated_date_str = date_str[:26] + 'Z'
        # Parse the input date string
        dt = datetime.strptime(truncated_date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        # Return the formatted date string
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def get_prev_date(time_delta, unit):
        unit = unit.lower()
        if unit not in ['seconds', 'minutes', 'hours']:
            raise ValueError("Invalid unit. Please choose 'seconds', 'minutes', or 'hours'.")

        if unit == 'seconds':
            delta = timedelta(seconds=time_delta)
        elif unit == 'minutes':
            delta = timedelta(minutes=time_delta)
        elif unit == 'hours':
            delta = timedelta(hours=time_delta)

        current_time = datetime.now()
        return current_time - delta
    
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