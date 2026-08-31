import time
from functools import wraps


def timer(func):
    """Estimate function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        wrapper.elapsed_time = end - start
        return result

    wrapper.elapsed_time = 0
    return wrapper
