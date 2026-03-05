from venv import logger

from .base_storage_handler import StorageHandler
from typing import List, Dict
import os 
import yaml
import json
import logging
logger = logging.getLogger(__name__)

class JSONStorageHandler(StorageHandler):
    def __init__(self):
        self.config = self._load_config()
        self.output_dir = self.config.get("output_dir", "data/analytics")

    def get_name(self) -> str:
        return "JSONStorageHandler"
    
    def _load_config(self)->Dict:
        try:
            with open("config.yaml", 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            return{}
    

    def save(self , data:json) -> None:
        import json
        import os
        
        if not data:
            logger.warning("No data received to save. Skipping write.")
            return
        # Ensure directory exists
        try:
            os.makedirs(os.path.dirname(self.output_dir), exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directory for {self.output_dir}: {e}")
            return
        
        # Save to JSON file
        try:
            with open(self.output_dir, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                logger.info(f"Data successfully saved to {self.output_dir}")
        except Exception as e:
                logger.error(f"Error saving data to JSON file: {e}")