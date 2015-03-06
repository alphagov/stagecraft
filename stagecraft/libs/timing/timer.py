import time
import logging

logger = logging.getLogger(__name__)


def timer(start_message):
    logger.info(start_message)
    start = time.time()

    def log_timing(message):
        end = time.time()
        elapsed = end - start
        logger.info('{} took {}'.format(message, elapsed),
                    extra={'elapsed_time': elapsed})
    return log_timing
