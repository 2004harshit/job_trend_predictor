from abc import ABC, abstractmethod
from typing import List, Dict

class StorageHandler(ABC):
    """
    Abstract base class for all storage handlers.
    Each storage handler (CSV, SQL, etc.) must implement save().
    """
    @abstractmethod
    def save(self , clean_dataset: List[Dict] , filename: str)->None:
        pass

    @abstractmethod
    def get_name(self)->str:
        """Return handler name (e.g., 'csv', 'sql')"""
        pass
