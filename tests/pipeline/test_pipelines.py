"""
Unit Tests for Pipelines
Job Trend Predictor - Test Suite
"""

import unittest
import pandas as pd
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pipelines.cleaning_pipeline import DataCleaningPipeline
from pipelines.analytics_pipeline import AnalyticsPipeline
from pipelines.naukri_fresher_job_scraping_pipeline import NaukriFresherJobDataExtractionPipeline


class TestDataCleaningPipeline(unittest.TestCase):
    """Test cases for DataCleaningPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "data_paths": {
                "input_path": "test_input.csv",
                "output_dir": "test_output",
                "output_file": "test_cleaned.csv"
            }
        }
        
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        import yaml
        yaml.dump(self.test_config, self.config_file)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_file.name):
            os.unlink(self.config_file.name)
    
    def test_initialization_with_config(self):
        """Test pipeline initialization with config."""
        pipeline = DataCleaningPipeline(self.config_file.name)
        
        self.assertEqual(pipeline.config_path, self.config_file.name)
        self.assertIsNotNone(pipeline.config)
        self.assertIsNotNone(pipeline.cleaner)
        self.assertEqual(pipeline.input_path, "test_input.csv")
        self.assertEqual(pipeline.output_dir, "test_output")
        self.assertEqual(pipeline.output_file, "test_cleaned.csv")
    
    def test_load_config_valid_file(self):
        """Test loading of valid config file."""
        pipeline = DataCleaningPipeline(self.config_file.name)
        config = pipeline._load_config(self.config_file.name)
        
        self.assertIsInstance(config, dict)
        self.assertIn("data_paths", config)
        self.assertIn("input_path", config["data_paths"])
    
    def test_load_config_invalid_file(self):
        """Test loading of invalid config file."""
        pipeline = DataCleaningPipeline("nonexistent.yaml")
        
        with self.assertRaises(Exception):
            pipeline._load_config("nonexistent.yaml")
    
    @patch('pandas.read_csv')
    def test_run_pipeline_success(self, mock_read_csv):
        """Test successful pipeline execution."""
        # Mock input data
        mock_data = pd.DataFrame({
            "title": ["Data Scientist", "Software Engineer"],
            "location": ["Bangalore", "Mumbai"],
            "salary": ["8-12 LPA", "10-15 LPA"]
        })
        mock_read_csv.return_value = mock_data
        
        # Mock cleaner
        mock_cleaned_data = pd.DataFrame({
            "title_cleaned": ["Data Scientist", "Software Engineer"],
            "location_cleaned": ["Bangalore", "Mumbai"],
            "min_salary": [8, 10],
            "max_salary": [12, 15]
        })
        
        with patch.object(DataCleaningPipeline, '_save_output') as mock_save:
            pipeline = DataCleaningPipeline(self.config_file.name)
            pipeline.cleaner = Mock()
            pipeline.cleaner.clean_data.return_value = mock_cleaned_data
            
            # Run pipeline
            result = pipeline.run()
            
            self.assertTrue(result)
            mock_save.assert_called_once_with(mock_cleaned_data)
    
    def test_run_pipeline_failure(self):
        """Test pipeline execution with failure."""
        with patch.object(DataCleaningPipeline, '_save_output') as mock_save:
            mock_save.side_effect = Exception("Save failed")
            
            pipeline = DataCleaningPipeline(self.config_file.name)
            
            # Should handle failure gracefully
            with self.assertRaises(Exception):
                pipeline.run()


class TestAnalyticsPipeline(unittest.TestCase):
    """Test cases for AnalyticsPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "data_paths": {
                "input_path": "test_cleaned.csv",
                "output_dir": "test_analytics"
            }
        }
        
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        import yaml
        yaml.dump(self.test_config, self.config_file)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_file.name):
            os.unlink(self.config_file.name)
    
    def test_initialization_with_config(self):
        """Test analytics pipeline initialization."""
        pipeline = AnalyticsPipeline(self.config_file.name)
        
        self.assertEqual(pipeline.config_path, self.config_file.name)
        self.assertIsNotNone(pipeline.config)
    
    @patch('pandas.read_csv')
    def test_run_analytics_success(self, mock_read_csv):
        """Test successful analytics execution."""
        # Mock input data
        mock_data = pd.DataFrame({
            "title_cleaned": ["Data Scientist", "Software Engineer"],
            "location_cleaned": ["Bangalore", "Mumbai"],
            "min_salary": [8, 10],
            "max_salary": [12, 15]
        })
        mock_read_csv.return_value = mock_data
        
        pipeline = AnalyticsPipeline(self.config_file.name)
        
        # Mock analytics engines
        with patch.object(pipeline, '_run_all_analytics') as mock_analytics:
            mock_analytics.return_value = {"demand_score": 85, "growth_score": 90}
            
            # Run pipeline
            result = pipeline.run()
            
            self.assertTrue(result)
            mock_analytics.assert_called_once_with(mock_data)
    
    def test_run_analytics_failure(self):
        """Test analytics execution with failure."""
        pipeline = AnalyticsPipeline(self.config_file.name)
        
        with patch.object(pipeline, '_run_all_analytics') as mock_analytics:
            mock_analytics.side_effect = Exception("Analytics failed")
            
            # Should handle failure gracefully
            with self.assertRaises(Exception):
                pipeline.run()


class TestNaukriFresherJobDataExtractionPipeline(unittest.TestCase):
    """Test cases for NaukriFresherJobDataExtractionPipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_config = {
            "scraping": {
                "job_roles": ["Data Scientist", "Software Engineer"],
                "locations": ["Bangalore", "Mumbai"],
                "output_dir": "test_scraped"
            }
        }
        
        # Create temporary config file
        self.config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        import yaml
        yaml.dump(self.test_config, self.config_file)
        self.config_file.close()
    
    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.config_file.name):
            os.unlink(self.config_file.name)
    
    def test_initialization_with_config(self):
        """Test scraping pipeline initialization."""
        pipeline = NaukriFresherJobDataExtractionPipeline(self.config_file.name)
        
        self.assertEqual(pipeline.config_path, self.config_file.name)
        self.assertIsNotNone(pipeline.config)
    
    @patch('requests.get')
    def test_run_scraping_success(self, mock_get):
        """Test successful scraping execution."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html>Mock job data</html>"
        mock_get.return_value = mock_response
        
        pipeline = NaukriFresherJobScrapingPipeline(self.config_file.name)
        
        with patch.object(pipeline, '_save_scraped_data') as mock_save:
            mock_save.return_value = True
            
            # Run pipeline
            result = pipeline.run()
            
            self.assertTrue(result)
            mock_save.assert_called()
    
    @patch('requests.get')
    def test_run_scraping_failure(self, mock_get):
        """Test scraping execution with failure."""
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        pipeline = NaukriFresherJobScrapingPipeline(self.config_file.name)
        
        # Should handle failure gracefully
        with self.assertRaises(Exception):
            pipeline.run()


class TestPipelineIntegration(unittest.TestCase):
    """Integration tests for all pipelines."""
    
    def test_pipeline_interface_compliance(self):
        """Test that all pipelines have required methods."""
        pipelines = [
            DataCleaningPipeline(),
            AnalyticsPipeline(),
            NaukriFresherJobDataExtractionPipeline()
        ]
        
        for pipeline in pipelines:
            self.assertTrue(hasattr(pipeline, 'run'))
            self.assertTrue(callable(getattr(pipeline, 'run')))
    
    def test_pipeline_config_handling(self):
        """Test that all pipelines handle config correctly."""
        test_config = {
            "test": "config"
        }
        
        # Create temporary config file
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        import yaml
        yaml.dump(test_config, config_file)
        config_file.close()
        
        try:
            pipelines = [
                DataCleaningPipeline(config_file.name),
                AnalyticsPipeline(config_file.name),
                NaukriFresherJobDataExtractionPipeline(config_file.name)
            ]
            
            for pipeline in pipelines:
                self.assertIsNotNone(pipeline.config)
                self.assertEqual(pipeline.config, test_config)
                
        finally:
            if os.path.exists(config_file.name):
                os.unlink(config_file.name)


if __name__ == "__main__":
    unittest.main()
