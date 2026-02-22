"""
Optimized Job Scraping Pipeline
Handles multiple extractors, storage handlers, and job queues efficiently.
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime

from src.storage.csv_storage_handler import CSVStorageHandler
from src.scrapers.naukri_general_job_scraper import GeneralJobScraper
from src.scrapers.base_scraper import JobExtractor
from src.storage.base_storage_handler import StorageHandler

from src.utils.logger import get_logger  

# Initialize logger
logger = get_logger(__name__)

class NaukriGeneralJobDataExtractionPipeline():
    """
    A modular job scraping pipeline that runs multiple extractors
    and stores results using one or more storage handlers.
    """
    def __init__(self , extractors : List[JobExtractor],handlers: List[StorageHandler] , jobs: List[str], filedirectory: Dict):

        """
        Initialize pipeline with extractors, handlers, and job list.
        
        Args:
            extractors: List of JobExtractor instances (e.g., NaukriExtractor, LinkedInExtractor)
            handlers: List of StorageHandler instances (e.g., CSVHandler, JSONHandler)
            jobs: List of job titles to scrape (e.g., ['Python Developer', 'Data Scientist'])
            filedirectory: Mapping of handler names to file paths

        """
        self.extractors = extractors
        self.handlers = handlers
        self.jobs = jobs
        self.filedirectory = filedirectory

    
    def _validate_configuration(self):
        """
        Validate pipeline configuration before execution
        """
        if not self.extractors:
            raise ValueError("At least one extractor is required.")
        if not self.handlers:
            raise ValueError("Atlease one storage handler is required")
        if not self.jobs:
            raise ValueError("Atlease one job is required")
        
        # verify all handlers have filepath
        for handler in self.handlers:
            handler_name = handler.get_name()
            if handler_name not in self.filedirectory:
                raise ValueError(f"Missing file  path for handler : {handler_name}")

    def run(self)-> Dict[str,any]:
        """
        Execute the scraping pipeline for all jobs.
        
        Returns:
            Dictionary with execution statistics
        """
        start_time = datetime.now()
        stats = {
            "total_jobs": len(self.jobs),
            "successful_jobs": 0,
            "failed_jobs": 0,
            "total_records": 0,
            "job_details": {},
        }

        logger.info("="*60)
        logger.info(f"Pipeline Started | Jobs: {len(self.jobs)} | Extractors: {len(self.extractors)} | Handlers: {len(self.handlers)}")
        logger.info("="*60)

        for job_idx , job in enumerate(self.jobs, 1):
            logger.info(f"\n[{job_idx}/{len(self.jobs)}] Processing job: '{job}' ")
            job_stats = self._process_single_job(job)

            # update global stats
            stats ["job_details"][job] = job_stats
            if job_stats["success"]:
                stats["successful_jobs"] +=1
                stats["total_records"] += job_stats["records_extracted"]
            else:
                stats["failed_jobs"] += 1
        
        # Final Summary
        elapsed = (datetime.now() - start_time).total_seconds()

        logger.info("\n" + "=" *60 )
        logger.info("Pipeline Execution Summary: ")
        logger.info(f" Total Jobs : {stats['total_jobs']}")
        logger.info(f" Successful: {stats['successful_jobs']}")
        logger.info(f" Failed: {stats['failed_jobs']}")
        logger.info(f" Total Recors: {stats['total_records']}")
        logger.info(f" Elapsed Time: {elapsed:.2f}s")
        logger.info("\n" + "=" *60 )

        return stats
    
    def run_single_job(self, job: str) -> Dict:
        """
        Convenience method to run pipeline for a single job.
        
        Args:
            job: Job title to scrape
            
        Returns:
            Job-level statistics
        """
        logger.info(f"Running pipeline for single job: '{job}'")
        return self._process_single_job(job)
    
    def _process_single_job(self , job: str) -> Dict:
        """
        Process a single job across all extractors and handlers.

        Args:
            job: Job title to scrape

        Returns:
            Dictionary with job-level stastics

        """

        job_stats = {
            "success": False,
            "records_extracted": 0,
            "extractors_used": 0,
            "handlers_used": 0,
            "errors": []
        }

        all_data = []

        # Extraction phase
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__

            logger.info(f"Extractor={extractor_name} | starting extraction....")

            try:
                data = extractor.extract(job)
                record_count = len(data)

                if record_count >0:
                    all_data.extend(data)
                    job_stats["extractors_used"] += 1
                    logger.info(f"Extractor={extractor_name} | Extracted {len(data)} records")
            except Exception as e:
                error_msg = f"Extractor {extractor_name} failed: {str(e)}"
                logger.error(f" {error_msg}", exc_info = True)
                job_stats["errors"].append(error_msg)
                continue
            
            # check if any data is extracted
            if not  all_data:
                logger.warning(f" No data extracted for job '{job}' from any extractor")
                return job_stats
            
            job_stats["records_extracted"] = len(all_data)

            
        # Storage Phase
        logger.info(f" Saving {len(all_data)} records using {len(self.handlers)} handler(s)... ")
        for handler in self.handlers:
            handler_name = handler.get_name()
            filename = self.filedirectory[handler_name]

            try:
                handler.save(all_data, filename)
                job_stats["handlers_used"] += 1
                logger.info(f"Handler={handler_name} | Saved data to {filename}")
            except Exception as e:
                error_msg = f"Handler {handler_name} failed : {str(e)}"
                logger.error(f" {error_msg}", exc_info=True)
                job_stats["errors"].append(error_msg)
                continue
            
            
        # Mark as successful if at least one handler succeeded
        if job_stats["handlers_used"] > 0:
            job_stats["success"] = True
           
        return job_stats



# Example usage
if __name__ == "__main__":

    
    from src.utils.logger import setup_logging
    
    # Setup logging
    setup_logging()
    
    # Initialize components
    extractors = [
        GeneralJobScraper(
            max_pages=2,
            per_page_limit=5,
            min_delay=2,
            max_delay=4
        )
    ]
    
    handlers = [
        CSVStorageHandler()
    ]
    
    jobs = ["Python Developer", "Data Scientist"]
    
    filedirectory = {
        "CSVStorageHandler": "data/scraped_jobs.csv"
    }
    
    # Run pipeline
    pipeline = NaukriGeneralJobDataExtractionPipeline(
        extractors=extractors,
        handlers=handlers,
        jobs=jobs,
        filedirectory=filedirectory,

    )
    
    stats = pipeline.run()
    print(f"\nPipeline completed! Total records: {stats['total_records']}")
    


