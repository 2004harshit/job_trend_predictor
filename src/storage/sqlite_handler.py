# import mysql.connector
# from mysql.connector import Error
# import logging
# from .base_storage_handler import StorageHandler
# from ..utils.database_schema import db_creation, cleaned_job_table_creation,raw_job_table_creation,rejected_job_table_creation,validated_job_table_creation

# class MySQLHandler(StorageHandler):
#     def __init__(self, host,user, password,database,table,port):
#         self.host = host,
#         self.user = user
#         self.password = password
#         self.database = database
#         self.table = table
#         self.port = port 
#         self.logger = logging.getLogger("MySQLHandler")

#     def _get_connection(self):

#         if not self.host:
#              self.logger.error("Host must not be empty. Please provide valid host.")
#              raise ValueError("Host must not be empty!")
#         if not self.user:
#              self.logger.error("User name must not be empty! please provide a valid user name")
#              raise ValueError("User must not be empty!")
#         if not self.database:
#              self.logger.error("Database must not be empty! please provide a valid database")
#              raise ValueError("Database name must not be empty!")
        
#         conn = mysql.connector.connect(
#         host = self.host
#         port = self.port,
#         password = self.password
#         user = self.user
#         )

#         if not conn.is_connected():
#              self.error("Connection error occurred !")
#              raise Error
#         return conn
        
#     def _check_database_exists(self , cursor):
#         query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s"
#         cursor.execute(query, (self.database,))
#         return cursor.fetchone() is not None
    
#     def _check_table_exists(self, cursor):
#         query = """
#             SELECT COUNT(*) 
#             FROM INFORMATION_SCHEMA.TABLES 
#             WHERE TABLE_SCHEMA = %s 
#             AND TABLE_NAME = %s
#         """
#         cursor.execute(query, (self.database,self.table))

#         # Returns 1 if exists, 0 if not
#         return cursor.fetchone()[0] == 1
    
#     def save(self, clean_dataset, filename):
#         job_list = [(job_data_point["Title"],job_data_point["Company"],job_data_point["Experience"],job_data_point["Salary"],job_data_point["Location"],job_data_point["Education"],job_data_point["Star_Skills"],job_data_point["Normal_Skills"], job_data_point["Posted_Date"], job_data_point["Last_Apply_Date"],job_data_point["Role"],job_data_point["Industry_Type"],job_data_point["Department"],job_data_point["Employment_Type"],job_data_point["Role_Category"],job_data_point["Description"],job_data_point["Job_URL"],job_data_point["Scraped_At"],job_data_point["Job_Type"],job_data_point["num_openings"],job_data_point["num_applicants"]) for job_data_point in clean_dataset]
#         try:
#             conn = self._get_connection()
#             cursor = conn.cursor()

#             # check database exist or not 
#             if not self._check_database_exist(cursor):
#                 # create database
#                 cursor.execute(db_creation)
                

#             cursor.execute("USE DATABASE %s",(self.database,))

#             # check if table exist or not
#             if not self._check_table_exists(cursor):
#                 # create table
#                 cursor.execute(raw_job_table_creation)
                
#         #    inserting data into table
#             query = """INSERT INTO jobs (Title, Company, Experience, Salary, Location, Education, Star_Skills, Normal_Skills, Posted_Date, Last_Apply_Date, Role, Industry_Type, Department, Employment_Type, Role_Category, Description, Job_URL, Scraped_At, Job_Type, num_openings, num_applicants)    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
#             cursor.executemany(query , job_list)
#             conn.commit()
#         except mysql.connector.IntegrityError as err:
#             print(f"Duplicate entries or constraint voilation: {err}")
#             conn.rollback()
#         except Error as e:
#             print(f"Error : {e}")
#             conn.rollback()
#         finally:
#             cursor.close()
#             conn.close()



import mysql.connector
from mysql.connector import Error
import logging
import json
from typing import List, Dict, Any, Optional
from .base_storage_handler import StorageHandler
from ..utils.database_schema import (
    db_creation, 
    cleaned_job_table_creation,
    raw_job_table_creation,
    rejected_job_table_creation,
    validated_job_table_creation
)


class MySQLHandler(StorageHandler):
    """
    MySQL Storage Handler for job data.
    
    Handles storage to raw_job_data table with proper error handling,
    connection management, and data serialization.
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
        self.logger = logging.getLogger("MySQLHandler")
        
        # Validate required parameters
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if not self.host:
            self.logger.error("Host must not be empty.")
            raise ValueError("Host must not be empty!")
        if not self.user:
            self.logger.error("User name must not be empty.")
            raise ValueError("User must not be empty!")
        if not self.database:
            self.logger.error("Database name must not be empty.")
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
                self.logger.error("Failed to establish MySQL connection")
                raise Error("Connection failed")
            
            self.logger.debug(f"Successfully connected to MySQL at {self.host}:{self.port}")
            return conn
            
        except Error as e:
            self.logger.error(f"MySQL connection error: {e}")
            raise

    def _check_database_exists(self, cursor) -> bool:
        """Check if database exists."""
        try:
            query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s"
            cursor.execute(query, (self.database,))
            exists = cursor.fetchone() is not None
            self.logger.debug(f"Database '{self.database}' exists: {exists}")
            return exists
        except Error as e:
            self.logger.error(f"Error checking database existence: {e}")
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
            self.logger.debug(f"Table '{self.table}' exists: {exists}")
            return exists
        except Error as e:
            self.logger.error(f"Error checking table existence: {e}")
            return False

    def _create_database(self, cursor) -> None:
        """Create database if it doesn't exist."""
        try:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            self.logger.info(f"Database '{self.database}' created successfully")
        except Error as e:
            self.logger.error(f"Error creating database: {e}")
            raise

    def _create_table(self, cursor) -> None:
        """Create table based on table name."""
        try:
            # Select appropriate table creation script
            table_creation_map = {
                'raw_job_data': raw_job_table_creation,
                'validated_job_data': validated_job_table_creation,
                'rejected_job_data': rejected_job_table_creation,
                'cleaned_job_data': cleaned_job_table_creation
            }
            
            creation_script = table_creation_map.get(self.table, raw_job_table_creation)
            cursor.execute(creation_script)
            self.logger.info(f"Table '{self.table}' created successfully")
        except Error as e:
            self.logger.error(f"Error creating table: {e}")
            raise

    def _serialize_skills(self, skills: Any) -> str:
        """
        Convert skills list to JSON string for storage.
        
        Args:
            skills: List of skills or string
            
        Returns:
            JSON string representation
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
        
        Args:
            job_data: Dictionary containing job information
            
        Returns:
            Tuple of values in correct order for SQL insertion
        """
        # Serialize list fields to JSON
        star_skills = self._serialize_skills(job_data.get("Star_Skills", []))
        normal_skills = self._serialize_skills(job_data.get("Normal_Skills", []))
        
        return (
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
        
        Args:
            dataset: List of job dictionaries
            filename: Optional filename (not used for MySQL, kept for interface compatibility)
            
        Returns:
            Dict with save statistics
        """
        if not dataset:
            self.logger.warning("Empty dataset provided, nothing to save")
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
            # Step 1: Connect without database to check/create it
            conn = self._get_connection(use_database=False)
            cursor = conn.cursor()

            # Step 2: Check and create database if needed
            if not self._check_database_exists(cursor):
                self.logger.info(f"Database '{self.database}' does not exist, creating...")
                self._create_database(cursor)
                conn.commit()

            # Step 3: Close and reconnect with database selected
            cursor.close()
            conn.close()
            
            conn = self._get_connection(use_database=True)
            cursor = conn.cursor()

            # Step 4: Check and create table if needed
            if not self._check_table_exists(cursor):
                self.logger.info(f"Table '{self.table}' does not exist, creating...")
                self._create_table(cursor)
                conn.commit()

            # Step 5: Prepare insertion query
            insert_query = """
                INSERT INTO raw_job_data (
                    title, company, experience, salary, location, education,
                    star_skills, normal_skills, posted_date, last_apply_date,
                    num_openings, num_applicants, role, industry_type, department,
                    employment_type, role_category, job_type, description, job_url, scraped_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            # Step 6: Insert data with individual error handling
            for idx, job_data in enumerate(dataset):
                try:
                    job_tuple = self._prepare_job_data(job_data)
                    cursor.execute(insert_query, job_tuple)
                    stats["inserted"] += 1
                    
                    # Commit in batches of 100
                    if (idx + 1) % 100 == 0:
                        conn.commit()
                        self.logger.info(f"Committed batch: {idx + 1}/{len(dataset)} jobs")
                        
                except mysql.connector.IntegrityError as e:
                    # Duplicate entry (job_url is UNIQUE)
                    stats["duplicates"] += 1
                    self.logger.debug(f"Duplicate job URL: {job_data.get('Job_URL', 'Unknown')}")
                    
                except Error as e:
                    stats["errors"] += 1
                    error_msg = f"Job {idx}: {str(e)[:100]}"
                    stats["error_details"].append(error_msg)
                    self.logger.error(f"Error inserting job {idx}: {e}")

            # Final commit
            conn.commit()
            stats["success"] = True
            
            self.logger.info(
                f"Save completed - Inserted: {stats['inserted']}, "
                f"Duplicates: {stats['duplicates']}, Errors: {stats['errors']}"
            )

        except Error as e:
            self.logger.error(f"Critical error during save operation: {e}")
            if conn:
                conn.rollback()
            stats["success"] = False
            stats["error_details"].append(f"Critical error: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                self.logger.debug("MySQL connection closed")

        return stats

    def get_name(self) -> str:
        """Return handler name."""
        return "MySQLHandler"

    def fetch_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all jobs from database.
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            List of job dictionaries
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
                if 'star_skills' in job and job['star_skills']:
                    try:
                        job['star_skills'] = json.loads(job['star_skills'])
                    except json.JSONDecodeError:
                        job['star_skills'] = []
                        
                if 'normal_skills' in job and job['normal_skills']:
                    try:
                        job['normal_skills'] = json.loads(job['normal_skills'])
                    except json.JSONDecodeError:
                        job['normal_skills'] = []

            self.logger.info(f"Fetched {len(jobs)} jobs from {self.table}")

        except Error as e:
            self.logger.error(f"Error fetching data: {e}")
            
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

        return jobs

    def clear_table(self) -> bool:
        """
        Clear all data from table (use with caution).
        
        Returns:
            True if successful, False otherwise
        """
        conn = None
        cursor = None

        try:
            conn = self._get_connection(use_database=True)
            cursor = conn.cursor()

            cursor.execute(f"TRUNCATE TABLE {self.table}")
            conn.commit()
            
            self.logger.warning(f"Table '{self.table}' has been cleared")
            return True

        except Error as e:
            self.logger.error(f"Error clearing table: {e}")
            if conn:
                conn.rollback()
            return False
            
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize handler
    handler = MySQLHandler(
        host="localhost",
        user="root",
        password="harshit",
        database="JOB_DATA_DB",
        table="raw_job_data",
        port=3306
    )
    
    # Sample data
    sample_jobs = [
        {
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
    
    # Save to database
    result = handler.save(sample_jobs)
    print(f"\nSave Results:")
    print(f"  Success: {result['success']}")
    print(f"  Inserted: {result['inserted']}")
    print(f"  Duplicates: {result['duplicates']}")
    print(f"  Errors: {result['errors']}")
    
    # Fetch data
    jobs = handler.fetch_all(limit=10)
    print(f"\nFetched {len(jobs)} jobs from database")