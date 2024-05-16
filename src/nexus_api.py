from src.logger import logger

class NexusAPI:
    def register(event):
        logger.info(f"Nexus API: Registering - {event}")

    def create_event(event):
        logger.info(f"Nexus API: Create Event - {event}")