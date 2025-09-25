from etl_pipeline.data_collection.base import StorageHandler
from typing import List , Dict 
import pandas as pd
import csv
import os
from airflow.utils.log.logging_mixin import LoggingMixin

class CSVStorageHandler(StorageHandler):
    def __init__(self, logger=None):
        self.logger = logger or LoggingMixin().log

    def get_name(self) -> str:
        return "CSVStorageHandler"

    def save(self , clean_dataset: List[Dict] , filename: str)->None:
        if not clean_dataset:
            self.logger.warning("No data received to save. Skipping write.")
            return
        
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            df = pd.DataFrame(clean_dataset)
            self.logger.debug(f"Converted dataset with {len(df)} rows into DataFrame.")
        except Exception as e:
            self.logger.warning(f"An error occured while converting data into dataframe : {e}")

        try:
            df.to_csv(filename, mode="a", index=False, header = not CSVStorageHandler.file_exists(filename))
            self.logger.info(f"Saved {len(df)} rows into CSV file at {filename}")
        except Exception as e:
            self.logger.exception(f"Error occurred while saving data into CSV file {filename}")

    @staticmethod
    def file_exists(path: str) -> bool:
        try:
            with open(path, "r"):
                return True
        except FileNotFoundError:
            return False