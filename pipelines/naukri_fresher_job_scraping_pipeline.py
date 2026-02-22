"""
Naukri Fresher Job Data Extraction Pipeline
Specialized pipeline for extracting, validating, and storing fresher/entry-level job data.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

# ─── Correct logger import ──────────────────────────────────────────────────────
from src.utils.logger import get_logger

logger = get_logger(__name__)

# ─── Project imports ────────────────────────────────────────────────────────────
from src.storage.sqlite_handler import MySQLStorageHandler   # ← note: file says sqlite but class is MySQL
from src.scrapers.naukri_fresher_job_scraper import FresherJobScraper
from src.scrapers.base_scraper import JobExtractor
from src.storage.base_storage_handler import StorageHandler


class NaukriFresherJobDataExtractionPipeline:
    """
    Modular pipeline for extracting fresher job listings from Naukri
    and storing them using one or multiple storage handlers.
    """

    def __init__(
        self,
        extractors: List[Any],           # List[JobExtractor]
        handlers: List[Any],             # List[StorageHandler]
        job_roles: List[str],
        filedirectory: Dict[str, str],
        locations: Optional[List[str]] = None,
    ):
        self.extractors = extractors
        self.handlers = handlers
        self.job_roles = job_roles
        self.filedirectory = filedirectory
        self.locations = locations

        self._validate_configuration()

    def _validate_configuration(self) -> None:
        if not self.extractors:
            raise ValueError("At least one extractor is required.")
        if not self.handlers:
            raise ValueError("At least one storage handler is required.")
        if not self.job_roles:
            raise ValueError("At least one job role is required.")

        for handler in self.handlers:
            name = handler.get_name()
            if name not in self.filedirectory:
                raise ValueError(f"Missing file/path config for handler: {name}")

        logger.info("Pipeline configuration validated successfully")

    def run(self) -> Dict[str, Any]:
        start_time = datetime.now()

        stats = {
            "total_job_roles": len(self.job_roles),
            "successful_jobs": 0,
            "failed_jobs": 0,
            "total_records": 0,
            "fresher_friendly_records": 0,
            "job_details": {},
            "start_time": start_time.isoformat(),
        }

        logger.info("=" * 80)
        logger.info("NAUKRI FRESHER JOB EXTRACTION PIPELINE STARTED")
        logger.info("=" * 80)
        logger.info(f"Job roles: {len(self.job_roles)}")
        logger.info(f"Extractors: {len(self.extractors)}")
        logger.info(f"Handlers: {len(self.handlers)}")
        if self.locations:
            logger.info(f"Locations: {', '.join(self.locations)}")
        logger.info("=" * 80)

        for idx, role in enumerate(self.job_roles, 1):
            logger.info(f"\n{'─'*80}")
            logger.info(f"[{idx}/{len(self.job_roles)}] Processing: {role}")
            logger.info(f"{'─'*80}")

            job_stats = self._process_single_job_role(role)
            stats["job_details"][role] = job_stats

            if job_stats["success"]:
                stats["successful_jobs"] += 1
                stats["total_records"] += job_stats["records_extracted"]
                stats["fresher_friendly_records"] += job_stats.get("fresher_friendly", 0)
            else:
                stats["failed_jobs"] += 1

        end_time = datetime.now()
        stats["end_time"] = end_time.isoformat()
        stats["execution_time_seconds"] = (end_time - start_time).total_seconds()

        self._log_pipeline_summary(stats)
        return stats

    def run_single_job(self, job_role: str) -> Dict[str, Any]:
        logger.info(f"Single job mode → {job_role}")
        return self._process_single_job_role(job_role)

    def _process_single_job_role(self, job_role: str) -> Dict[str, Any]:
        job_stats = {
            "success": False,
            "records_extracted": 0,
            "fresher_friendly": 0,
            "extractors_used": 0,
            "handlers_used": 0,
            "errors": [],
            "storage_results": {}
        }

        all_data = []

        # Extraction
        for extractor in self.extractors:
            name = extractor.__class__.__name__
            logger.info(f"  Extractor → {name}")

            try:
                data = extractor.extract([job_role], locations=self.locations)
                count = len(data)
                if count > 0:
                    all_data.extend(data)
                    job_stats["extractors_used"] += 1

                    fresher_count = sum(1 for j in data if j.get("Is_Fresher_Friendly", True))
                    job_stats["fresher_friendly"] += fresher_count

                    logger.info(f"  → extracted {count} jobs ({fresher_count} fresher-friendly)")
                else:
                    logger.warning(f"  → no jobs found")
            except Exception as e:
                msg = f"Extractor {name} failed: {str(e)}"
                logger.error(msg, exc_info=True)
                job_stats["errors"].append(msg)

        if not all_data:
            logger.warning(f"No data collected for '{job_role}'")
            return job_stats

        job_stats["records_extracted"] = len(all_data)

        # Storage
        logger.info(f"  Storing {len(all_data)} records using {len(self.handlers)} handler(s)")

        for handler in self.handlers:
            name = handler.get_name()
            path = self.filedirectory.get(name, "")

            try:
                result = handler.save(all_data, path)
                job_stats["storage_results"][name] = result
                job_stats["handlers_used"] += 1

                if isinstance(result, dict):
                    logger.info(
                        f"  {name} → inserted:{result.get('inserted',0)}  "
                        f"duplicates:{result.get('duplicates',0)}  "
                        f"errors:{result.get('errors',0)}"
                    )
                else:
                    logger.info(f"  {name} → saved to {path}")
            except Exception as e:
                msg = f"Handler {name} failed: {str(e)}"
                logger.error(msg, exc_info=True)
                job_stats["errors"].append(msg)

        job_stats["success"] = job_stats["handlers_used"] > 0
        return job_stats

    def _log_pipeline_summary(self, stats: Dict[str, Any]) -> None:
        logger.info("\n" + "="*80)
        logger.info("PIPELINE SUMMARY")
        logger.info("="*80)
        logger.info(f"Job roles:      {stats['total_job_roles']}")
        logger.info(f"Successful:     {stats['successful_jobs']}")
        logger.info(f"Failed:         {stats['failed_jobs']}")
        logger.info(f"Total records:  {stats['total_records']}")
        logger.info(f"Fresher jobs:   {stats['fresher_friendly_records']}")
        logger.info(f"Duration:       {stats['execution_time_seconds']:.2f} s")
        logger.info(f"Start:          {stats['start_time']}")
        logger.info(f"End:            {stats['end_time']}")

        if stats.get("job_details"):
            logger.info("-"*80)
            logger.info("Per-role breakdown:")
            for role, s in stats["job_details"].items():
                status = "OK" if s["success"] else "FAIL"
                logger.info(
                    f"  {status} {role:<18} "
                    f"{s['records_extracted']} records "
                    f"({s.get('fresher_friendly',0)} fresher)"
                )
                if s.get("errors"):
                    for err in s["errors"]:
                        logger.warning(f"     → {err}")

        logger.info("="*80 + "\n")

    def get_pipeline_info(self) -> Dict[str, Any]:
        return {
            "extractors": [e.__class__.__name__ for e in self.extractors],
            "handlers": [h.get_name() for h in self.handlers],
            "job_roles": self.job_roles,
            "locations": self.locations,
        }


# ─── Standalone / development usage ─────────────────────────────────────────────
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from src.utils.logger import setup_logging

    # Logging **must** be initialized before anything else
    setup_logging()

    load_dotenv()
    db_password = os.getenv("DB_PASSWORD")

    if not db_password:
        logger.error("DB_PASSWORD not found in environment")
        exit(1)

    extractors = [
        FresherJobScraper(
            max_pages=2,
            per_page_limit=5,
            min_delay=2,
            max_delay=4
        )
    ]

    handlers = [
        MySQLStorageHandler(
            host="localhost",
            user="root",
            password=db_password,
            database="sample_db"
        )
    ]

    job_roles = ["Python Developer", "Data Scientist"]

    filedirectory = {
        "MySQLStorageHandler": ""   # not needed for MySQL, but kept for interface
    }

    pipeline = NaukriFresherJobDataExtractionPipeline(
        extractors=extractors,
        handlers=handlers,
        job_roles=job_roles,
        filedirectory=filedirectory
    )

    stats = pipeline.run()
    print(f"\nPipeline finished → {stats['total_records']} records collected")