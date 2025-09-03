from base import StorageHandler
from typing import List , Dict 
import pandas as pd
import csv

class CSVStorageHandler(StorageHandler):

    def get_name(self) -> str:
        return "CSVStorageHandler"

    def save(self , clean_dataset: List[Dict] , filename: str)->None:

        if not clean_dataset:
            return
        df = pd.DataFrame(clean_dataset)

        df.to_csv(filename, mode="a", index=False, header=not self._file_exists(filename))
    
    @staticmethod
    def _file_exists(path: str) -> bool:
        try:
            with open(path, "r"):
                return True
        except FileNotFoundError:
            return False
