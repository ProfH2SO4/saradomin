from saradomin import log

import time
import functools
import psutil
import os


def profiler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Memory and CPU usage before function execution
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024**2  # Convert to MB
        cpu_before = process.cpu_percent(interval=None)
        log.info(f"START: {func.__name__}")

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Memory and CPU usage after function execution
        mem_after = process.memory_info().rss / 1024**2  # Convert to MB
        cpu_after = process.cpu_percent(interval=None)

        log.debug(f"{func.__name__} execution time: {end_time - start_time:.4f} seconds")
        log.debug(f"{func.__name__} memory usage: {mem_after - mem_before:.4f} MB")
        log.debug(f"{func.__name__} CPU usage: {cpu_after - cpu_before:.4f} %")

        return result

    return wrapper
