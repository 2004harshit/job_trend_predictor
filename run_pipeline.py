"""
run_pipeline.py - Main pipeline orchestrator for job scraping.

This script manages multiple extractors (NaukriJobExtractor, FresherJobExtractor)
and their respective storage handlers (CSV, MySQL).

Usage:
    python run_pipeline.py --mode general --group group1
    python run_pipeline.py --mode fresher --group group2
    python run_pipeline.py --mode all
"""

import yaml
import sys
import os
import time
import logging
import argparse
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Import extractors
from airflow_automation.etl_pipeline.data_collection.extractors.NaukriExtractor import NaukriJobExtractor
from src.scrapers.naukri_fresher_extractor import FresherJobExtractor

# Import storage handlers
from airflow_automation.etl_pipeline.data_collection.storage.CSVStoragehandler import CSVStorageHandler
from src.storage.sqlite_handler import MySQLStorageHandler

# Import pipelines
from airflow_automation.etl_pipeline.data_collection.pipeline import Pipeline
from pipelines.naukri_fresher_job_scraping_pipeline import NaukriFresherJobDataExtractionPipeline

# Import utilities
from airflow_automation.etl_pipeline.utils.logger import setup_logging

load_dotenv()

class PipelineOrchestrator:
    """Orchestrates different scraping pipelines based on configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the pipeline orchestrator.
        
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        self.config = self._load_config(config_path)
        self.logger = self._setup_logger()
        
    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file
            
        Returns:
            Configuration dictionary
        """
        if config_path is None:
            # Try multiple possible locations
            possible_paths = [
                "config/config.yml",
                "configuration/config.yml",
                "../config/config.yml",
                "../configuration/config.yml"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            else:
                raise FileNotFoundError(
                    f"Configuration file not found. Searched in: {possible_paths}"
                )
        
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging configuration."""
        if not logging.getLogger().hasHandlers():
            setup_logging()
        return logging.getLogger("pipeline_orchestrator")
    
    def _initialize_general_extractor(self) -> List:
        """
        Initialize Naukri general job extractor.
        
        Returns:
            List of extractor instances
        """
        pipeline_config = self.config['pipeline']
        
        extractor = NaukriJobExtractor(
            max_pages=pipeline_config.get('max_pages', 10),
            per_page_limit=pipeline_config.get('per_page_limit', 15),
            min_delay=pipeline_config.get('min_delay', 3),
            max_delay=pipeline_config.get('max_delay', 7),
            role_delay=pipeline_config.get('role_delay', 20),
            logger=self.logger
        )
        
        self.logger.info("Initialized NaukriJobExtractor")
        return [extractor]
    
    def _initialize_fresher_extractor(self) -> List:
        """
        Initialize Fresher job extractor.
        
        Returns:
            List of extractor instances
        """
        pipeline_config = self.config['pipeline']
        
        extractor = FresherJobExtractor(
            max_pages=pipeline_config.get('fresher_max_pages', 5),
            per_page_limit=pipeline_config.get('fresher_per_page_limit', 20),
            min_delay=pipeline_config.get('fresher_min_delay', 2),
            max_delay=pipeline_config.get('fresher_max_delay', 5),
            role_delay=pipeline_config.get('fresher_role_delay', 15),
            logger=self.logger
        )
        
        self.logger.info("Initialized FresherJobExtractor")
        return [extractor]
    
    def _initialize_csv_handler(self) -> CSVStorageHandler:
        """
        Initialize CSV storage handler.
        
        Returns:
            CSVStorageHandler instance
        """
        self.logger.info("Initialized CSVStorageHandler")
        return CSVStorageHandler(logger=self.logger)
    
    def _initialize_mysql_handler(self) -> MySQLStorageHandler:
        """
        Initialize MySQL storage handler.
        
        Returns:
            MySQLStorageHandler instance
        """
        # Load database credentials from environment or config
        db_config = self.config.get('database', {})
        
        handler = MySQLStorageHandler(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 3306),
            user=os.getenv("DB_USER") if db_config['user'] == '${DB_USER}' else db_config['user'],
            password=os.getenv("DB_PASSWORD") if db_config['password'] == '${DB_PASSWORD}' else db_config['password'],
            database=db_config.get('database', os.getenv('DB_NAME')),
            logger=self.logger
        )
        
        self.logger.info("Initialized MySQLStorageHandler")
        return handler
    
    def _get_jobs_from_config(self, group: Optional[str] = None, mode: str = 'general') -> List[str]:
        """
        Get job list from configuration.
        
        Args:
            group: Specific group to run (e.g., 'group1')
            mode: Pipeline mode ('general' or 'fresher')
            
        Returns:
            List of job titles
        """
        # Determine which job queue to use
        queue_key = 'fresher_job_queue' if mode == 'fresher' else 'job_queue'
        job_queue = self.config.get(queue_key, {})
        
        if group and group in job_queue:
            jobs = job_queue[group]
            self.logger.info(f"Running {mode} mode for group '{group}' with {len(jobs)} jobs")
            return jobs
        
        # Return all jobs if no group specified
        all_jobs = []
        for jobs in job_queue.values():
            all_jobs.extend(jobs)
        
        self.logger.info(f"Running {mode} mode for ALL groups with {len(all_jobs)} jobs")
        return all_jobs
    
    def run_general_pipeline(self, group: Optional[str] = None) -> Dict:
        """
        Run general job extraction pipeline with CSV storage.
        
        Args:
            group: Optional job group to process
            
        Returns:
            Pipeline execution statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting GENERAL Job Extraction Pipeline")
        self.logger.info("=" * 60)
        
        # Initialize components
        extractors = self._initialize_general_extractor()
        handlers = [self._initialize_csv_handler()]
        jobs = self._get_jobs_from_config(group, mode='general')
        
        # Get file directory
        storage_config = self.config.get('storage', {})
        filedirectory = storage_config.get('filedirectory', {}).get(
            'CSVStorageHandler',
            'data/raw/general_jobs.csv'
        )
        
        # Create pipeline
        pipeline = Pipeline(
            extractors=extractors,
            handlers=handlers,
            jobs=jobs,
            filedirectory=filedirectory,
            logger=self.logger
        )
        
        # Execute
        start_time = time.time()
        stats = pipeline.run()
        execution_time = time.time() - start_time
        
        # Log results
        self.logger.info("=" * 60)
        self.logger.info("General Pipeline Completed Successfully!")
        self.logger.info(f"Total records scraped: {stats.get('total_records', 0)}")
        self.logger.info(f"Execution time: {execution_time:.2f} seconds")
        self.logger.info(f"Data saved to: {filedirectory}")
        self.logger.info("=" * 60)
        
        return stats
    
    def run_fresher_pipeline(self, group: Optional[str] = None) -> Dict:
        """
        Run fresher job extraction pipeline with MySQL storage.
        
        Args:
            group: Optional job group to process
            
        Returns:
            Pipeline execution statistics
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting FRESHER Job Extraction Pipeline")
        self.logger.info("=" * 60)
        
        # Initialize components
        extractors = self._initialize_fresher_extractor()
        handlers = [self._initialize_mysql_handler()]
        jobs = self._get_jobs_from_config(group, mode='fresher')
        
        # Get database table name
        db_config = self.config.get('database', {})
        table_name = db_config.get('raw_job_data', 'raw_job_data')
        
        # Create specialized fresher pipeline
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=extractors,
            handlers=handlers,
            job_roles=jobs,
            logger=self.logger,
            filedirectory={"MySQLStorageHandler" :""}
        )
        
        # Execute
        start_time = time.time()
        stats = pipeline.run()
        execution_time = time.time() - start_time
        
        # Log results
        self.logger.info("=" * 60)
        self.logger.info("Fresher Pipeline Completed Successfully!")
        self.logger.info(f"Total records scraped: {stats.get('total_records', 0)}")
        self.logger.info(f"Execution time: {execution_time:.2f} seconds")
        self.logger.info(f"Data saved to database table: {table_name}")
        self.logger.info("=" * 60)
        
        return stats
    
    def run_all_pipelines(self, group: Optional[str] = None) -> Dict:
        """
        Run both general and fresher pipelines sequentially.
        
        Args:
            group: Optional job group to process
            
        Returns:
            Combined statistics from both pipelines
        """
        self.logger.info("#" * 60)
        self.logger.info("Starting ALL Pipelines (General + Fresher)")
        self.logger.info("#" * 60)
        
        # Run general pipeline
        general_stats = self.run_general_pipeline(group)
        
        # Wait between pipelines to avoid rate limiting
        self.logger.info("Waiting 30 seconds before starting fresher pipeline...")
        time.sleep(30)
        
        # Run fresher pipeline
        fresher_stats = self.run_fresher_pipeline(group)
        
        # Combine statistics
        combined_stats = {
            'general': general_stats,
            'fresher': fresher_stats,
            'total_records': (
                general_stats.get('total_records', 0) + 
                fresher_stats.get('total_records', 0)
            )
        }
        
        self.logger.info("#" * 60)
        self.logger.info("ALL Pipelines Completed Successfully!")
        self.logger.info(f"Total records across all pipelines: {combined_stats['total_records']}")
        self.logger.info("#" * 60)
        
        return combined_stats


def main():
    """Main execution function with CLI argument parsing."""
    
    parser = argparse.ArgumentParser(
        description="Job Scraping Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run general pipeline for all jobs
  python run_pipeline.py --mode general
  
  # Run fresher pipeline for specific group
  python run_pipeline.py --mode fresher --group group1
  
  # Run both pipelines for group2
  python run_pipeline.py --mode all --group group2
  
  # Use custom config file
  python run_pipeline.py --mode general --config custom_config.yml
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['general', 'fresher', 'all'],
        default='general',
        help='Pipeline mode: general (CSV), fresher (MySQL), or all (both)'
    )
    
    parser.add_argument(
        '--group',
        type=str,
        help='Specific job group to process (e.g., group1, group2). If not specified, runs all groups.',
        default=None
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(config_path=args.config)
        
        # Run appropriate pipeline(s)
        if args.mode == 'general':
            stats = orchestrator.run_general_pipeline(group=args.group)
        elif args.mode == 'fresher':
            stats = orchestrator.run_fresher_pipeline(group=args.group)
        elif args.mode == 'all':
            stats = orchestrator.run_all_pipelines(group=args.group)
        
        # Exit successfully
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user. Exiting gracefully...")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()