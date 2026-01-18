from ....etl_pipeline.data_collection.base import StorageHandler
from typing import List, Dict
import pandas as pd
import csv
import os
import logging


class CSVStorageHandler(StorageHandler):
    def __init__(self, output_dir: str = "data/raw", logger=None):
        """
        Initialize CSV Storage Handler
        
        Args:
            output_dir: Directory where CSV files will be saved
            logger: Logger instance (if None, creates a default logger)
        """
        self.output_dir = output_dir
        
        # Initialize logger - CRITICAL FIX
        if logger is None:
            self.logger = logging.getLogger(self.__class__.__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(levelname)s: %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        else:
            self.logger = logger

    def get_name(self) -> str:
        return "CSVStorageHandler"

    def save(self, clean_dataset: List[Dict], filename: str) -> None:
        """
        Save data to CSV file
        
        Args:
            clean_dataset: List of dictionaries containing job data
            filename: Name of the output CSV file
        """
        if not clean_dataset:
            self.logger.warning("No data received to save. Skipping write.")
            return
        
        # Convert to DataFrame
        try:
            df = pd.DataFrame(clean_dataset)
            self.logger.debug(f"Converted dataset with {len(df)} rows into DataFrame.")
        except Exception as e:
            self.logger.error(f"Error converting data to DataFrame: {e}")
            return  # ✅ CRITICAL: Return here to stop execution
        
        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except Exception as e:
            self.logger.error(f"Error creating directory for {filename}: {e}")
            return
        
        # Save to CSV
        try:
            # Check if file exists to determine if we need headers
            file_exists = os.path.isfile(filename)
            
            df.to_csv(
                filename, 
                mode="a" if file_exists else "w",  # Append if exists, write if new
                index=False, 
                header=not file_exists,  # No header if appending
                encoding='utf-8'
            )
            self.logger.info(f"Saved {len(df)} rows to {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving data to CSV file {filename}: {e}")
            raise  # Re-raise to let caller know it failed

    @staticmethod
    def file_exists(path: str) -> bool:
        """Check if file exists"""
        return os.path.isfile(path)
    

# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    handler = CSVStorageHandler()
    sample_data = [
        {"job_title": "Data Scientist", "company": "TechCorp", "location": "New York"},
        {"job_title": "ML Engineer", "company": "InnovateX", "location": "San Francisco"}
    ]
    handler.save(sample_data, "data/raw/job.csv")