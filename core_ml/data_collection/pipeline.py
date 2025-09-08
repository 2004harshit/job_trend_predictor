from data_collection.base import JobExtractor , StorageHandler
from typing import List , Dict
from config.logger import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class Pipeline:
    """
    A modular job scraping pipeline that runs multiple extractors
    and stores results using one or more storage handlers.
    """
    def __init__(self , extractors : List[JobExtractor],handler: StorageHandler , job_queue: List[str], filedirectory: Dict, max_pages: int , per_page_limit: int):
        self.extractors = extractors
        self.handlers = handler
        self.job_queue = job_queue
        self.filedirectory = filedirectory
        self.max_pages = max_pages
        self.per_page_limit = per_page_limit
    
    def run(self):
        logger.info("Job Scraping Started")
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            for job in self.job_queue:
                logger.info(f"Extractor={extractor_name} | Job={job} | Extraction started")
                try:
                    data = extractor.extract(job, self.max_pages, self.per_page_limit)
                    logger.info(f"Extractor={extractor_name} | Job={job} | Extracted {len(data)} records")
                except Exception as e:
                    logger.error(f"Extractor={extractor_name} failed for job={job}", exc_info=True)
                    continue
                
                for handler in self.handlers:
                    handler_name = handler.get_name()
                    filename = self.filedirectory[handler_name]
                    try:
                        handler.save(data, filename)
                        logger.info(f"Handler={handler_name} | Job={job} | Saved data to {filename}")
                    except Exception as e:
                        logger.error(f"Handler={handler_name} failed for job={job}", exc_info=True)
    
        logger.info("Pipeline executed successfully.")
