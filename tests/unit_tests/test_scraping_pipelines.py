"""
Comprehensive Unit Test Suite for Scraping Pipelines
QA Testing Implementation for Naukri General and Fresher Job Scraping Pipelines

Author: QA Team
Date: 2025-03-14
Coverage: Pipeline validation, error handling, integration testing
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from typing import List, Dict, Any
import tempfile
import os
import sys
import logging

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import pipeline classes
from .pipelines.naukri_general_pipeline import NaukriGeneralJobDataExtractionPipeline
from .pipelines.naukri_fresher_job_scraping_pipeline import NaukriFresherJobDataExtractionPipeline

# Import base classes
from src.scrapers.base_scraper import JobExtractor
from src.storage.base_storage_handler import StorageHandler


class MockJobExtractor(JobExtractor):
    """Mock implementation of JobExtractor for testing"""
    
    def __init__(self, name: str, should_fail: bool = False, empty_result: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.empty_result = empty_result
        self.extract_calls = []
        self.extract_call_count = 0
    
    def extract(self, job_name: str, locations: List[str]) -> List[Dict[str, str]]:
        """Mock extract method"""
        self.extract_calls.append((job_name, locations))
        self.extract_call_count += 1
        
        if self.should_fail:
            raise Exception(f"Mock extraction failed for {job_name}")
        
        if self.empty_result:
            return []
        
        # Return mock job data
        return [
            {
                'title': f'Mock {job_name} Position',
                'company': 'Mock Company',
                'location': locations[0] if locations else 'Mock Location',
                'salary': '5-10 LPA',
                'experience': '0-2 years',
                'description': 'Mock job description',
                'skills': 'Python, SQL',
                'posted_date': '2025-03-14'
            },
            {
                'title': f'Senior {job_name} Role',
                'company': 'Another Mock Company',
                'location': locations[1] if len(locations) > 1 else 'Mock Location 2',
                'salary': '8-15 LPA',
                'experience': '2-5 years',
                'description': 'Senior mock job description',
                'skills': 'Python, SQL, AWS',
                'posted_date': '2025-03-13'
            }
        ]
    
    def get_name(self) -> str:
        return self.name


class MockStorageHandler(StorageHandler):
    """Mock implementation of StorageHandler for testing"""
    
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.saved_data = []
        self.save_calls = []
        self.save_call_count = 0
    
    def save(self, clean_dataset: List[Dict], filename: str) -> None:
        """Mock save method"""
        self.save_calls.append((clean_dataset, filename))
        self.save_call_count += 1
        
        if self.should_fail:
            raise Exception(f"Mock save failed for {filename}")
        
        self.saved_data.extend(clean_dataset)
    
    def get_name(self) -> str:
        return self.name
    
    def get_saved_data(self) -> List[Dict]:
        """Helper method to retrieve saved data for verification"""
        return self.saved_data


class TestNaukriGeneralPipeline(unittest.TestCase):
    """Test cases for Naukri General Job Scraping Pipeline"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_extractor = MockJobExtractor("MockExtractor")
        self.mock_storage = MockStorageHandler("MockStorage")
        self.jobs = ["Python Developer", "Data Scientist"]
        self.filedirectory = {"MockStorage": "test_output.csv"}
        
        self.pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[self.mock_storage],
            jobs=self.jobs,
            filedirectory=self.filedirectory
        )
    
    def test_pipeline_initialization_success(self):
        """Test successful pipeline initialization"""
        # Assert
        self.assertEqual(len(self.pipeline.extractors), 1)
        self.assertEqual(len(self.pipeline.handlers), 1)
        self.assertEqual(len(self.pipeline.jobs), 2)
        self.assertEqual(self.pipeline.filedirectory, self.filedirectory)
    
    def test_pipeline_initialization_missing_extractors(self):
        """Test pipeline initialization failure with no extractors"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            NaukriGeneralJobDataExtractionPipeline(
                extractors=[],
                handlers=[self.mock_storage],
                jobs=self.jobs,
                filedirectory=self.filedirectory
            )
        
        self.assertIn("At least one extractor is required", str(context.exception))
    
    def test_pipeline_initialization_missing_handlers(self):
        """Test pipeline initialization failure with no handlers"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            NaukriGeneralJobDataExtractionPipeline(
                extractors=[self.mock_extractor],
                handlers=[],
                jobs=self.jobs,
                filedirectory=self.filedirectory
            )
        
        self.assertIn("Atleast one storage handler is required", str(context.exception))
    
    def test_pipeline_initialization_missing_jobs(self):
        """Test pipeline initialization failure with no jobs"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            NaukriGeneralJobDataExtractionPipeline(
                extractors=[self.mock_extractor],
                handlers=[self.mock_storage],
                jobs=[],
                filedirectory=self.filedirectory
            )
        
        self.assertIn("Atleast one job is required", str(context.exception))
    
    def test_pipeline_initialization_missing_filedirectory(self):
        """Test pipeline initialization failure with missing file directory"""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            NaukriGeneralJobDataExtractionPipeline(
                extractors=[self.mock_extractor],
                handlers=[self.mock_storage],
                jobs=self.jobs,
                filedirectory={}
            )
        
        self.assertIn("Missing file path for handler", str(context.exception))
    
    def test_pipeline_run_success(self):
        """Test successful pipeline execution"""
        # Act
        result = self.pipeline.run()
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 4)  # 2 jobs × 2 records each
        self.assertIn('job_details', result)
        self.assertIn('start_time', result)
        self.assertIn('execution_time_seconds', result)
        
        # Verify extractor was called for each job
        self.assertEqual(self.mock_extractor.extract_call_count, 2)
        self.assertEqual(len(self.mock_extractor.extract_calls), 2)
        
        # Verify storage was called
        self.assertEqual(self.mock_storage.save_call_count, 2)
        self.assertEqual(len(self.mock_storage.saved_data), 4)
    
    def test_pipeline_run_with_locations(self):
        """Test pipeline execution with location filtering"""
        # Arrange
        locations = ["Bangalore", "Hyderabad"]
        
        # Act
        result = self.pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 2)
        
        # Verify locations were passed to extractor
        for job_name, passed_locations in self.mock_extractor.extract_calls:
            self.assertEqual(passed_locations, locations)
    
    def test_pipeline_run_extractor_failure(self):
        """Test pipeline execution with extractor failure"""
        # Arrange
        failing_extractor = MockJobExtractor("FailingExtractor", should_fail=True)
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[failing_extractor],
            handlers=[self.mock_storage],
            jobs=self.jobs,
            filedirectory=self.filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 0)
        self.assertEqual(result['failed_jobs'], 2)
        
        # Verify extractor was called despite failures
        self.assertEqual(failing_extractor.extract_call_count, 2)
    
    def test_pipeline_run_storage_failure(self):
        """Test pipeline execution with storage failure"""
        # Arrange
        failing_storage = MockStorageHandler("FailingStorage", should_fail=True)
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[failing_storage],
            jobs=self.jobs,
            filedirectory={"FailingStorage": "test_output.csv"}
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 0)
        self.assertEqual(result['failed_jobs'], 2)
        
        # Verify extractor was called but storage failed
        self.assertEqual(self.mock_extractor.extract_call_count, 2)
        self.assertEqual(failing_storage.save_call_count, 2)
    
    def test_pipeline_run_empty_results(self):
        """Test pipeline execution with empty extraction results"""
        # Arrange
        empty_extractor = MockJobExtractor("EmptyExtractor", empty_result=True)
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[empty_extractor],
            handlers=[self.mock_storage],
            jobs=self.jobs,
            filedirectory=self.filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 2)  # Empty results are still successful
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 0)
    
    def test_pipeline_multiple_extractors(self):
        """Test pipeline with multiple extractors"""
        # Arrange
        extractor1 = MockJobExtractor("Extractor1")
        extractor2 = MockJobExtractor("Extractor2")
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[extractor1, extractor2],
            handlers=[self.mock_storage],
            jobs=self.jobs,
            filedirectory=self.filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['total_records'], 8)  # 2 jobs × 2 extractors × 2 records each
        
        # Verify both extractors were called
        self.assertEqual(extractor1.extract_call_count, 2)
        self.assertEqual(extractor2.extract_call_count, 2)
    
    def test_pipeline_multiple_handlers(self):
        """Test pipeline with multiple storage handlers"""
        # Arrange
        storage1 = MockStorageHandler("Storage1")
        storage2 = MockStorageHandler("Storage2")
        filedirectory = {"Storage1": "output1.csv", "Storage2": "output2.csv"}
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[storage1, storage2],
            jobs=self.jobs,
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 2)
        
        # Verify both storage handlers were called
        self.assertEqual(storage1.save_call_count, 2)
        self.assertEqual(storage2.save_call_count, 2)
        self.assertEqual(len(storage1.saved_data), 4)
        self.assertEqual(len(storage2.saved_data), 4)
    
    def test_pipeline_job_details_structure(self):
        """Test the structure of job details in results"""
        # Act
        result = self.pipeline.run()
        
        # Assert
        job_details = result['job_details']
        self.assertEqual(len(job_details), 2)
        
        for job_name, details in job_details.items():
            self.assertIn(job_name, self.jobs)
            self.assertIn('success', details)
            self.assertIn('records_extracted', details)
            self.assertIn('error', details)
            self.assertTrue(details['success'])
            self.assertEqual(details['records_extracted'], 2)
            self.assertIsNone(details['error'])


class TestNaukriFresherPipeline(unittest.TestCase):
    """Test cases for Naukri Fresher Job Scraping Pipeline"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_extractor = MockJobExtractor("MockFresherExtractor")
        self.mock_storage = MockStorageHandler("MockFresherStorage")
        self.job_roles = ["Entry Level Python Developer", "Junior Data Analyst"]
        self.filedirectory = {"MockFresherStorage": "fresher_output.csv"}
        self.locations = ["Bangalore", "Hyderabad"]
        
        self.pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[self.mock_storage],
            job_roles=self.job_roles,
            filedirectory=self.filedirectory,
            locations=self.locations
        )
    
    def test_fresher_pipeline_initialization_success(self):
        """Test successful fresher pipeline initialization"""
        # Assert
        self.assertEqual(len(self.pipeline.extractors), 1)
        self.assertEqual(len(self.pipeline.handlers), 1)
        self.assertEqual(len(self.pipeline.job_roles), 2)
        self.assertEqual(self.pipeline.locations, self.locations)
        self.assertEqual(self.pipeline.filedirectory, self.filedirectory)
    
    def test_fresher_pipeline_initialization_without_locations(self):
        """Test fresher pipeline initialization without locations"""
        # Arrange
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[self.mock_storage],
            job_roles=self.job_roles,
            filedirectory=self.filedirectory,
            locations=None
        )
        
        # Assert
        self.assertIsNone(pipeline.locations)
    
    def test_fresher_pipeline_run_success(self):
        """Test successful fresher pipeline execution"""
        # Act
        result = self.pipeline.run()
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result['total_job_roles'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 4)
        self.assertEqual(result['fresher_friendly_records'], 4)
        self.assertIn('job_details', result)
        self.assertIn('start_time', result)
        self.assertIn('end_time', result)
        self.assertIn('execution_time_seconds', result)
    
    def test_fresher_pipeline_run_extractor_failure(self):
        """Test fresher pipeline execution with extractor failure"""
        # Arrange
        failing_extractor = MockJobExtractor("FailingFresherExtractor", should_fail=True)
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[failing_extractor],
            handlers=[self.mock_storage],
            job_roles=self.job_roles,
            filedirectory=self.filedirectory,
            locations=self.locations
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_job_roles'], 2)
        self.assertEqual(result['successful_jobs'], 0)
        self.assertEqual(result['failed_jobs'], 2)
        self.assertEqual(result['total_records'], 0)
        self.assertEqual(result['fresher_friendly_records'], 0)
    
    def test_fresher_pipeline_run_storage_failure(self):
        """Test fresher pipeline execution with storage failure"""
        # Arrange
        failing_storage = MockStorageHandler("FailingFresherStorage", should_fail=True)
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[self.mock_extractor],
            handlers=[failing_storage],
            job_roles=self.job_roles,
            filedirectory={"FailingFresherStorage": "fresher_output.csv"},
            locations=self.locations
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_job_roles'], 2)
        self.assertEqual(result['successful_jobs'], 0)
        self.assertEqual(result['failed_jobs'], 2)
    
    def test_fresher_pipeline_statistics_accuracy(self):
        """Test accuracy of fresher pipeline statistics"""
        # Act
        result = self.pipeline.run()
        
        # Assert
        self.assertEqual(result['total_records'], 4)
        self.assertEqual(result['fresher_friendly_records'], 4)
        
        # Verify job details structure
        for role_name, role_details in result['job_details'].items():
            self.assertIn(role_name, self.job_roles)
            self.assertIn('success', role_details)
            self.assertIn('records_extracted', role_details)
            self.assertIn('fresher_friendly', role_details)
            self.assertTrue(role_details['success'])
            self.assertEqual(role_details['records_extracted'], 2)
            self.assertEqual(role_details['fresher_friendly'], 2)


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for pipeline scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor1 = MockJobExtractor("IntegrationExtractor1")
        self.extractor2 = MockJobExtractor("IntegrationExtractor2")
        self.storage1 = MockStorageHandler("IntegrationStorage1")
        self.storage2 = MockStorageHandler("IntegrationStorage2")
    
    def test_general_pipeline_full_integration(self):
        """Test full integration scenario for general pipeline"""
        # Arrange
        jobs = ["Full Stack Developer", "DevOps Engineer"]
        filedirectory = {"IntegrationStorage1": "jobs1.csv", "IntegrationStorage2": "jobs2.csv"}
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[self.extractor1, self.extractor2],
            handlers=[self.storage1, self.storage2],
            jobs=jobs,
            filedirectory=filedirectory
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 8)  # 2 jobs × 2 extractors × 2 records
        
        # Verify all extractors and handlers were called
        self.assertEqual(self.extractor1.extract_call_count, 2)
        self.assertEqual(self.extractor2.extract_call_count, 2)
        self.assertEqual(self.storage1.save_call_count, 2)
        self.assertEqual(self.storage2.save_call_count, 2)
    
    def test_fresher_pipeline_full_integration(self):
        """Test full integration scenario for fresher pipeline"""
        # Arrange
        job_roles = ["Junior Python Developer", "Trainee Data Scientist"]
        locations = ["Mumbai", "Pune"]
        filedirectory = {"IntegrationStorage1": "fresher1.csv", "IntegrationStorage2": "fresher2.csv"}
        
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[self.extractor1, self.extractor2],
            handlers=[self.storage1, self.storage2],
            job_roles=job_roles,
            filedirectory=filedirectory,
            locations=locations
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_job_roles'], 2)
        self.assertEqual(result['successful_jobs'], 2)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 8)
        self.assertEqual(result['fresher_friendly_records'], 8)
    
    def test_mixed_failure_scenario(self):
        """Test scenario with mixed failures"""
        # Arrange
        failing_extractor = MockJobExtractor("FailingExtractor", should_fail=True)
        failing_storage = MockStorageHandler("FailingStorage", should_fail=True)
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[self.extractor1, failing_extractor],
            handlers=[self.storage1, failing_storage],
            jobs=["Test Job"],
            filedirectory={"IntegrationStorage1": "success.csv", "FailingStorage": "fail.csv"}
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], 1)
        self.assertEqual(result['failed_jobs'], 1)  # Should fail due to storage failure
        
        # Verify both extractors were called
        self.assertEqual(self.extractor1.extract_call_count, 1)
        self.assertEqual(failing_extractor.extract_call_count, 1)


class TestPipelinePerformance(unittest.TestCase):
    """Performance and load testing for pipelines"""
    
    def test_large_job_list_performance(self):
        """Test pipeline performance with large job list"""
        # Arrange
        large_job_list = [f"Job Title {i}" for i in range(100)]
        extractor = MockJobExtractor("PerformanceExtractor")
        storage = MockStorageHandler("PerformanceStorage")
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[extractor],
            handlers=[storage],
            jobs=large_job_list,
            filedirectory={"PerformanceStorage": "performance_test.csv"}
        )
        
        # Act
        start_time = datetime.now()
        result = pipeline.run()
        end_time = datetime.now()
        
        # Assert
        self.assertEqual(result['total_jobs'], 100)
        self.assertEqual(result['successful_jobs'], 100)
        self.assertEqual(result['failed_jobs'], 0)
        self.assertEqual(result['total_records'], 200)  # 100 jobs × 2 records each
        
        # Performance check (should complete within reasonable time)
        execution_time = (end_time - start_time).total_seconds()
        self.assertLess(execution_time, 10.0, "Pipeline should complete within 10 seconds")
        
        # Verify extractor and storage call counts
        self.assertEqual(extractor.extract_call_count, 100)
        self.assertEqual(storage.save_call_count, 100)
    
    def test_memory_usage_with_large_datasets(self):
        """Test memory usage with large datasets"""
        # This is a basic test - in real scenarios, you'd use memory profiling tools
        # Arrange
        extractor = MockJobExtractor("MemoryTestExtractor")
        storage = MockStorageHandler("MemoryTestStorage")
        jobs = [f"Memory Test Job {i}" for i in range(50)]
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[extractor],
            handlers=[storage],
            jobs=jobs,
            filedirectory={"MemoryTestStorage": "memory_test.csv"}
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_records'], 100)
        self.assertEqual(len(storage.saved_data), 100)
        
        # Basic memory check - ensure data is properly stored
        for record in storage.saved_data:
            self.assertIsInstance(record, dict)
            self.assertIn('title', record)
            self.assertIn('company', record)


class TestPipelineErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_invalid_job_types(self):
        """Test pipeline with invalid job types"""
        # Arrange
        extractor = MockJobExtractor("InvalidJobExtractor")
        storage = MockStorageHandler("InvalidJobStorage")
        invalid_jobs = ["", "   ", None]
        
        # Filter out None as it would cause type issues
        valid_invalid_jobs = [job for job in invalid_jobs if job is not None]
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[extractor],
            handlers=[storage],
            jobs=valid_invalid_jobs,
            filedirectory={"InvalidJobStorage": "invalid_test.csv"}
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['total_jobs'], len(valid_invalid_jobs))
        # Pipeline should still attempt to process invalid job names
        self.assertEqual(extractor.extract_call_count, len(valid_invalid_jobs))
    
    def test_empty_locations_list(self):
        """Test pipeline with empty locations list"""
        # Arrange
        extractor = MockJobExtractor("EmptyLocationsExtractor")
        storage = MockStorageHandler("EmptyLocationsStorage")
        
        pipeline = NaukriFresherJobDataExtractionPipeline(
            extractors=[extractor],
            handlers=[storage],
            job_roles=["Test Role"],
            filedirectory={"EmptyLocationsStorage": "empty_locations.csv"},
            locations=[]
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 1)
        self.assertEqual(extractor.extract_call_count, 1)
        
        # Verify empty locations were passed
        job_name, locations = extractor.extract_calls[0]
        self.assertEqual(locations, [])
    
    def test_extremely_long_job_titles(self):
        """Test pipeline with extremely long job titles"""
        # Arrange
        long_job_title = "A" * 1000  # 1000 character job title
        extractor = MockJobExtractor("LongTitleExtractor")
        storage = MockStorageHandler("LongTitleStorage")
        
        pipeline = NaukriGeneralJobDataExtractionPipeline(
            extractors=[extractor],
            handlers=[storage],
            jobs=[long_job_title],
            filedirectory={"LongTitleStorage": "long_title_test.csv"}
        )
        
        # Act
        result = pipeline.run()
        
        # Assert
        self.assertEqual(result['successful_jobs'], 1)
        self.assertEqual(extractor.extract_call_count, 1)
        
        # Verify long title was passed correctly
        passed_job_title = extractor.extract_calls[0][0]
        self.assertEqual(passed_job_title, long_job_title)


# Test Suite Configuration
def create_test_suite():
    """Create and return a test suite with all test cases"""
    suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestNaukriGeneralPipeline,
        TestNaukriFresherPipeline,
        TestPipelineIntegration,
        TestPipelinePerformance,
        TestPipelineErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests_with_coverage():
    """Run tests with coverage reporting"""
    import coverage
    
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*60)
    print("COVERAGE REPORT")
    print("="*60)
    cov.report()
    
    # Generate HTML coverage report
    cov.html_report(directory='tests/coverage_html')
    print(f"\nHTML coverage report generated in: tests/coverage_html/")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    print("Running Scraping Pipelines Unit Tests")
    print("="*60)
    
    # Run tests
    success = run_tests_with_coverage()
    
    if success:
        print("\n✅ All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)
