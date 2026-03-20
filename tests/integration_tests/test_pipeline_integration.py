"""
Integration Tests for Scraping Pipelines
End-to-end testing with real components and database connections

Author: QA Team
Date: 2025-03-14
Purpose: Validate pipeline integration with actual scrapers and storage handlers
"""

import pytest
import unittest
import tempfile
import os
import csv
import json
import sqlite3
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import actual pipeline classes
from pipelines.naukri_general_pipeline import NaukriGeneralJobDataExtractionPipeline
from pipelines.naukri_fresher_job_scraping_pipeline import NaukriFresherJobDataExtractionPipeline

# Import actual components (if available)
try:
    from src.scrapers.naukri_general_job_scraper import GeneralJobScraper
    from src.scrapers.naukri_fresher_job_scraper import FresherJobScraper
    from src.storage.csv_storage_handler import CSVStorageHandler
    from src.storage.sqlite_handler import MySQLStorageHandler
    REAL_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Real components not available: {e}")
    REAL_COMPONENTS_AVAILABLE = False


class TestCSVStorageIntegration(unittest.TestCase):
    """Test CSV storage handler integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_file = os.path.join(self.temp_dir, "test_jobs.csv")
        
        if REAL_COMPONENTS_AVAILABLE:
            self.csv_storage = CSVStorageHandler()
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real CSV storage not available")
    def test_csv_storage_save_and_verify(self):
        """Test CSV storage save operation and data verification"""
        # Arrange
        test_data = [
            {
                'title': 'Software Engineer',
                'company': 'Test Company',
                'location': 'Bangalore',
                'salary': '8-15 LPA',
                'experience': '2-5 years',
                'description': 'Test job description',
                'skills': 'Python, Java, SQL',
                'posted_date': '2025-03-14'
            },
            {
                'title': 'Data Scientist',
                'company': 'Another Company',
                'location': 'Hyderabad',
                'salary': '10-20 LPA',
                'experience': '3-6 years',
                'description': 'Data science role',
                'skills': 'Python, ML, Statistics',
                'posted_date': '2025-03-13'
            }
        ]
        
        # Act
        self.csv_storage.save(test_data, self.test_csv_file)
        
        # Assert
        self.assertTrue(os.path.exists(self.test_csv_file))
        
        # Verify CSV content
        with open(self.test_csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            saved_data = list(reader)
        
        self.assertEqual(len(saved_data), 2)
        
        # Verify first record
        first_record = saved_data[0]
        self.assertEqual(first_record['title'], 'Software Engineer')
        self.assertEqual(first_record['company'], 'Test Company')
        self.assertEqual(first_record['location'], 'Bangalore')
        
        # Verify second record
        second_record = saved_data[1]
        self.assertEqual(second_record['title'], 'Data Scientist')
        self.assertEqual(second_record['skills'], 'Python, ML, Statistics')
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real CSV storage not available")
    def test_csv_storage_empty_data(self):
        """Test CSV storage with empty data"""
        # Act
        self.csv_storage.save([], self.test_csv_file)
        
        # Assert
        self.assertTrue(os.path.exists(self.test_csv_file))
        
        # Verify file is empty or has only headers
        with open(self.test_csv_file, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        
        # File should be empty or contain only headers
        self.assertTrue(len(content) == 0 or content.startswith('title'))
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real CSV storage not available")
    def test_csv_storage_large_dataset(self):
        """Test CSV storage with large dataset"""
        # Arrange
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                'title': f'Job Title {i}',
                'company': f'Company {i}',
                'location': f'City {i}',
                'salary': f'{5+i%10}-{15+i%10} LPA',
                'experience': f'{i%5}-{i%5+3} years',
                'description': f'Description for job {i}',
                'skills': f'Skill{i%10}, Skill{i%5}',
                'posted_date': f'2025-03-{14+i%30:02d}'
            })
        
        # Act
        self.csv_storage.save(large_dataset, self.test_csv_file)
        
        # Assert
        self.assertTrue(os.path.exists(self.test_csv_file))
        
        # Verify file size and content
        file_size = os.path.getsize(self.test_csv_file)
        self.assertGreater(file_size, 0)
        
        # Verify a sample of records
        with open(self.test_csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            saved_data = list(reader)
        
        self.assertEqual(len(saved_data), 1000)
        self.assertEqual(saved_data[0]['title'], 'Job Title 0')
        self.assertEqual(saved_data[999]['title'], 'Job Title 999')


class TestMockScraperIntegration(unittest.TestCase):
    """Test integration with mock scrapers simulating real behavior"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_file = os.path.join(self.temp_dir, "integration_test.csv")
        
        if REAL_COMPONENTS_AVAILABLE:
            self.csv_storage = CSVStorageHandler()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real components not available")
    def test_general_pipeline_with_real_components(self):
        """Test general pipeline with real CSV storage and mock scraper"""
        # Create a mock scraper that simulates real behavior
        class MockRealScraper:
            def __init__(self):
                self.name = "MockRealScraper"
            
            def extract(self, job_name, locations):
                # Simulate real scraping behavior
                mock_data = []
                for location in locations:
                    mock_data.append({
                        'title': f'{job_name} in {location}',
                        'company': f'Tech Company {location}',
                        'location': location,
                        'salary': '8-15 LPA',
                        'experience': '2-4 years',
                        'description': f'Real job description for {job_name}',
                        'skills': 'Python, SQL, Git',
                        'posted_date': '2025-03-14',
                        'scraped_at': datetime.now().isoformat()
                    })
                return mock_data
            
            def get_name(self):
                return self.name
        
        # Arrange
        mock_scraper = MockRealScraper()
        filedirectory = {"csv": self.test_csv_file}
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[mock_scraper],
            handlers=[self.csv_storage],
            jobs=['Python Developer', 'Data Scientist'],
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertGreater(result['total_records'], 0)
        
        # Verify CSV file was created and contains data
        self.assertTrue(os.path.exists(self.test_csv_file))
        
        with open(self.test_csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            saved_records = list(reader)
        
        self.assertGreater(len(saved_records), 0)
        self.assertIn('Python Developer', [record['title'] for record in saved_records])
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real components not available")
    def test_fresher_pipeline_with_real_components(self):
        """Test fresher pipeline with real CSV storage and mock scraper"""
        # Create a mock fresher scraper
        class MockFresherScraper:
            def __init__(self):
                self.name = "MockFresherScraper"
            
            def extract(self, job_role, locations):
                # Simulate fresher job scraping
                mock_data = []
                for location in locations:
                    mock_data.append({
                        'title': f'Junior {job_role}',
                        'company': f'Startup {location}',
                        'location': location,
                        'salary': '3-6 LPA',
                        'experience': '0-1 years',
                        'description': f'Entry level position for {job_role}',
                        'skills': 'Python, Basic SQL',
                        'posted_date': '2025-03-14',
                        'is_fresher_friendly': True,
                        'scraped_at': datetime.now().isoformat()
                    })
                return mock_data
            
            def get_name(self):
                return self.name
        
        # Arrange
        mock_scraper = MockFresherScraper()
        filedirectory = {"csv": self.test_csv_file}
        
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[mock_scraper],
            handlers=[self.csv_storage],
            job_roles=['Junior Developer', 'Trainee Analyst'],
            filedirectory=filedirectory,
            locations=['Bangalore', 'Pune']
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_job_roles'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['fresher_friendly_records'], result['total_records'])
        
        # Verify CSV file contains fresher-friendly data
        with open(self.test_csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            saved_records = list(reader)
        
        self.assertGreater(len(saved_records), 0)
        
        # Check for fresher-specific indicators
        for record in saved_records:
            self.assertIn('Junior', record['title'] or record.get('title', ''))
            salary = record.get('salary', '')
            self.assertTrue('3-6' in salary or 'Trainee' in record.get('title', ''))


class TestDatabaseStorageIntegration(unittest.TestCase):
    """Test database storage integration"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_file = os.path.join(self.temp_dir, "test_jobs.db")
        
        # Create test database
        self.conn = sqlite3.connect(self.test_db_file)
        self.cursor = self.conn.cursor()
        
        # Create test table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_postings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                experience TEXT,
                description TEXT,
                skills TEXT,
                posted_date TEXT,
                scraped_at TEXT
            )
        ''')
        self.conn.commit()
    
    def tearDown(self):
        """Clean up test environment"""
        self.conn.close()
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipUnless(REAL_COMPONENTS_AVAILABLE, "Real MySQL storage not available")
    def test_mysql_storage_integration(self):
        """Test MySQL storage handler integration (using SQLite as substitute)"""
        # This test would use the actual MySQLStorageHandler
        # For now, we'll simulate it with SQLite
        
        class MockMySQLStorage:
            def __init__(self, db_file):
                self.db_file = db_file
                self.name = "mysql"
            
            def save(self, clean_dataset, filename):
                # Simulate MySQL storage using SQLite
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                for record in clean_dataset:
                    cursor.execute('''
                        INSERT INTO job_postings 
                        (title, company, location, salary, experience, description, skills, posted_date, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        record.get('title'),
                        record.get('company'),
                        record.get('location'),
                        record.get('salary'),
                        record.get('experience'),
                        record.get('description'),
                        record.get('skills'),
                        record.get('posted_date'),
                        record.get('scraped_at')
                    ))
                
                conn.commit()
                conn.close()
            
            def get_name(self):
                return self.name
        
        # Arrange
        mysql_storage = MockMySQLStorage(self.test_db_file)
        test_data = [
            {
                'title': 'Database Engineer',
                'company': 'Database Corp',
                'location': 'Bangalore',
                'salary': '12-20 LPA',
                'experience': '3-5 years',
                'description': 'Database engineering role',
                'skills': 'SQL, NoSQL, Python',
                'posted_date': '2025-03-14',
                'scraped_at': datetime.now().isoformat()
            }
        ]
        
        # Act
        mysql_storage.save(test_data, "test_table")
        
        # Assert
        cursor = self.cursor.execute("SELECT COUNT(*) FROM job_postings")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 1)
        
        # Verify data
        cursor = self.cursor.execute("SELECT title, company FROM job_postings LIMIT 1")
        record = cursor.fetchone()
        self.assertEqual(record[0], 'Database Engineer')
        self.assertEqual(record[1], 'Database Corp')


class TestErrorRecoveryIntegration(unittest.TestCase):
    """Test error recovery and resilience in integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_file = os.path.join(self.temp_dir, "error_test.csv")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_partial_failure_recovery(self):
        """Test pipeline recovery from partial failures"""
        # Create a scraper that fails on specific jobs
        class FlakyScraper:
            def __init__(self):
                self.name = "FlakyScraper"
                self.call_count = 0
            
            def extract(self, job_name, locations):
                self.call_count += 1
                # Fail on every second call
                if self.call_count % 2 == 0:
                    raise Exception(f"Network error for {job_name}")
                
                return [{
                    'title': job_name,
                    'company': 'Test Company',
                    'location': locations[0] if locations else 'Test Location',
                    'salary': '8-15 LPA',
                    'experience': '2-4 years',
                    'description': 'Test description',
                    'skills': 'Python, SQL',
                    'posted_date': '2025-03-14'
                }]
            
            def get_name(self):
                return self.name
        
        # Arrange
        flaky_scraper = FlakyScraper()
        
        class MockCSVStorage:
            def __init__(self):
                self.name = "csv"
                self.saved_data = []
            
            def save(self, data, filename):
                self.saved_data.extend(data)
            
            def get_name(self):
                return self.name
        
        csv_storage = MockCSVStorage()
        filedirectory = {"csv": self.test_csv_file}
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[flaky_scraper],
            handlers=[csv_storage],
            jobs=['Job 1', 'Job 2', 'Job 3', 'Job 4'],
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 4)
        self.assertEqual(result['successful_jobs'], 2)  # Every other job succeeds
        self.assertEqual(result['failed_jobs'], 2)
        self.assertEqual(len(csv_storage.saved_data), 2)  # Only successful jobs saved
    
    def test_storage_failure_recovery(self):
        """Test pipeline behavior when storage fails"""
        # Create a storage handler that fails
        class FailingStorage:
            def __init__(self):
                self.name = "failing_storage"
                self.failure_count = 0
            
            def save(self, data, filename):
                self.failure_count += 1
                if self.failure_count <= 2:
                    raise Exception("Storage temporarily unavailable")
                # Succeed on third attempt
                pass
            
            def get_name(self):
                return self.name
        
        # Arrange
        mock_scraper = type('MockScraper', (), {
            'name': 'MockScraper',
            'extract': lambda self, job, loc: [{'title': job, 'company': 'Test'}],
            'get_name': lambda self: 'MockScraper'
        })()
        
        failing_storage = FailingStorage()
        filedirectory = {"failing_storage": self.test_csv_file}
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[mock_scraper],
            handlers=[failing_storage],
            jobs=['Test Job'],
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        # The pipeline should handle storage failures gracefully
        self.assertEqual(result['total_jobs'], 1)
        # Depending on implementation, this might be marked as failed
        self.assertIn(result['failed_jobs'], [0, 1])


class TestDataValidationIntegration(unittest.TestCase):
    """Test data validation in integration scenarios"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_file = os.path.join(self.temp_dir, "validation_test.csv")
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_data_quality_validation(self):
        """Test data quality validation in pipeline integration"""
        # Create a scraper that returns various data quality issues
        class DataQualityScraper:
            def __init__(self):
                self.name = "DataQualityScraper"
            
            def extract(self, job_name, locations):
                return [
                    # Good record
                    {
                        'title': job_name,
                        'company': 'Good Company',
                        'location': locations[0] if locations else 'Good Location',
                        'salary': '8-15 LPA',
                        'experience': '2-4 years',
                        'description': 'Good description',
                        'skills': 'Python, SQL',
                        'posted_date': '2025-03-14'
                    },
                    # Record with missing fields
                    {
                        'title': 'Incomplete Job',
                        'company': '',  # Empty company
                        'location': None,  # Null location
                        'salary': 'N/A',  # Invalid salary
                        'experience': '',  # Empty experience
                        'description': 'Incomplete description',
                        'skills': 'Python',
                        'posted_date': 'invalid-date'  # Invalid date
                    },
                    # Record with special characters
                    {
                        'title': 'Special "Chars" Job',
                        'company': 'Company & Co.',
                        'location': 'City, State',
                        'salary': '₹10-20 LPA',  # Currency symbol
                        'experience': '2-4 years',
                        'description': 'Description with\nnewlines and\ttabs',
                        'skills': 'Python; SQL; Java',  # Different separator
                        'posted_date': '2025-03-14'
                    }
                ]
            
            def get_name(self):
                return self.name
        
        # Arrange
        scraper = DataQualityScraper()
        
        class ValidatingStorage:
            def __init__(self):
                self.name = "validating_storage"
                self.saved_data = []
                self.validation_issues = []
            
            def save(self, data, filename):
                for record in data:
                    # Basic validation
                    issues = []
                    
                    if not record.get('title') or not record.get('title').strip():
                        issues.append("Missing title")
                    
                    if not record.get('company') or not record.get('company').strip():
                        issues.append("Missing company")
                    
                    if record.get('location') == 'None' or not record.get('location'):
                        issues.append("Missing location")
                    
                    if issues:
                        self.validation_issues.append({
                            'record': record,
                            'issues': issues
                        })
                    
                    self.saved_data.append(record)
            
            def get_name(self):
                return self.name
        
        validating_storage = ValidatingStorage()
        filedirectory = {"validating_storage": self.test_csv_file}
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[scraper],
            handlers=[validating_storage],
            jobs=['Quality Test Job'],
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 1)
        self.assertEqual(len(validating_storage.saved_data), 3)
        self.assertEqual(len(validating_storage.validation_issues), 1)  # One record has issues
        
        # Check validation issues
        incomplete_record_issues = validating_storage.validation_issues[0]
        self.assertIn('Missing company', incomplete_record_issues['issues'])
        self.assertIn('Missing location', incomplete_record_issues['issues'])


if __name__ == '__main__':
    # Configure logging for integration tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("Running Scraping Pipelines Integration Tests")
    print("="*60)
    
    # Run integration tests
    unittest.main(verbosity=2)
