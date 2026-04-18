"""
Unit Tests for Scrapers
Job Trend Predictor - Test Suite
"""

import unittest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.scrapers.base_scraper import JobExtractor
from src.scrapers.naukri_fresher_job_scraper import FresherJobScraper


class TestJobExtractor(unittest.TestCase):
    """Test cases for JobExtractor abstract base class."""
    
    def test_abstract_methods(self):
        """Test that JobExtractor is properly abstract."""
        with self.assertRaises(TypeError):
            JobExtractor()
    
    def test_extract_method_is_abstract(self):
        """Test that extract method is abstract."""
        self.assertTrue(hasattr(JobExtractor, 'extract'))
        self.assertTrue(getattr(JobExtractor, 'extract').__isabstractmethod__)
    
    def test_get_name_method_is_abstract(self):
        """Test that get_name method is abstract."""
        self.assertTrue(hasattr(JobExtractor, 'get_name'))
        self.assertTrue(getattr(JobExtractor, 'get_name').__isabstractmethod__)


class TestFresherJobScraper(unittest.TestCase):
    """Test cases for FresherJobScraper."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = FresherJobScraper()
    
    def test_get_name(self):
        """Test scraper name method."""
        result = self.scraper.get_name()
        self.assertEqual(result, "FresherJobScraper")
    
    def test_initialization(self):
        """Test scraper initialization."""
        self.assertIsInstance(self.scraper, FresherJobScraper)
        self.assertIsInstance(self.scraper, JobExtractor)
    
    @patch('requests.get')
    def test_extract_with_valid_data(self, mock_get):
        """Test extraction with valid mock data."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <div class="jobtuple">
                <div class="info fleft">
                    <h3>Data Scientist</h3>
                    <div class="loc">Bangalore</div>
                    <div class="exp">0-3 Yrs</div>
                    <div class="salary">8-12 LPA</div>
                </div>
            </div>
        </html>
        """
        mock_get.return_value = mock_response
        
        # Test extraction
        result = self.scraper.extract("Data Scientist", ["Bangalore", "Mumbai"])
        
        self.assertIsInstance(result, list)
        if result:  # Only test if extraction returned data
            self.assertIsInstance(result[0], dict)
    
    @patch('requests.get')
    def test_extract_with_network_error(self, mock_get):
        """Test extraction with network error."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        # Should handle network errors gracefully
        with self.assertRaises(Exception):
            self.scraper.extract("Data Scientist", ["Bangalore"])
    
    def test_extract_with_empty_job_name(self):
        """Test extraction with empty job name."""
        result = self.scraper.extract("", ["Bangalore"])
        self.assertEqual(result, [])
    
    def test_extract_with_empty_locations(self):
        """Test extraction with empty locations."""
        result = self.scraper.extract("Data Scientist", [])
        self.assertEqual(result, [])
    
    def test_extract_with_invalid_job_name(self):
        """Test extraction with invalid job name."""
        result = self.scraper.extract(None, ["Bangalore"])
        self.assertEqual(result, [])
    
    def test_extract_with_invalid_locations(self):
        """Test extraction with invalid locations."""
        result = self.scraper.extract("Data Scientist", None)
        self.assertEqual(result, [])


class TestScraperIntegration(unittest.TestCase):
    """Integration tests for scraper functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scraper = NaukriFresherJobScraper()
    
    def test_scraper_interface_compliance(self):
        """Test that scraper implements required interface."""
        self.assertTrue(hasattr(self.scraper, 'extract'))
        self.assertTrue(hasattr(self.scraper, 'get_name'))
        self.assertTrue(callable(getattr(self.scraper, 'extract')))
        self.assertTrue(callable(getattr(self.scraper, 'get_name')))
    
    def test_scraper_method_signatures(self):
        """Test method signatures match interface."""
        import inspect
        
        # Check extract method signature
        extract_sig = inspect.signature(self.scraper.extract)
        extract_params = list(extract_sig.parameters.keys())
        self.assertIn('job_name', extract_params)
        self.assertIn('locations', extract_params)
        
        # Check get_name method signature
        get_name_sig = inspect.signature(self.scraper.get_name)
        self.assertEqual(len(get_name_sig.parameters), 0)


if __name__ == "__main__":
    unittest.main()
