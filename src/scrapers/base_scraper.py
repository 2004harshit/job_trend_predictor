from abc import ABC , abstractmethod
from typing import List , Dict ,Union

class JobExtractor(ABC):
    """
    Abstract base class for all job extractors.
    Each extractor (e.g., NaukriExtractor, LinkedInExtractor)
    must implement the extract method.
    """
    @abstractmethod
    def extract(self , job_name: Union[str, List[str]] ,locations:List[str])-> List[Dict[str, str]]: 
        pass

    @abstractmethod
    def get_name(self)->str:
        """Return extractor name (e.g., 'NaukriExtractor','LinkedinExtractor')"""
        pass


