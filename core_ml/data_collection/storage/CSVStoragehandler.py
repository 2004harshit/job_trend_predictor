from base import StorageHandler
from typing import List , Dict 
import pandas as pd
import csv
from config.logger import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

class CSVStorageHandler(StorageHandler):

    def get_name(self) -> str:
        return "CSVStorageHandler"

    def save(self , clean_dataset: List[Dict] , filename: str)->None:
        if not clean_dataset:
            logger.warning("No data received to save. Skipping write.")
            return
        
        try:
            df = pd.DataFrame(clean_dataset)
            logger.debug(f"Converted dataset with {len(df)} rows into DataFrame.")
        except Exception as e:
            logger.warning(f"An error occured while converting data into dataframe : {e}")

        try:
            df.to_csv(filename, mode="a", index=False, header=not self._file_exists(filename))
            logger.info(f"Saved {len(df)} rows into CSV file at {filename}")
        except Exception as e:
            logger.exception(f"Error occurred while saving data into CSV file {filename}")

    @staticmethod
    def _file_exists(path: str) -> bool:
        try:
            with open(path, "r"):
                logger.debug("File already exist at {path}")
                return True  
        except FileNotFoundError:
            logger.info(f"No existing file found at {path}. Creating a new one.")
            return False
