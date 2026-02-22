"""
run_pipeline.py - Main orchestrator for job market scraping pipelines

Supports three modes:
  - general   → Naukri general jobs → CSV
  - fresher   → Naukri fresher jobs → MySQL
  - all       → both pipelines sequentially

Usage examples:
  python run_pipeline.py --mode fresher
  python run_pipeline.py --mode general --group group1
  python run_pipeline.py --mode all
  python run_pipeline.py --mode fresher --config config/custom.yml
"""

import yaml
import sys
import os
import time
import argparse
from typing import List, Dict, Optional
from dotenv import load_dotenv

# ─── Logging & Session ──────────────────────────────────────────────────────────
from src.utils.logger import setup_logging, get_logger
from src.utils.session_logger import ScrapeSessionLogger

logger = get_logger(__name__)

# ─── Extractors & Handlers ──────────────────────────────────────────────────────
from src.scrapers.naukri_general_job_scraper import GeneralJobScraper
from src.scrapers.naukri_fresher_job_scraper import FresherJobScraper
from src.storage.csv_storage_handler import CSVStorageHandler
from src.storage.sqlite_handler import MySQLStorageHandler

# ─── Pipeline classes ───────────────────────────────────────────────────────────
from pipelines.naukri_fresher_job_scraping_pipeline import NaukriFresherJobDataExtractionPipeline
from pipelines.naukri_general_pipeline import NaukriGeneralJobDataExtractionPipeline


class PipelineOrchestrator:
    """Central orchestrator that prepares and runs the desired scraping pipeline(s)."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.session_logger = None

    def _load_config(self, config_path: Optional[str] = None) -> dict:
        if config_path is None:
            possible = [
                "config/config.yml",
                "configuration/config.yml",
                "../config/config.yml",
                "../configuration/config.yml",
                "airflow_automation/etl_pipeline/configuration/config.yml",
            ]
            for p in possible:
                if os.path.exists(p):
                    config_path = p
                    break
            else:
                raise FileNotFoundError("No config.yml found in common locations")

        logger.info(f"Loading configuration from: {config_path}")
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            data["__loaded_from__"] = config_path  # useful for session metadata
            return data

    def _get_jobs_from_config(self, group: Optional[str] = None, mode: str = 'general') -> List[str]:
        INVALID = {'-', '--', '---', 'null', 'none', '', ' '}

        def validate(roles: list, src: str) -> List[str]:
            valid = []
            for r in (roles or []):
                if r is None:
                    logger.warning(f"Null role in {src} — skipping")
                    continue
                s = str(r).strip()
                if s.lower() in INVALID or len(s) < 2:
                    logger.warning(f"Invalid role '{r}' in {src} — skipping")
                    continue
                valid.append(s)
            return valid

        key = 'fresher_job_queue' if mode == 'fresher' else 'job_queue'
        queue = self.config.get(key, {})

        if group and group in queue:
            jobs = validate(queue[group], group)
            logger.info(f"Group '{group}' → {len(jobs)} valid roles")
            return jobs

        # all groups
        all_jobs = []
        for gname, roles in queue.items():
            all_jobs.extend(validate(roles, gname))
        logger.info(f"All groups → {len(all_jobs)} valid roles")
        return all_jobs

    def _init_session_logger(self, mode: str, group: Optional[str]) -> Optional[ScrapeSessionLogger]:
        """Initialize session logger safely (your version does not support auto_recover)"""
        try:
            s = ScrapeSessionLogger()  # no auto_recover argument
            total = len(self._get_jobs_from_config(group, mode))
            sid = s.start_session(
                mode=mode,
                total_roles=total,
                group=group or "ALL"
            )
            logger.info(f"Session started: {sid}  (mode={mode}, roles≈{total})")
            return s
        except Exception as e:
            logger.warning(f"Session logger could not start: {e} → continuing without session tracking")
            return None

    def _finalize_session(self, s: Optional[ScrapeSessionLogger], stats: Dict, success: bool = True):
        """Safely close the session logger if it was initialized"""
        if s is None:
            return
        try:
            status = "completed" if success else "failed"
            s.update_session(stats)
            s.end_session(status=status)
            logger.info(f"Session {s.session_id} closed → {status}")
        except Exception as e:
            logger.warning(f"Failed to finalize session: {e}")

    # ─── Pipeline runners ───────────────────────────────────────────────────────────

    def run_general_pipeline(self, group: Optional[str] = None) -> Dict:
        logger.info("GENERAL pipeline" + (f" (group={group})" if group else ""))
        session = self._init_session_logger("general", group)

        try:
            extractors = [GeneralJobScraper(
                max_pages=self.config['pipeline'].get('max_pages', 10),
                per_page_limit=self.config['pipeline'].get('per_page_limit', 15),
                min_delay=self.config['pipeline'].get('min_delay', 3),
                max_delay=self.config['pipeline'].get('max_delay', 7),
                role_delay=self.config['pipeline'].get('role_delay', 20)
            )]

            handlers = [CSVStorageHandler()]

            jobs = self._get_jobs_from_config(group, 'general')

            csv_path = self.config.get('storage', {}).get('filedirectory', {}).get(
                'CSVStorageHandler', 'data/raw/general_jobs.csv'
            )

            pipeline = NaukriGeneralJobDataExtractionPipeline(
                extractors=extractors,
                handlers=handlers,
                jobs=jobs,
                filedirectory={'CSVStorageHandler': csv_path}
            )

            start = time.time()
            stats = pipeline.run()
            stats['execution_time_seconds'] = time.time() - start

            logger.info(f"GENERAL done → {stats.get('total_records', 0)} records")
            self._finalize_session(session, stats)
            return stats

        except Exception as e:
            logger.error("GENERAL pipeline failed", exc_info=True)
            self._finalize_session(session, {}, success=False)
            raise

    def run_fresher_pipeline(self, group: Optional[str] = None) -> Dict:
        logger.info("FRESHER pipeline" + (f" (group={group})" if group else ""))
        session = self._init_session_logger("fresher", group)

        try:
            extractors = [FresherJobScraper(
                max_pages=self.config['pipeline'].get('fresher_max_pages', 5),
                per_page_limit=self.config['pipeline'].get('fresher_per_page_limit', 20),
                min_delay=self.config['pipeline'].get('fresher_min_delay', 2),
                max_delay=self.config['pipeline'].get('fresher_max_delay', 5),
                role_delay=self.config['pipeline'].get('fresher_role_delay', 15),
            )]

            db = self.config.get('database', {})
            handlers = [MySQLStorageHandler(
                host=db.get('host', 'localhost'),
                port=db.get('port', 3306),
                user=os.getenv("DB_USER") if db.get('user') == '${DB_USER}' else db.get('user', 'root'),
                password=os.getenv("DB_PASSWORD") if db.get('password') == '${DB_PASSWORD}' else db.get('password', ''),
                database=db.get('database', os.getenv('DB_NAME', 'job_trend_db')),
                table=db.get('raw_job_data', 'raw_job_data')
            )]

            jobs = self._get_jobs_from_config(group, 'fresher')

            pipeline = NaukriFresherJobDataExtractionPipeline(
                extractors=extractors,
                handlers=handlers,
                job_roles=jobs,
                filedirectory={"MySQLStorageHandler": ""}
            )

            start = time.time()
            stats = pipeline.run()
            stats['execution_time_seconds'] = time.time() - start

            logger.info(f"FRESHER done → {stats.get('total_records', 0)} records")
            self._finalize_session(session, stats)
            return stats

        except Exception as e:
            logger.error("FRESHER pipeline failed", exc_info=True)
            self._finalize_session(session, {}, success=False)
            raise

    def run_all_pipelines(self, group: Optional[str] = None) -> Dict:
        logger.info("ALL pipelines" + (f" (group={group})" if group else ""))
        session = self._init_session_logger("all", group)

        try:
            g_stats = self.run_general_pipeline(group)
            logger.info("Waiting 30s before fresher pipeline...")
            time.sleep(30)
            f_stats = self.run_fresher_pipeline(group)

            combined = {
                'general': g_stats,
                'fresher': f_stats,
                'total_records': g_stats.get('total_records', 0) + f_stats.get('total_records', 0)
            }

            self._finalize_session(session, combined)
            return combined

        except Exception as e:
            logger.error("ALL pipelines failed", exc_info=True)
            self._finalize_session(session, {}, success=False)
            raise


def main():
    parser = argparse.ArgumentParser(description="Job Trend Scraping Orchestrator")
    parser.add_argument('--mode', choices=['general', 'fresher', 'all'], default='general')
    parser.add_argument('--group', type=str, default=None)
    parser.add_argument('--config', type=str, default=None)
    args = parser.parse_args()

    # ─── Logging initialized HERE – once per run ────────────────────────────────
    setup_logging()

    try:
        orch = PipelineOrchestrator(config_path=args.config)

        if args.mode == 'general':
            orch.run_general_pipeline(args.group)
        elif args.mode == 'fresher':
            orch.run_fresher_pipeline(args.group)
        elif args.mode == 'all':
            orch.run_all_pipelines(args.group)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()