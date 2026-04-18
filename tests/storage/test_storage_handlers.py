"""
Unit Tests for Storage Handlers
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

from src.storage.base_storage_handler import StorageHandler
from src.storage.csv_storage_handler import CSVStorageHandler
from src.storage.json_storage_handler import JSONStorageHandler
from src.storage.sqlite_handler import MySQLStorageHandler


class TestStorageHandler(unittest.TestCase):
    """Test cases for StorageHandler abstract base class."""
    
    def test_abstract_methods(self):
        """Test that StorageHandler is properly abstract."""
        with self.assertRaises(TypeError):
            StorageHandler()
    
    def test_save_method_is_abstract(self):
        """Test that save method is abstract."""
        self.assertTrue(hasattr(StorageHandler, 'save'))
        self.assertTrue(getattr(StorageHandler, 'save').__isabstractmethod__)
    
    def test_get_name_method_is_abstract(self):
        """Test that get_name method is abstract."""
        self.assertTrue(hasattr(StorageHandler, 'get_name'))
        self.assertTrue(getattr(StorageHandler, 'get_name').__isabstractmethod__)


class TestCSVStorageHandler(unittest.TestCase):
    """Test cases for CSVStorageHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = CSVStorageHandler()
        self.test_data = [
            {"title": "Data Scientist", "location": "Bangalore", "salary": "8-12 LPA"},
            {"title": "Software Engineer", "location": "Mumbai", "salary": "10-15 LPA"},
            {"title": "ML Engineer", "location": "Delhi", "salary": "12-18 LPA"}
        ]
    
    def test_get_name(self):
        """Test handler name method."""
        result = self.handler.get_name()
        self.assertEqual(result, "csv")
    
    def test_save_valid_data(self):
        """Test saving valid data to CSV."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save data
            self.handler.save(self.test_data, temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify data content
            df = pd.read_csv(temp_path)
            self.assertEqual(len(df), 3)
            self.assertIn("title", df.columns)
            self.assertIn("location", df.columns)
            self.assertIn("salary", df.columns)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_empty_data(self):
        """Test saving empty data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save empty data
            self.handler.save([], temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify empty data
            df = pd.read_csv(temp_path)
            self.assertEqual(len(df), 0)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_invalid_path(self):
        """Test saving to invalid path."""
        invalid_path = "/invalid/path/test.csv"
        
        with self.assertRaises(Exception):
            self.handler.save(self.test_data, invalid_path)


class TestJSONStorageHandler(unittest.TestCase):
    """Test cases for JSONStorageHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = JSONStorageHandler()
        self.test_data = [
            {"title": "Data Scientist", "location": "Bangalore", "salary": "8-12 LPA"},
            {"title": "Software Engineer", "location": "Mumbai", "salary": "10-15 LPA"}
        ]
    
    def test_get_name(self):
        """Test handler name method."""
        result = self.handler.get_name()
        self.assertEqual(result, "json")
    
    def test_save_valid_data(self):
        """Test saving valid data to JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save data
            self.handler.save(self.test_data, temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify data content
            import json
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(len(loaded_data), 2)
            self.assertEqual(loaded_data[0]["title"], "Data Scientist")
            self.assertEqual(loaded_data[1]["location"], "Mumbai")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_empty_data(self):
        """Test saving empty data to JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save empty data
            self.handler.save([], temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify empty data
            import json
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(len(loaded_data), 0)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMySQLStorageHandler(unittest.TestCase):
    """Test cases for MySQLStorageHandler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = MySQLStorageHandler()
        self.test_data = [
            {"title": "Data Scientist", "location": "Bangalore", "salary": "8-12 LPA"},
            {"title": "Software Engineer", "location": "Mumbai", "salary": "10-15 LPA"}
        ]
    
    def test_get_name(self):
        """Test handler name method."""
        result = self.handler.get_name()
        self.assertEqual(result, "mysql")
    
    def test_save_valid_data(self):
        """Test saving valid data to SQLite."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save data
            self.handler.save(self.test_data, temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify data content
            import sqlite3
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_data")
            count = cursor.fetchone()[0]
            conn.close()
            
            self.assertEqual(count, 2)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_save_empty_data(self):
        """Test saving empty data to SQLite."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save empty data
            self.handler.save([], temp_path)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify empty data
            import sqlite3
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM job_data")
            count = cursor.fetchone()[0]
            conn.close()
            
            self.assertEqual(count, 0)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestStorageIntegration(unittest.TestCase):
    """Integration tests for storage handlers."""
    
    def test_handler_interface_compliance(self):
        """Test that all handlers implement required interface."""
        handlers = [CSVStorageHandler(), JSONStorageHandler(), SQLiteHandler()]
        
        for handler in handlers:
            self.assertTrue(hasattr(handler, 'save'))
            self.assertTrue(hasattr(handler, 'get_name'))
            self.assertTrue(callable(getattr(handler, 'save')))
            self.assertTrue(callable(getattr(handler, 'get_name')))
    
    def test_handler_data_consistency(self):
        """Test data consistency across different handlers."""
        test_data = [
            {"title": "Data Scientist", "location": "Bangalore", "salary": "8-12 LPA"}
        ]
        
        handlers = [CSVStorageHandler(), JSONStorageHandler()]
        
        for handler in handlers:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                
                try:
                    # Save data
                    handler.save(test_data, temp_path)
                    
                    # Verify file exists
                    self.assertTrue(os.path.exists(temp_path))
                    
                finally:
                    # Clean up
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
