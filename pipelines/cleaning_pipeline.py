"""
Data Cleaning Pipeline — Orchestrator
====================================

This pipeline handles the end-to-end cleaning process:
1. Loads raw job data from a configured CSV path.
2. Initializes the JobDataCleaner with specialized strategies.
3. Applies all cleaning strategies to the data.
4. Saves the results to the processed/cleaned directory.
"""

import pandas as pd
import os
import yaml
import time
from pathlib import Path
from typing import Dict, Any

from src.utils.logger import get_logger, setup_logging
from src.cleaners.job_data_cleaner import JobDataCleaner

# Initialize logger for this pipeline component
logger = get_logger(__name__)

class DataCleaningPipeline:
    """
    Orchestrates the data cleaning process for job market data.
    """

    def __init__(self, config_path: str = "config/cleaning_config.yaml"):
        """
        Initialize the pipeline with configuration.
        
        Args:
            config_path: Path to the cleaning configuration YAML.
        """
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Initialize the cleaner with the config
        self.cleaner = JobDataCleaner(config_path)
        
        # Set up paths from config
        data_cfg = self.config.get("data_paths", {})
        self.input_path = data_cfg.get("input_path", "data/raw/general_jobs.csv")
        self.output_dir = data_cfg.get("output_dir", "data/processed/cleaned")
        self.output_file = data_cfg.get("output_file", "cleaned_job_data.csv")

    def _load_config(self, config_path: str) -> dict:
        """Load and parse the YAML configuration file."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from '{config_path}': {e}")
            raise

    def run(self) -> Dict[str, Any]:
        """
        Run the data cleaning pipeline.
        
        Returns:
            Dictionary containing execution statistics.
        """
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("DATA CLEANING PIPELINE STARTED")
        logger.info("=" * 60)
        logger.info(f"Input path:  {self.input_path}")
        logger.info(f"Output path: {os.path.join(self.output_dir, self.output_file)}")

        stats = {
            "status": "failed",
            "rows_before": 0,
            "rows_after": 0,
            "execution_time_seconds": 0,
            "error": None
        }

        try:
            # 1. Load data
            if not os.path.exists(self.input_path):
                raise FileNotFoundError(f"Input data not found at: {self.input_path}")
            
            logger.info("Loading raw data...")
            df = pd.read_csv(self.input_path)
            stats["rows_before"] = len(df)
            logger.info(f"Successfully loaded {len(df)} rows.")

            # 2. Run Cleaning
            logger.info("Starting cleaning process...")
            cleaned_df = self.cleaner.clean_all(df)
            stats["rows_after"] = len(cleaned_df)
            logger.info("Cleaning process completed successfully.")

            # 3. Save Data
            logger.info(f"Saving cleaned data to {self.output_dir}...")
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, self.output_file)
            cleaned_df.to_csv(output_path, index=False)
            logger.info(f"Cleaned data saved to: {output_path}")

            stats["status"] = "success"

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            stats["error"] = str(e)
            raise

        finally:
            end_time = time.time()
            stats["execution_time_seconds"] = end_time - start_time
            logger.info("=" * 60)
            logger.info("CLEANING PIPELINE SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Status:         {stats['status']}")
            logger.info(f"Rows processed: {stats['rows_before']}")
            logger.info(f"Rows output:    {stats['rows_after']}")
            logger.info(f"Time taken:     {stats['execution_time_seconds']:.2f}s")
            logger.info("=" * 60)

        return stats

def main():
    """Entry point for standalone execution."""
    # Ensure logging is set up
    setup_logging()
    
    try:
        pipeline = DataCleaningPipeline()
        pipeline.run()
    except Exception as e:
        print(f"FATAL: Cleaning pipeline failed. Check logs for details. Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
