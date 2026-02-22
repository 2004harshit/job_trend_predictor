"""
MySQL Storage Handler for job market data pipeline.
Handles insertion, fetching, and table management with proper logging.
"""

import mysql.connector
from mysql.connector import Error
import json
from typing import List, Dict, Any, Optional

# ─── Central logging ────────────────────────────────────────────────────────────
from src.utils.logger import setup_logging, get_logger

logger = get_logger(__name__)

# ─── Other imports ──────────────────────────────────────────────────────────────
from dotenv import load_dotenv
import yaml
import os

from .base_storage_handler import StorageHandler
from ..utils.database_schema import (
    db_creation,
    cleaned_job_table_creation,
    raw_job_table_creation,
    rejected_job_table_creation,
    validated_job_table_creation
)


load_dotenv()


class MySQLStorageHandler(StorageHandler):
    """
    MySQL Storage Handler for job data.

    Handles storage to raw_job_data / validated_job_data / etc. tables with
    proper error handling, connection management, and data serialization.
    """

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        database: str,
        table: str = "raw_job_data",
        port: int = 3306
    ):
        """
        Initialize MySQL Handler.

        Args:
            host: MySQL server host
            user: MySQL username
            password: MySQL password
            database: Database name
            table: Table name (default: raw_job_data)
            port: MySQL port (default: 3306)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.table = table
        self.port = port

        # Validate required parameters
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.host:
            logger.error("Host must not be empty.")
            raise ValueError("Host must not be empty!")
        if not self.user:
            logger.error("User name must not be empty.")
            raise ValueError("User must not be empty!")
        if not self.database:
            logger.error("Database name must not be empty.")
            raise ValueError("Database name must not be empty!")

    def _get_connection(self, use_database: bool = True) -> mysql.connector.connection.MySQLConnection:
        """
        Establish MySQL connection.

        Args:
            use_database: Whether to connect to specific database (False for initial setup)

        Returns:
            MySQL connection object
        """
        try:
            conn_config = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'password': self.password
            }

            if use_database:
                conn_config['database'] = self.database

            conn = mysql.connector.connect(**conn_config)

            if not conn.is_connected():
                logger.error("Failed to establish MySQL connection")
                raise Error("Connection failed")

            logger.debug(f"Successfully connected to MySQL at {self.host}:{self.port}")
            return conn

        except Error as e:
            logger.error(f"MySQL connection error: {e}")
            raise

    def _check_database_exists(self, cursor) -> bool:
        """Check if database exists."""
        try:
            query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s"
            cursor.execute(query, (self.database,))
            exists = cursor.fetchone() is not None
            logger.debug(f"Database '{self.database}' exists: {exists}")
            return exists
        except Error as e:
            logger.error(f"Error checking database existence: {e}")
            return False

    def _check_table_exists(self, cursor) -> bool:
        """Check if table exists in database."""
        try:
            query = """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
            """
            cursor.execute(query, (self.database, self.table))
            exists = cursor.fetchone()[0] == 1
            logger.debug(f"Table '{self.table}' exists: {exists}")
            return exists
        except Error as e:
            logger.error(f"Error checking table existence: {e}")
            return False

    def _create_database(self, cursor) -> None:
        """Create database if it doesn't exist."""
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' created successfully")
        except Error as e:
            logger.error(f"Error creating database: {e}")
            raise

    def _create_table(self, cursor) -> None:
        """Create table based on table name."""
        try:
            table_creation_map = {
                'raw_job_data': raw_job_table_creation,
                'validated_job_data': validated_job_table_creation,
                'rejected_job_data': rejected_job_table_creation,
                'cleaned_job_data': cleaned_job_table_creation
            }

            creation_script = table_creation_map.get(self.table, raw_job_table_creation)
            cursor.execute(creation_script)
            logger.info(f"Table '{self.table}' created successfully")
        except Error as e:
            logger.error(f"Error creating table: {e}")
            raise

    def _serialize_skills(self, skills: Any) -> str:
        """
        Convert skills list to JSON string for storage.
        """
        if skills is None:
            return "[]"
        if isinstance(skills, list):
            return json.dumps(skills)
        if isinstance(skills, str):
            return skills
        return json.dumps([str(skills)])

    def _prepare_job_data(self, job_data: Dict[str, Any]) -> tuple:
        """
        Prepare job data tuple for insertion.
        """
        star_skills = self._serialize_skills(job_data.get("Star_Skills", []))
        normal_skills = self._serialize_skills(job_data.get("Normal_Skills", []))

        return (
            job_data.get("Job_ID", "NA"),
            job_data.get("Title", "NA"),
            job_data.get("Company", "NA"),
            job_data.get("Experience", "NA"),
            job_data.get("Salary", "NA"),
            job_data.get("Location", "NA"),
            job_data.get("Education", "NA"),
            star_skills,
            normal_skills,
            job_data.get("Posted_Date", "NA"),
            job_data.get("Last_Apply_Date", "NA"),
            job_data.get("num_openings"),
            job_data.get("num_applicants"),
            job_data.get("Role", "NA"),
            job_data.get("Industry_Type", "NA"),
            job_data.get("Department", "NA"),
            job_data.get("Employment_Type", "NA"),
            job_data.get("Role_Category", "NA"),
            job_data.get("Job_Type", "NA"),
            job_data.get("Description", "NA"),
            job_data.get("Job_URL", ""),
            job_data.get("Scraped_At", "")
        )

    def save(self, dataset: List[Dict[str, Any]], filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Save job data to MySQL database.

        Returns:
            Dict with save statistics
        """
        if not dataset:
            logger.warning("Empty dataset provided, nothing to save")
            return {
                "success": False,
                "total_jobs": 0,
                "inserted": 0,
                "duplicates": 0,
                "errors": 0
            }

        stats = {
            "success": False,
            "total_jobs": len(dataset),
            "inserted": 0,
            "duplicates": 0,
            "errors": 0,
            "error_details": []
        }

        conn = None
        cursor = None

        try:
            # Connect without database to check/create it
            conn = self._get_connection(use_database=False)
            cursor = conn.cursor()

            if not self._check_database_exists(cursor):
                logger.info(f"Database '{self.database}' does not exist, creating...")
                self._create_database(cursor)
                conn.commit()

            cursor.close()
            conn.close()

            # Reconnect with database selected
            conn = self._get_connection(use_database=True)
            cursor = conn.cursor()

            if not self._check_table_exists(cursor):
                logger.info(f"Table '{self.table}' does not exist, creating...")
                self._create_table(cursor)
                conn.commit()

            # Prepare insertion query (ON DUPLICATE KEY UPDATE)
            insert_query = f"""INSERT INTO {self.table} (
                job_id, title, company, experience, salary, location, education,
                star_skills, normal_skills, posted_date, last_apply_date,
                num_openings, num_applicants, role, industry_type, department,
                employment_type, role_category, job_type, description, job_url, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON DUPLICATE KEY UPDATE
                num_applicants = VALUES(num_applicants),
                num_openings   = VALUES(num_openings),
                last_apply_date = VALUES(last_apply_date),
                scraped_at     = VALUES(scraped_at)
            """

            for idx, job_data in enumerate(dataset):
                try:
                    job_tuple = self._prepare_job_data(job_data)
                    cursor.execute(insert_query, job_tuple)
                    stats["inserted"] += 1

                    if (idx + 1) % 100 == 0:
                        conn.commit()
                        logger.info(f"Committed batch: {idx + 1}/{len(dataset)} jobs")

                except mysql.connector.IntegrityError as e:
                    stats["duplicates"] += 1
                    logger.debug(f"Duplicate job URL: {job_data.get('Job_URL', 'Unknown')}")

                except Error as e:
                    stats["errors"] += 1
                    error_msg = f"Job {idx}: {str(e)[:100]}"
                    stats["error_details"].append(error_msg)
                    logger.error(f"Error inserting job {idx}: {e}")

            conn.commit()
            stats["success"] = True

            logger.info(
                f"Save completed → Inserted: {stats['inserted']}, "
                f"Duplicates: {stats['duplicates']}, Errors: {stats['errors']}"
            )

        except Error as e:
            logger.error(f"Critical error during save operation: {e}")
            if conn:
                conn.rollback()
            stats["success"] = False
            stats["error_details"].append(f"Critical error: {str(e)}")

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                logger.debug("MySQL connection closed")

        return stats

    def fetch_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from database.
        """
        conn = None
        cursor = None
        jobs = []

        try:
            conn = self._get_connection(use_database=True)
            cursor = conn.cursor(dictionary=True)

            query = f"SELECT * FROM {self.table}"
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            jobs = cursor.fetchall()

            # Deserialize JSON fields
            for job in jobs:
                for field in ['star_skills', 'normal_skills']:
                    if field in job and job[field]:
                        try:
                            job[field] = json.loads(job[field])
                        except json.JSONDecodeError:
                            job[field] = []

            logger.info(f"Fetched {len(jobs)} jobs from {self.table}")

        except Error as e:
            logger.error(f"Error fetching data: {e}")

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        return jobs

    def clear_table(self) -> bool:
        """
        Clear all data from table (use with caution).
        """
        conn = None
        cursor = None

        try:
            conn = self._get_connection(use_database=True)
            cursor = conn.cursor()

            cursor.execute(f"TRUNCATE TABLE {self.table}")
            conn.commit()

            logger.warning(f"Table '{self.table}' has been cleared")
            return True

        except Error as e:
            logger.error(f"Error clearing table: {e}")
            if conn:
                conn.rollback()
            return False

        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    def get_name(self) -> str:
        return "MySQLStorageHandler"


# ─── Standalone testing / development ───────────────────────────────────────────
if __name__ == "__main__":
    # ─── Initialize central logging first ───
    setup_logging()

    # Optional: quick diagnostic (remove later)
    logger.debug("Logger diagnostic in mysql_storage_handler.py")
    logger.info(f"Logger name: {logger.name}")
    logger.debug(f"Handlers attached: {[h.__class__.__name__ for h in logger.handlers]}")

    # Load config
    config_path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\config\config.yml"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        database_config = config["database"]
    except Exception as e:
        logger.error(f"Failed to load config file: {e}")
        raise

    # Get credentials (prefer env vars when placeholder is used)
    host = database_config["host"]
    user = os.getenv("DB_USER") if database_config.get('user') == '${DB_USER}' else database_config['user']
    password = os.getenv("DB_PASSWORD") if database_config.get('password') == '${DB_PASSWORD}' else database_config['password']
    database = database_config["database"]
    table = database_config.get("raw_job_data", "raw_job_data")  # fallback

    # Initialize handler
    handler = MySQLStorageHandler(
        host=host,
        user=user,
        password=password,
        database=database,
        table=table,
        port=3306
    )

    # Sample data
    sample_jobs = [
        {
            "Job_ID": 4511587,
            "Title": "Python Developer - Fresher",
            "Company": "TCS",
            "Experience": "0-1 Yrs",
            "Salary": "3-5 Lacs P.A.",
            "Location": "Bengaluru",
            "Education": "B.Tech/B.E.",
            "Star_Skills": ["Python", "Django", "SQL"],
            "Normal_Skills": ["Git", "REST API"],
            "Posted_Date": "2 Days Ago",
            "Last_Apply_Date": "15 Feb 2026",
            "Role": "Software Development",
            "Industry_Type": "IT Services",
            "Department": "Engineering",
            "Employment_Type": "Full Time",
            "Role_Category": "Programming",
            "Job_Type": "python-developer",
            "Description": "Looking for fresh graduates...",
            "Job_URL": "https://example.com/job1",
            "Scraped_At": "2026-01-26T10:30:00",
            "num_openings": 5,
            "num_applicants": 120
        }
    ]

    # Save
    result = handler.save(sample_jobs)
    print("\nSave Results:")
    print(f"  Success:     {result['success']}")
    print(f"  Inserted:    {result['inserted']}")
    print(f"  Duplicates:  {result['duplicates']}")
    print(f"  Errors:      {result['errors']}")

    # Fetch some data to verify
    jobs = handler.fetch_all(limit=5)
    print(f"\nFetched {len(jobs)} jobs from database")