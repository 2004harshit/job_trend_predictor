from abc import ABC , abstractmethod
from typing import List , Dict ,Union

class JobExtractor(ABC):
    """
    Abstract base class for all job extractors.
    Each extractor (e.g., NaukriExtractor, LinkedInExtractor)
    must implement the extract method.
    """
    @abstractmethod
    def extract(self , job_name: Union[str, List[str]] , max_pages: int , max_limit: int)-> List[Dict[str, str]]: 
        pass

    @abstractmethod
    def get_name(self)->str:
        """Return extractor name (e.g., 'NaukriExtractor','LinkedinExtractor')"""
        pass


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
