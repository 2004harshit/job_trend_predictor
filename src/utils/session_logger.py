import yaml
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Importing your specific setup function
try:
    from .logger import setup_logging
except ImportError:
    from src.utils.logger import setup_logging

class ScrapeSessionLogger:
    """
    Logs scraping sessions to a JSON file for pattern analysis.
    """

    def __init__(self, config_path: str = "config/.yml", log_path: str = "logs/scrape_sessions.json"):
        # 1. Initialize global logging configuration
        # This matches your setup_logging(config_path=None) signature
        setup_logging() 
        
        # 2. Assign the specific logger for this class
        # Now that setup_logging has run dictConfig, this will have your custom settings
        self.logger = logging.getLogger()

        # 3. Load the session-specific app config
        self.config = self._load_config(config_path) or {}

        # 4. Setup Session JSON Log Path
        raw_log_path = self.config.get("session_log_path", log_path)
        self.log_path = Path(raw_log_path)
        
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Could not create log directory for sessions: {e}")

        self.session_id = None
        self.session_data = None
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from a YAML file."""
        p = Path(config_path)
        
        if not p.exists():
            # Using self.logger which was initialized in step 2
            self.logger.error(f"App config file NOT found at: {p.absolute()}")
            return {}

        try:
            with open(p, "r") as f:
                config = yaml.safe_load(f)
                self.logger.info(f"App configuration loaded from {config_path}")
                return config
        except Exception as e:
            self.logger.error(f"Failed to parse app config: {e}")
            return {}

    def start_session(self, mode: str, total_roles: int, group: Optional[str] = None) -> str:
        """Start a new scraping session."""
        self.session_id = f"{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:6]}"

        self.session_data = {
            "session_id": self.session_id,
            "mode": mode,
            "group": group or "ALL",
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "scrape_week": datetime.now().strftime("%Y-W%W"),
            "total_roles": total_roles,
            "successful_roles": 0,
            "failed_roles": 0,
            "total_records_scraped": 0,
            "total_inserted": 0,
            "total_duplicates": 0,
            "total_errors": 0,
            "status": "running",
            "error_summary": []
        }

        self.logger.info(f"Session started: {self.session_id}")
        self._append_to_log(self.session_data)
        return self.session_id

    def update_session(self, pipeline_stats: Dict[str, Any]) -> None:
        """Update session with pipeline run statistics."""
        if not self.session_data:
            self.logger.warning("No active session to update.")
            return

        self.session_data["successful_roles"] = pipeline_stats.get("successful_jobs", 0)
        self.session_data["failed_roles"] = pipeline_stats.get("failed_jobs", 0)
        self.session_data["total_records_scraped"] = pipeline_stats.get("total_records", 0)

        total_inserted = 0
        total_duplicates = 0
        total_errors = 0

        for role, role_stats in pipeline_stats.get("job_details", {}).items():
            for handler, result in role_stats.get("storage_results", {}).items():
                if isinstance(result, dict):
                    total_inserted += result.get("inserted", 0)
                    total_duplicates += result.get("duplicates", 0)
                    total_errors += result.get("errors", 0)

            if role_stats.get("errors"):
                self.session_data["error_summary"].extend([
                    f"{role}: {err}" for err in role_stats["errors"]
                ])

        self.session_data["total_inserted"] = total_inserted
        self.session_data["total_duplicates"] = total_duplicates
        self.session_data["total_errors"] = total_errors

    def end_session(self, status: str = "completed") -> None:
        """End the current session and write final stats."""
        if not self.session_data:
            return

        end_time = datetime.now()
        start_time = datetime.fromisoformat(self.session_data["start_time"])

        self.session_data["end_time"] = end_time.isoformat()
        self.session_data["duration_seconds"] = round(
            (end_time - start_time).total_seconds(), 2
        )
        self.session_data["status"] = status

        self._update_log(self.session_data)

        self.logger.info(
            f"Session ended: {self.session_id} | "
            f"Status: {status} | "
            f"Duration: {self.session_data['duration_seconds']}s"
        )

    def _append_to_log(self, session: dict) -> None:
        sessions = self._load_log()
        sessions.append(session)
        self._write_log(sessions)

    def _update_log(self, session: dict) -> None:
        sessions = self._load_log()
        for i, s in enumerate(sessions):
            if s["session_id"] == session["session_id"]:
                sessions[i] = session
                break
        self._write_log(sessions)

    def _load_log(self) -> list:
        if self.log_path.exists():
            try:
                with open(self.log_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    def _write_log(self, sessions: list) -> None:
        try:
            with open(self.log_path, "w") as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to write session log: {e}")

    def get_summary(self) -> Dict[str, Any]:
        sessions = self._load_log()
        if not sessions:
            return {"message": "No sessions logged yet."}

        completed = [s for s in sessions if s["status"] == "completed"]
        sorted_sessions = sorted(sessions, key=lambda x: x["start_time"])
        
        return {
            "total_sessions": len(sessions),
            "completed": len(completed),
            "total_records_collected": sum(s.get("total_inserted", 0) for s in completed),
            "last_session": sorted_sessions[-1]["start_time"] if sorted_sessions else None
        }


if __name__ == "__main__":
    # Run using: python -m src.utils.session_logger
    session_logger = ScrapeSessionLogger()
    session_id = session_logger.start_session(mode="fresher", total_roles=10)
    
    # Simulate a run
    session_logger.update_session({
        "successful_jobs": 1,
        "total_records": 50,
        "job_details": {
            "Data Engineer": {"storage_results": {"json": {"inserted": 45, "duplicates": 5, "errors": 0}}}
        }
    })
    
    session_logger.end_session(status="completed")
    print("\nTest completed successfully. Check your logs/ directory.")