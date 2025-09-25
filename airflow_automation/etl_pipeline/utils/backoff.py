# utils/backoff.py
import random
import time
import logging

logger = logging.getLogger(__name__)

def exponential_backoff(retry_fn, max_retries=5, base_delay=2, max_delay=60):
    """
    Retry a function with exponential backoff and jitter.
    retry_fn: function with no arguments (wrap request or driver.get call)
    """
    attempt = 0
    while attempt < max_retries:
        try:
            return retry_fn()
        except Exception as e:
            wait_time = min(max_delay, base_delay * (2 ** attempt))
            jitter = random.uniform(0, 1)
            total_wait = wait_time + jitter
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {total_wait:.2f}s")
            time.sleep(total_wait)
            attempt += 1
    logger.error(f"Max retries ({max_retries}) reached. Giving up.")
    raise RuntimeError("Exponential backoff failed after max retries.")
