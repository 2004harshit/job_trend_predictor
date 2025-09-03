from data_collection.base import JobExtractor , StorageHandler
from typing import List , Dict

class Pipeline:
    """
    A modular job scraping pipeline that runs multiple extractors
    and stores results using one or more storage handlers.
    """
    def __init__(self , extractors : List[JobExtractor],handler: StorageHandler , job_queue: List[str], filedirectory: Dict, max_pages: int , per_page_limit: int):
        self.extractors = extractors
        self.handler = handler
        self.job_queue = job_queue
        self.filedirectory = filedirectory
        self.max_pages = max_pages
        self.per_page_limit = per_page_limit
    
    def run(self):
        for extractor in self.extractors:
            for job in self. job_queue:
                data = extractor.extract(job , self.max_pages , self.per_page_limit)
                for handler in self.handlers:
                    filename = self.filedirectory[handler.get_name()]
                    handler.save(data, filename)

