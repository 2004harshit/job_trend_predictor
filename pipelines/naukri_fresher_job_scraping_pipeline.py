"""
Naukri Fresher Job Data Extraction Pipeline
Specialized pipeline for extracting, validating, and storing fresher/entry-level job data.
"""

from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import traceback

# Assuming these are imported from your project structure
from src.storage.sqlite_handler import MySQLStorageHandler
from src.scrapers.naukri_fresher_extractor import FresherJobExtractor
from src.scrapers.base_scraper import JobExtractor
from src.storage.base_storage_handler import StorageHandler


class NaukriFresherJobDataExtractionPipeline:
    """
    A modular pipeline specifically designed for extracting fresher job listings
    from Naukri and storing them using multiple storage handlers.
    
    Features:
    - Multi-extractor support (though typically one FresherJobExtractor)
    - Multi-storage handler support (CSV, MySQL, JSON, etc.)
    - Comprehensive error handling and recovery
    - Detailed statistics tracking per job role
    - Location-based filtering
    - Salary range filtering
    - Experience level validation
    """
    
    def __init__(
        self, 
        extractors: List[Any],  # List[JobExtractor]
        handlers: List[Any],    # List[StorageHandler]
        job_roles: List[str],
        filedirectory: Dict[str, str],
        locations: Optional[List[str]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the Fresher Job Data Extraction Pipeline.
        
        Args:
            extractors: List of JobExtractor instances (typically FresherJobExtractor)
            handlers: List of StorageHandler instances (e.g., MySQLStorageHandler, CSVHandler)
            job_roles: List of job roles to scrape (e.g., ['python-developer', 'data-analyst'])
            filedirectory: Mapping of handler names to file paths/configs
                          Example: {"MySQLStorageHandler": "config.yaml", "CSVStorageHandler": "data/jobs.csv"}
            locations: Optional list of locations to filter (e.g., ['bengaluru', 'mumbai'])
            logger: Optional logger instance
        """
        self.extractors = extractors
        self.handlers = handlers
        self.job_roles = job_roles
        self.filedirectory = filedirectory
        self.locations = locations
        self.logger = logger or logging.getLogger("fresher_pipeline")
        
        # Validate configuration before proceeding
        self._validate_configuration()
        
    def _validate_configuration(self) -> None:
        """
        Validate pipeline configuration before execution.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.extractors:
            raise ValueError("At least one extractor is required.")
        
        if not self.handlers:
            raise ValueError("At least one storage handler is required.")
        
        if not self.job_roles:
            raise ValueError("At least one job role is required.")
        
        # Verify all handlers have filepath/configuration
        
        for handler in self.handlers:
            handler_name = handler.get_name()
            if handler_name not in self.filedirectory:
                raise ValueError(f"Missing file path/config for handler: {handler_name}")
        
        self.logger.info("Pipeline configuration validated successfully")
    
    def run(self) -> Dict[str, Any]:
        """
        Execute the complete fresher job scraping pipeline for all job roles.
        
        Returns:
            Dictionary with comprehensive execution statistics:
            {
                "total_job_roles": int,
                "successful_jobs": int,
                "failed_jobs": int,
                "total_records": int,
                "fresher_friendly_records": int,
                "job_details": {
                    "job_role_name": {
                        "success": bool,
                        "records_extracted": int,
                        "fresher_friendly": int,
                        "extractors_used": int,
                        "handlers_used": int,
                        "errors": List[str]
                    }
                },
                "execution_time_seconds": float,
                "start_time": str,
                "end_time": str
            }
        """
        start_time = datetime.now()
        
        stats = {
            "total_job_roles": len(self.job_roles),
            "successful_jobs": 0,
            "failed_jobs": 0,
            "total_records": 0,
            "fresher_friendly_records": 0,
            "job_details": {},
            "start_time": start_time.isoformat(),
        }
        
        self.logger.info("=" * 80)
        self.logger.info(f" NAUKRI FRESHER JOB EXTRACTION PIPELINE STARTED")
        self.logger.info("=" * 80)
        self.logger.info(f"Job Roles: {len(self.job_roles)}")
        self.logger.info(f"Extractors: {len(self.extractors)}")
        self.logger.info(f"Handlers: {len(self.handlers)}")
        if self.locations:
            self.logger.info(f"Target Locations: {', '.join(self.locations)}")
        self.logger.info("=" * 80)
        
        # Process each job role
        for job_idx, job_role in enumerate(self.job_roles, 1):
            self.logger.info(f"\n{'─' * 80}")
            self.logger.info(f"[{job_idx}/{len(self.job_roles)}]  Processing Job Role: '{job_role}'")
            self.logger.info(f"{'─' * 80}")
            
            job_stats = self._process_single_job_role(job_role)
            
            # Update global statistics
            stats["job_details"][job_role] = job_stats
            
            if job_stats["success"]:
                stats["successful_jobs"] += 1
                stats["total_records"] += job_stats["records_extracted"]
                stats["fresher_friendly_records"] += job_stats.get("fresher_friendly", 0)
            else:
                stats["failed_jobs"] += 1
        
        # Calculate execution time
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        stats["end_time"] = end_time.isoformat()
        stats["execution_time_seconds"] = elapsed
        
        # Final Summary
        self._log_pipeline_summary(stats)
        
        return stats
    
    def run_single_job(self, job_role: str) -> Dict[str, Any]:
        """
        Convenience method to run pipeline for a single job role.
        
        Args:
            job_role: Job role to scrape (e.g., 'python-developer')
            
        Returns:
            Job-level statistics dictionary
        """
        self.logger.info(f"Running pipeline for single job role: '{job_role}'")
        return self._process_single_job_role(job_role)
    
    def _process_single_job_role(self, job_role: str) -> Dict[str, Any]:
        """
        Process a single job role across all extractors and handlers.
        
        Args:
            job_role: Job role to scrape
            
        Returns:
            Dictionary with job-level statistics:
            {
                "success": bool,
                "records_extracted": int,
                "fresher_friendly": int,
                "extractors_used": int,
                "handlers_used": int,
                "errors": List[str],
                "storage_results": Dict
            }
        """
        job_stats = {
            "success": False,
            "records_extracted": 0,
            "fresher_friendly": 0,
            "extractors_used": 0,
            "handlers_used": 0,
            "errors": [],
            "storage_results": {}
        }
        
        all_data = []
        
        # ─────────────────────────────────────────────────────────────────────
        # EXTRACTION PHASE
        # ─────────────────────────────────────────────────────────────────────
        
        for extractor in self.extractors:
            extractor_name = extractor.__class__.__name__
            
            self.logger.info(f"   Extractor: {extractor_name} | Starting extraction...")
            
            try:
                # Extract job data (FresherJobExtractor.extract expects List[str] for roles)
                data = extractor.extract([job_role], locations=self.locations)
                record_count = len(data)
                
                if record_count > 0:
                    all_data.extend(data)
                    job_stats["extractors_used"] += 1
                    
                    # Count fresher-friendly jobs (if flag exists)
                    fresher_count = sum(
                        1 for job in data 
                        if job.get("Is_Fresher_Friendly", True)
                    )
                    job_stats["fresher_friendly"] += fresher_count
                    
                    self.logger.info(
                        f"   Extractor: {extractor_name} | "
                        f"Extracted {record_count} records "
                        f"({fresher_count} fresher-friendly)"
                    )
                else:
                    self.logger.warning(
                        f"   Extractor: {extractor_name} | No records extracted"
                    )
                    
            except Exception as e:
                error_msg = f"Extractor {extractor_name} failed: {str(e)}"
                self.logger.error(f"   {error_msg}")
                self.logger.debug(traceback.format_exc())
                job_stats["errors"].append(error_msg)
                continue
        
        # Check if any data was extracted
        if not all_data:
            self.logger.warning(
                f"   No data extracted for job role '{job_role}' from any extractor"
            )
            return job_stats
        
        job_stats["records_extracted"] = len(all_data)
        
        # ─────────────────────────────────────────────────────────────────────
        # STORAGE PHASE
        # ─────────────────────────────────────────────────────────────────────
        
        self.logger.info(
            f"   Saving {len(all_data)} records using {len(self.handlers)} handler(s)..."
        )
        
        for handler in self.handlers:
            handler_name = handler.get_name()
            filename = self.filedirectory.get(handler_name, "")
            
            try:
                # Save data using handler
                save_result = handler.save(all_data, filename)
                
                # Track storage results
                job_stats["storage_results"][handler_name] = save_result
                job_stats["handlers_used"] += 1
                
                # Log based on handler response
                if isinstance(save_result, dict):
                    # Handler returned statistics (e.g., MySQLStorageHandler)
                    self.logger.info(
                        f"   Handler: {handler_name} | "
                        f"Inserted: {save_result.get('inserted', 0)}, "
                        f"Duplicates: {save_result.get('duplicates', 0)}, "
                        f"Errors: {save_result.get('errors', 0)}"
                    )
                else:
                    # Simple confirmation
                    self.logger.info(
                        f"   Handler: {handler_name} | Saved data to {filename}"
                    )
                    
            except Exception as e:
                error_msg = f"Handler {handler_name} failed: {str(e)}"
                self.logger.error(f"   {error_msg}")
                self.logger.debug(traceback.format_exc())
                job_stats["errors"].append(error_msg)
                continue
        
        # Mark as successful if at least one handler succeeded
        if job_stats["handlers_used"] > 0:
            job_stats["success"] = True
        
        return job_stats
    
    def _log_pipeline_summary(self, stats: Dict[str, Any]) -> None:
        """
        Log a comprehensive summary of pipeline execution.
        
        Args:
            stats: Pipeline execution statistics
        """
        self.logger.info("\n" + "=" * 80)
        self.logger.info(" PIPELINE EXECUTION SUMMARY")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Job Roles: {stats['total_job_roles']}")
        self.logger.info(f" Successful: {stats['successful_jobs']}")
        self.logger.info(f" Failed: {stats['failed_jobs']}")
        self.logger.info(f"-" * 80)
        self.logger.info(f"Total Records Extracted: {stats['total_records']}")
        self.logger.info(f"Fresher-Friendly Jobs: {stats['fresher_friendly_records']}")
        self.logger.info(f"-" * 80)
        self.logger.info(f"Execution Time: {stats['execution_time_seconds']:.2f} seconds")
        self.logger.info(f"Start Time: {stats['start_time']}")
        self.logger.info(f"End Time: {stats['end_time']}")
        
        # Per-job breakdown
        if stats.get("job_details"):
            self.logger.info(f"-" * 80)
            self.logger.info(" Per-Job Role Breakdown:")
            for job_role, job_stats in stats["job_details"].items():
                status = "[OK]" if job_stats["success"] else "[FAIL]"
                self.logger.info(
                    f"  {status} {job_role}: "
                    f"{job_stats['records_extracted']} records "
                    f"({job_stats.get('fresher_friendly', 0)} fresher-friendly)"
                )
                if job_stats.get("errors"):
                    for error in job_stats["errors"]:
                        self.logger.info(f"       {error}")
        
        self.logger.info("=" * 80 + "\n")
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about pipeline configuration.
        
        Returns:
            Dictionary with pipeline configuration details
        """
        return {
            "extractors": [e.__class__.__name__ for e in self.extractors],
            "handlers": [h.get_name() for h in self.handlers],
            "job_roles": self.job_roles,
            "locations": self.locations,
            "total_job_roles": len(self.job_roles),
            "total_extractors": len(self.extractors),
            "total_handlers": len(self.handlers)
        }

if __name__ == "__main__":
   
    from src.utils.logger import setup_logging
    import os
    from dotenv import load_dotenv, dotenv_values

    load_dotenv()
    password = os.getenv("database_password")

    setup_logging()
    logger = logging.getLogger("pipeline")
   
    extractors = [
        FresherJobExtractor(
            max_pages=2,
            per_page_limit=5,
            min_delay=2,
            max_delay=4
        )
    ]
    
    handlers = [
        MySQLStorageHandler(host="localhost",user="root",password=password,database="sample_db")
    ]
    
    jobs = ["Python Developer", "Data Scientist"]
    
    filedirectory = {
        "MySQLStorageHandler" : ""
    }
    
    # Run pipeline
    pipeline = NaukriFresherJobDataExtractionPipeline(
        extractors=extractors,
        handlers=handlers,
        job_roles=jobs,
        filedirectory=filedirectory,
        logger=logger
    )
    
    stats = pipeline.run()
    print(f"\nPipeline completed! Total records: {stats['total_records']}")
    
