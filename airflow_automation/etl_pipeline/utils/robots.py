# utils/robots.py
import urllib.robotparser
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

def is_allowed(url: str, user_agent: str = "*") -> bool:
    """
    Check robots.txt to see if scraping is allowed for the given URL.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    rp = urllib.robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        allowed = rp.can_fetch(user_agent, url)
        if not allowed:
            logger.warning(f"Scraping disallowed by robots.txt for: {url}")
        return allowed
    except Exception as e:
        logger.error(f"Error fetching robots.txt from {robots_url}: {e}")
        # If robots.txt fails to load, default to safe side (disallow)
        return False
