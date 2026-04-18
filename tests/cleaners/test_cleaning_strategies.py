"""
Unit Tests for Cleaning Strategies
Job Trend Predictor - Test Suite
"""

import unittest
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.cleaners.strategies.title_cleaning_strategy import TitleCleaningStrategy
from src.cleaners.strategies.role_type_cleaning_strategy import RoleCleaningStrategy
from src.cleaners.strategies.skill_cleaning_strategy import SkillsCleaningStrategy
from src.cleaners.strategies.location_cleaning_strategy import LocationCleaningStrategy
from src.cleaners.strategies.salary_cleaning_strategy import SalaryCleaningStrategy


class TestTitleCleaningStrategy(unittest.TestCase):
    """Test cases for TitleCleaningStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = TitleCleaningStrategy()
    
    def test_clean_feature_valid_title(self):
        """Test cleaning of valid job titles."""
        test_data = pd.Series(["Data Scientist", "Software Engineer", "ML Engineer"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(isinstance(item, str) for item in result))
    
    def test_clean_feature_invalid_title(self):
        """Test cleaning of invalid job titles."""
        test_data = pd.Series(["", "N/A", None, "123"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertTrue(all(item == "Other" for item in result))
    
    def test_clean_feature_abbreviations(self):
        """Test expansion of common abbreviations."""
        test_data = pd.Series(["ML Engineer", "SRE", "AI Specialist"])
        result = self.strategy.clean_feature(test_data)
        
        # Should expand abbreviations
        self.assertTrue(any("machine learning" in item.lower() for item in result))
        self.assertTrue(any("site reliability" in item.lower() for item in result))
    
    def test_clean_feature_seniority_removal(self):
        """Test removal of seniority markers."""
        test_data = pd.Series(["Senior Software Engineer", "Jr. Developer", "Lead Data Scientist"])
        result = self.strategy.clean_feature(test_data)
        
        # Should remove seniority markers
        self.assertTrue(all("senior" not in item.lower() for item in result))
        self.assertTrue(all("jr." not in item.lower() for item in result))
        self.assertTrue(all("lead" not in item.lower() for item in result))


class TestRoleCleaningStrategy(unittest.TestCase):
    """Test cases for RoleCleaningStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = RoleCleaningStrategy()
    
    def test_clean_feature_valid_roles(self):
        """Test cleaning of valid job roles."""
        test_data = pd.Series(["Full-time", "Part-time", "Contract"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), 3)
        self.assertTrue(all(isinstance(item, str) for item in result))
    
    def test_clean_feature_noisy_roles(self):
        """Test cleaning of roles with noise."""
        test_data = pd.Series(["Full-time,", "Part-time;", "Contract|"])
        result = self.strategy.clean_feature(test_data)
        
        # Should remove trailing punctuation
        self.assertTrue(all(item.strip() == item for item in result))
        self.assertTrue(all(item.endswith(",") == False for item in result))
    
    def test_clean_feature_empty_roles(self):
        """Test cleaning of empty/invalid roles."""
        test_data = pd.Series(["", None, "   ", "N/A"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertTrue(all(item == "Other" for item in result))


class TestSkillsCleaningStrategy(unittest.TestCase):
    """Test cases for SkillsCleaningStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = SkillsCleaningStrategy()
    
    def test_clean_feature_valid_skills(self):
        """Test cleaning of valid skills data."""
        test_data = pd.DataFrame({
            "star_skills": ["Python", "SQL", "Machine Learning"],
            "normal_skills": ["JavaScript", "React", "Node.js"]
        })
        result = self.strategy.clean_feature(test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("combined_skills", result.columns)
        self.assertIn("skill_count", result.columns)
    
    def test_clean_feature_mixed_format_skills(self):
        """Test cleaning of skills in different formats."""
        test_data = pd.DataFrame({
            "star_skills": ["Python, SQL, ML", "JavaScript|React|Node", "Data Science;AI;ML"],
            "normal_skills": ["React, Vue", "Python, Java", "AWS, Docker"]
        })
        result = self.strategy.clean_feature(test_data)
        
        # Should handle different separators
        self.assertTrue(all(isinstance(skills, str) for skills in result["combined_skills"]))
        self.assertTrue(all(len(skills.split(", ")) >= 1 for skills in result["combined_skills"]))
    
    def test_clean_feature_empty_skills(self):
        """Test cleaning of empty skills data."""
        test_data = pd.DataFrame({
            "star_skills": ["", None, "N/A"],
            "normal_skills": [None, "", "   "]
        })
        result = self.strategy.clean_feature(test_data)
        
        # Should handle empty data gracefully
        self.assertTrue(all(skills == "" for skills in result["combined_skills"]))
        self.assertTrue(all(count == 0 for count in result["skill_count"]))


class TestLocationCleaningStrategy(unittest.TestCase):
    """Test cases for LocationCleaningStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = LocationCleaningStrategy()
    
    def test_clean_feature_valid_locations(self):
        """Test cleaning of valid locations."""
        test_data = pd.Series(["Bangalore, India", "Mumbai", "Delhi NCR"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("location_cities", result.columns)
    
    def test_clean_feature_mixed_format_locations(self):
        """Test cleaning of locations in different formats."""
        test_data = pd.Series(["Bangalore|Karnataka", "Mumbai, Maharashtra", "Delhi NCR"])
        result = self.strategy.clean_feature(test_data)
        
        # Should handle different separators and formats
        self.assertTrue(all(isinstance(cities, str) for cities in result["location_cities"]))
    
    def test_clean_feature_remote_locations(self):
        """Test detection of remote locations."""
        test_data = pd.Series(["Remote", "Work from Home", "Hybrid"])
        result = self.strategy.clean_feature(test_data)
        
        # Should detect remote work
        self.assertTrue(any("remote" in str(cities).lower() for cities in result["location_cities"]))


class TestSalaryCleaningStrategy(unittest.TestCase):
    """Test cases for SalaryCleaningStrategy."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.strategy = SalaryCleaningStrategy()
    
    def test_clean_feature_valid_salaries(self):
        """Test cleaning of valid salary formats."""
        test_data = pd.Series(["8-12 LPA", "15-20 LPA", "25-30 LPA"])
        result = self.strategy.clean_feature(test_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("min_salary", result.columns)
        self.assertIn("max_salary", result.columns)
    
    def test_clean_feature_mixed_salary_formats(self):
        """Test cleaning of different salary formats."""
        test_data = pd.Series(["8-12 LPA", "15-20 lpa", "25-30 LPA", "Not disclosed"])
        result = self.strategy.clean_feature(test_data)
        
        # Should handle different cases and formats
        self.assertTrue(all(isinstance(min_sal, (int, float)) for min_sal in result["min_salary"]))
        self.assertTrue(all(isinstance(max_sal, (int, float)) for max_sal in result["max_salary"]))
    
    def test_clean_feature_invalid_salaries(self):
        """Test cleaning of invalid salary data."""
        test_data = pd.Series(["Not disclosed", "N/A", "", None])
        result = self.strategy.clean_feature(test_data)
        
        # Should handle invalid data
        self.assertTrue(all(pd.isna(result["min_salary"][i]) or result["min_salary"][i] == 0 for i in range(len(result))))


if __name__ == "__main__":
    unittest.main()
