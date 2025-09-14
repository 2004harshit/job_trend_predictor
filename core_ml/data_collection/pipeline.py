from core_ml.data_collection.base import JobExtractor , StorageHandler
from typing import List , Dict
from core_ml.configuration.logger import setup_logging
import logging

setup_logging()
logger = logging.getLogger("pipeline")

class Pipeline:
    """
    A modular job scraping pipeline that runs multiple extractors
    and stores results using one or more storage handlers.
    """
    def __init__(self , extractors : List[JobExtractor],handler: StorageHandler , job: str, filedirectory: Dict):
        self.extractors = extractors
        self.handlers = handler
        self.job = job
        self.filedirectory = filedirectory
    
    def run(self):
        logger.info("Job Scraping Started")
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            
            logger.info(f"Extractor={extractor_name} | Job={self.job} | Extraction started")
            try:
                data = extractor.extract(self.job)
                logger.info(f"Extractor={extractor_name} | Job={self.job} | Extracted {len(data)} records")
            except Exception as e:
                logger.error(f"Extractor={extractor_name} failed for job={self.job}", exc_info=True)
                continue
            
            for handler in self.handlers:
                handler_name = handler.get_name()
                filename = self.filedirectory[handler_name]
                try:
                    handler.save(data, filename)
                    logger.info(f"Handler={handler_name} | Job={self.job} | Saved data to {filename}")
                except Exception as e:
                    logger.error(f"Handler={handler_name} failed for job={self.job}", exc_info=True)
    
        logger.info("Pipeline executed successfully.")
