"""
PostgreSQL Data Ingestor for Job Trend Predictor
Handles database connections and data retrieval for production deployment

Author: Development Team
Date: 2025-03-18
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, List, Any, Optional
import logging
from abc import ABC, abstractmethod

# Import existing DataIngestor
from .ingest_data import DataIngestor

logger = logging.getLogger(__name__)


class PostgreSQLConfig:
    """PostgreSQL configuration management"""
    
    def __init__(self):
        # Check for Neon URL first (serverless PostgreSQL)
        neon_url = os.getenv('NEON_URL')
        if neon_url:
            self.connection_string = neon_url
            self.use_neon = True
            logger.info("Using Neon PostgreSQL connection")
        else:
            self.use_neon = False
            self.host = os.getenv('DB_HOST', 'localhost')
            self.port = os.getenv('DB_PORT', '5432')
            self.database = os.getenv('DB_NAME', 'job_trend_predictor')
            self.username = os.getenv('DB_USER', 'postgres')
            self.password = os.getenv('DB_PASSWORD', '')
            self.sslmode = os.getenv('DB_SSLMODE', 'require')
            logger.info("Using standard PostgreSQL connection")
    
    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        if self.use_neon:
            return self.connection_string
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_connection_params(self) -> Dict:
        """Get connection parameters for psycopg2"""
        if self.use_neon:
            return {'dsn': self.connection_string}
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.username,
            'password': self.password,
            'sslmode': self.sslmode
        }


class PostgreSQLIngestor(DataIngestor):
    """PostgreSQL data ingestor for production deployment"""
    
    def __init__(self, config: Optional[PostgreSQLConfig] = None):
        self.config = config or PostgreSQLConfig()
        self.connection = None
    
    def _get_connection(self):
        """Establish database connection"""
        try:
            if self.connection is None or self.connection.closed:
                self.connection = psycopg2.connect(**self.config.get_connection_params())
                logger.info("PostgreSQL connection established")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {str(e)}")
            raise
    
    def ingest(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute query and return results as DataFrame"""
        try:
            conn = self._get_connection()
            
            # Execute query
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            
            logger.info(f"Retrieved {len(df)} records from PostgreSQL")
            return df
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def get_job_data(self, limit: Optional[int] = None, 
                     where_clause: Optional[str] = None) -> pd.DataFrame:
        """Get job data from PostgreSQL"""
        query = """
        SELECT 
            job_type as "Job_Type",
            skills as "Skills",
            min_experience as "Min_Experience",
            max_experience as "Max_Experience",
            location as "Location",
            salary_lakhs as "Salary_Lakhs",
            company as "Company",
            posted_date as "Posted_Date",
            no_of_applicants as "No of applicant applied cleaned",
            no_of_openings as "No of job opening cleaned "
        FROM job_listings
        """
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        return self.ingest(query)
    
    def get_job_data_by_domain(self, domain: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Get job data filtered by domain"""
        where_clause = "LOWER(job_type) = LOWER(%s)"
        params = (domain,)
        
        query = f"""
        SELECT 
            job_type as "Job_Type",
            skills as "Skills",
            min_experience as "Min_Experience",
            max_experience as "Max_Experience",
            location as "Location",
            salary_lakhs as "Salary_Lakhs",
            company as "Company",
            posted_date as "Posted_Date",
            no_of_applicants as "No of applicant applied cleaned",
            no_of_openings as "No of job opening cleaned "
        FROM job_listings
        WHERE LOWER(job_type) = LOWER(%s)
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            conn = self._get_connection()
            df = pd.read_sql_query(query, conn, params=params)
            logger.info(f"Retrieved {len(df)} records for domain: {domain}")
            return df
        except Exception as e:
            logger.error(f"Error getting job data for domain {domain}: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def get_domains(self) -> List[str]:
        """Get all unique job domains"""
        query = "SELECT DISTINCT job_type FROM job_listings ORDER BY job_type"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            domains = [row['job_type'] for row in cursor.fetchall()]
            logger.info(f"Retrieved {len(domains)} unique domains")
            return domains
        except Exception as e:
            logger.error(f"Error getting domains: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT job_type) as unique_domains,
            COUNT(DISTINCT location) as unique_locations,
            AVG(salary_lakhs) as avg_salary,
            MIN(salary_lakhs) as min_salary,
            MAX(salary_lakhs) as max_salary,
            MEDIAN(salary_lakhs) as median_salary
        FROM job_listings
        """
        
        domain_dist_query = """
        SELECT job_type, COUNT(*) as count
        FROM job_listings
        GROUP BY job_type
        ORDER BY count DESC
        """
        
        location_dist_query = """
        SELECT location, COUNT(*) as count
        FROM job_listings
        GROUP BY location
        ORDER BY count DESC
        """
        
        try:
            conn = self._get_connection()
            
            # Get main stats
            stats_df = pd.read_sql_query(stats_query, conn)
            
            # Get domain distribution
            domain_df = pd.read_sql_query(domain_dist_query, conn)
            
            # Get location distribution
            location_df = pd.read_sql_query(location_dist_query, conn)
            
            stats = {
                'total_records': int(stats_df['total_records'].iloc[0]),
                'unique_domains': int(stats_df['unique_domains'].iloc[0]),
                'unique_locations': int(stats_df['unique_locations'].iloc[0]),
                'salary_stats': {
                    'mean': float(stats_df['avg_salary'].iloc[0]),
                    'min': float(stats_df['min_salary'].iloc[0]),
                    'max': float(stats_df['max_salary'].iloc[0]),
                    'median': float(stats_df['median_salary'].iloc[0])
                },
                'job_types': domain_df.set_index('job_type')['count'].to_dict(),
                'location_distribution': location_df.set_index('location')['count'].to_dict()
            }
            
            logger.info("Retrieved database statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info("Database connection test successful")
            return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None


class DatabaseIngestionFactory:
    """Extended factory to include database ingestors"""
    
    @staticmethod
    def get_ingestor(ingestor_type: str, **kwargs) -> DataIngestor:
        """Get appropriate ingestor based on type"""
        if ingestor_type == 'csv':
            from .ingest_data import CSVIngestor
            return CSVIngestor()
        elif ingestor_type == 'json':
            from .ingest_data import JSONIngestor
            return JSONIngestor()
        elif ingestor_type == 'excel':
            from .ingest_data import ExcelIngestor
            return ExcelIngestor()
        elif ingestor_type == 'postgres':
            return PostgreSQLIngestor()
        else:
            raise ValueError(f"Unsupported ingestor type: {ingestor_type}")


# Example usage and testing
if __name__ == "__main__":
    # Test PostgreSQL connection
    try:
        ingestor = DatabaseIngestionFactory.get_ingestor('postgres')
        
        # Test connection
        if ingestor.test_connection():
            print("✅ PostgreSQL connection successful")
            
            # Get sample data
            sample_data = ingestor.get_job_data(limit=5)
            print(f"Sample data shape: {sample_data.shape}")
            print(f"Columns: {list(sample_data.columns)}")
            
            # Get domains
            domains = ingestor.get_domains()
            print(f"Available domains: {domains[:5]}...")
            
            # Get stats
            stats = ingestor.get_data_stats()
            print(f"Total records: {stats['total_records']}")
            
        else:
            print("❌ PostgreSQL connection failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
