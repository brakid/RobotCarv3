from functools import wraps
import time
import logging

def timer(func):
    logger = logging.getLogger('Timer')
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info('Latency: %.6f sec', end - start)
        return result
    return wrapper