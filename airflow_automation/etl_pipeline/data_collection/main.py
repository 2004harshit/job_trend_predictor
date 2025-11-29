"""
Main entry point for job scraping pipeline.
Loads configuration and orchestrates the scraping process
"""

from .pipeline import Pipeline  # Same folder
from .extractors.NaukriExtractor import NaukriJobExtractor
from .storage.CSVStoragehandler import CSVStorageHandler
from ..utils.logger import setup_logging  # One level up to etl_pipeline


import yaml
import sys
import os
import time
import logging
from typing import List, Dict, Optional

def load_config(config_path=None) -> dict:
    """Load configuratuon from YAML file. """
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))  # project root
        config_path = os.path.join(base_dir, "configuration", "config.yml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    
def initialize_extractors(config: dict , logger)-> List:
    """Initilize extractors based on configurtion."""
    pipeline_config = config['pipeline']

    extractors = [
        NaukriJobExtractor(
            max_pages=pipeline_config['max_pages'],
            per_page_limit=pipeline_config['per_page_limit'],
            min_delay=pipeline_config['min_delay'],
            max_delay=pipeline_config['max_delay'],
            role_delay=pipeline_config['role_delay'],
            logger=logger
        )
    ]

    return extractors

def initialize_handlers(config: dict)-> List:
    """Initilize storage handlers based on configuration."""
    handler_names = config['handlers']
    handlers = []

    handler_map = {
        'CSVStorageHandler': CSVStorageHandler,
        # 'JSONStorageHandler': JSONStorageHandler
    }

    for handler_name in handler_names:
        if handler_name in handler_map:
            handlers.append(handler_map[handler_name]())
        else:
            logging.warning(f"Unknown handler: {handler_name}")
    
    return handlers

def get_jobs_from_config(config: dict , group: str = None)-> List:
    """
    Get job list from config.

    Args:
        config: Configuration dictionary
        group: Specific group to run (e.g, 'group1', or None for all)
    
    Returns:
        List of job titles
    """
    job_queue = config['job_queue']

    if group and group in job_queue:
        return job_queue[group]
    
    # Return all bobs if no group specified
    all_jobs = []
    for job in job_queue.values():
        all_jobs.extend(job)
    
    return all_jobs

def main(group: str = None):
    """
    Main execution function.
    
    Args:
        group: Optional job group to process (e.g., 'group1')
    """
    # Setup logging
    setup_logging()
    logger = logging.getLogger("pipeline")
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    extractors = initialize_extractors(config, logger)
    handlers = initialize_handlers(config)
    jobs = get_jobs_from_config(config, group)
    filedirectory = config['storage']['filedirectory']
    

    # Create and run pipeline
    pipeline = Pipeline(
        extractors=extractors,
        handlers=handlers,
        jobs=jobs,
        filedirectory=filedirectory,
        logger=logger
    )
    
    # Execute
    stats = pipeline.run()
    
    # Final output
    logger.info(f"\n🎉 Pipeline completed successfully!")
    logger.info(f"Total records scraped: {stats['total_records']}")
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Scraping Pipeline")
    parser.add_argument(
        '--group',
        type=str,
        help='Specific job group to process (e.g., group1, group2)',
        default=None
    )
    
    args = parser.parse_args()
    
    # Run with optional group filter
    # Example: python main.py --group group1
    main(group=args.group)