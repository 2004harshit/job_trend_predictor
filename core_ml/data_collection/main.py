from core_ml.data_collection.pipeline import Pipeline
from core_ml.data_collection.extractors.NaukriExtractor import NaukriJobExtractor
from core_ml.data_collection.storage.CSVStoragehandler import CSVStorageHandler
from core_ml.configuration.logger import setup_logging
import yaml
import sys
import os


def load_config(config_path=None) -> dict:
    if config_path is None:
        base_dir = os.path.dirname(os.path.dirname(__file__))  # project root
        config_path = os.path.join(base_dir, "configuration", "config.yml")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
    

if __name__ == "__main__":
    setup_logging()
    cfg = load_config()

    job_queue = cfg["job_queue"]
    filedirectory = cfg["storage"]["filedirectory"]
    per_page_limit = cfg["pipeline"]["per_page_limit"]
    max_pages = cfg["pipeline"]["max_pages"]
    min_delay = cfg["pipeline"]["min_delay"]
    max_delay = cfg["pipeline"]["max_delay"]
    per_page_limit = cfg["pipeline"]["per_page_limit"]
    role_delay = cfg["pipeline"]["role_delay"]

    extractors = [NaukriJobExtractor(max_pages , per_page_limit , min_delay , max_delay)]
    handlers = [CSVStorageHandler()]

    for group in job_queue:
        for job in group:
            pipeline = Pipeline(extractors, handlers, job, filedirectory)
            pipeline.run()
            break
        break
    sys.exit(0)
