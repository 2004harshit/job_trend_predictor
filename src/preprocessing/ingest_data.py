from abc import ABC, abstractmethod
import pandas as pd



class DataIngestor(ABC):
    @abstractmethod
    def ingest(self , file_path: str)->pd.DataFrame:
        pass


class CSVIngestor(DataIngestor):
    def ingest(self, file_path: str) -> pd.DataFrame:
        return pd.read_csv(file_path)
    
class JSONIngestor(DataIngestor):
    def ingest(self, file_path: str) -> pd.DataFrame:
        return pd.read_json(file_path)
    
class ExcelIngestor(DataIngestor):
    def ingest(self, file_path: str) -> pd.DataFrame:
        return pd.read_excel(file_path)
    

class DataIngestionFactory:
    @staticmethod
    def get_ingestor(file_type: str) -> DataIngestor:
        if file_type == 'csv':
            return CSVIngestor()
        elif file_type == 'json':
            return JSONIngestor()
        elif file_type == 'excel':
            return ExcelIngestor()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        

# Example usage:
if __name__ == "__main__":
    file_path = r"D:\DATA SCIENCE AND ML\job_trend_predictor\airflow_automation\etl_pipeline\data\raw\scraped_data.csv"
    file_type = "csv"
    
    ingestor = DataIngestionFactory.get_ingestor(file_type)
    df = ingestor.ingest(file_path)
    print(df.head())