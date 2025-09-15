from airflow import DAG
from airflow.decorators import task
from datetime import datetime, timedelta
import os
import yaml
import time
import logging

from core_ml.data_collection.pipeline import Pipeline
from core_ml.data_collection.extractors.NaukriExtractor import NaukriJobExtractor
from core_ml.data_collection.storage.CSVStoragehandler import CSVStorageHandler
from core_ml.configuration.logger import setup_logging


setup_logging()
logger = logging.getLogger("airflow.task")

@task
def run_full_pipeline():
    
    logger.info("Starting the job scraping pipeline")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
    config_path = os.path.join(base_dir , "core_ml","configuration","config.yaml")

    with open(config_path, 'r') as file:
        cfg = yaml.safe_load(file)
    
    logger.info(f"Configuration loaded from {config_path}")
    job_queue = cfg["job_queue"]
    filedirectory = cfg["storage"]["filedirectory"]
    per_page_limit = cfg["pipeline"]["per_page_limit"]
    max_pages = cfg["pipeline"]["max_pages"]
    min_delay = cfg["pipeline"]["min_delay"]
    max_delay = cfg["pipeline"]["max_delay"]
    role_delay = cfg["pipeline"]["role_delay"]

    logger.info(f"extractors and storage handlers initialization")
    extractors = [NaukriJobExtractor(max_pages, per_page_limit, min_delay, max_delay, role_delay)]
    storage_handlers = [CSVStorageHandler()]

    logger.info(f"Starting the pipeline for job queue")
    for group in job_queue:
        for job in job_queue[group]:
            try:
                logger.info(f"Running pipeline for job: {job}")
                pipeline = Pipeline(extractors, storage_handlers, job, filedirectory)
                pipeline.run()
            except Exception as e:
                logger.error(f"Pipeline failed for job: {job}", exc_info=True)
    logger.info("Job scraping pipeline completed")
    


with DAG(
    dag_id = "job_scraper_dag",
    start_date = datetime(2025, 9, 15),
    schedule_interval = "@daily",
    catchup = False,
    default_args = {
        "owner": "airflow",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    }
) as dag:
    

    run_pipeline_task = run_full_pipeline()