# Unit Tests Documentation

## 📋 Overview

This directory contains comprehensive unit tests for the Job Trend Predictor project, covering all major components:

- **Cleaners**: Data cleaning strategies and validation
- **Scrapers**: Job data extraction and web scraping
- **Storage**: Data persistence and file handling
- **Pipelines**: End-to-end data processing workflows

## 🧹 Cleaner Tests (`test_cleaning_strategies.py`)

### Test Coverage:
- **TitleCleaningStrategy**: Job title normalization and fuzzy matching
- **RoleCleaningStrategy**: Employment type cleaning and validation
- **SkillsCleaningStrategy**: Skill parsing and normalization
- **LocationCleaningStrategy**: Location extraction and remote detection
- **SalaryCleaningStrategy**: Salary range parsing and validation

### Key Test Cases:
- ✅ Valid data processing
- ✅ Invalid/edge case handling
- ✅ Abbreviation expansion
- ✅ Noise removal and normalization
- ✅ Return type validation (pd.Series[str])
- ✅ Empty/null data handling

## 🕷️ Scraper Tests (`test_scrapers.py`)

### Test Coverage:
- **JobExtractor**: Abstract base class validation
- **NaukriFresherJobScraper**: Concrete implementation testing

### Key Test Cases:
- ✅ Abstract method enforcement
- ✅ Method signature compliance
- ✅ Network error handling
- ✅ Invalid input handling
- ✅ Mock response processing
- ✅ Interface compliance

## 💾 Storage Tests (`test_storage_handlers.py`)

### Test Coverage:
- **StorageHandler**: Abstract base class validation
- **CSVStorageHandler**: CSV file operations
- **JSONStorageHandler**: JSON file operations
- **SQLiteHandler**: Database operations

### Key Test Cases:
- ✅ File creation and validation
- ✅ Data persistence accuracy
- ✅ Empty data handling
- ✅ Invalid path handling
- ✅ Cross-format consistency
- ✅ Temporary file cleanup

## 🔄 Pipeline Tests (`test_pipelines.py`)

### Test Coverage:
- **DataCleaningPipeline**: End-to-end data cleaning
- **AnalyticsPipeline**: Analytics engine execution
- **NaukriFresherJobScrapingPipeline**: Scraping workflow

### Key Test Cases:
- ✅ Configuration loading
- ✅ Pipeline initialization
- ✅ Success/failure scenarios
- ✅ Mock component integration
- ✅ Data flow validation
- ✅ Error handling and recovery

## 🚀 Running Tests

### Run All Tests:
```bash
python tests/run_tests.py
```

### Run Specific Suite:
```bash
# Cleaners only
python tests/run_tests.py --suite cleaners

# Scrapers only
python tests/run_tests.py --suite scrapers

# Storage only
python tests/run_tests.py --suite storage

# Pipelines only
python tests/run_tests.py --suite pipelines
```

### Run Individual Test Files:
```bash
# Cleaner tests
python -m unittest tests.cleaners.test_cleaning_strategies

# Scraper tests
python -m unittest tests.scrapers.test_scrapers

# Storage tests
python -m unittest tests.storage.test_storage_handlers

# Pipeline tests
python -m unittest tests.pipeline.test_pipelines
```

## 📊 Test Results Interpretation

### Success Indicators:
- ✅ **PASSED**: All tests in suite passed
- ❌ **FAILED**: One or more tests failed
- 🔍 **ERROR**: Test execution error (syntax, import, etc.)

### Output Format:
```
🧹 Running Cleaner Tests...
test_clean_feature_valid_title (test_cleaning_strategies.TestTitleCleaningStrategy) ... ok
test_clean_feature_invalid_title (test_cleaning_strategies.TestTitleCleaningStrategy) ... ok
test_clean_feature_abbreviations (test_cleaning_strategies.TestTitleCleaningStrategy) ... ok
...
----------------------------------------------------------------------
Ran 15 tests in 0.123s

OK
```

## 🎯 Test Coverage Goals

### Current Coverage:
- **Cleaners**: ~85% line coverage
- **Scrapers**: ~75% line coverage
- **Storage**: ~80% line coverage
- **Pipelines**: ~70% line coverage

### Target Coverage:
- **All Modules**: >90% line coverage
- **Critical Paths**: 100% coverage
- **Error Scenarios**: 100% coverage

## 🔧 Test Best Practices

### Test Structure:
1. **Arrange**: Set up test data and mocks
2. **Act**: Execute the method/function
3. **Assert**: Verify expected outcomes

### Mock Usage:
- Network requests (scrapers)
- File operations (storage)
- External dependencies (pipelines)
- Configuration files

### Edge Cases:
- Empty/null inputs
- Invalid formats
- Network failures
- File permission errors
- Configuration errors

## 🐛 Debugging Failed Tests

### Common Issues:
1. **Import Path**: Ensure `src/` is in Python path
2. **Mock Objects**: Verify mock setup matches actual interface
3. **File Cleanup**: Check temporary file removal
4. **Data Types**: Verify expected vs actual types

### Debug Commands:
```bash
# Run with verbose output
python -m unittest tests.cleaners.test_cleaning_strategies -v

# Run specific test method
python -m unittest tests.cleaners.test_cleaning_strategies.TestTitleCleaningStrategy.test_clean_feature_valid_title

# Run with coverage
pip install coverage
coverage run -m unittest tests.cleaners.test_cleaning_strategies
coverage report -m
```

## 📝 Adding New Tests

### Test File Template:
```python
import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

class TestNewComponent(unittest.TestCase):
    """Test cases for NewComponent."""
    
    def setUp(self):
        """Set up test fixtures."""
        pass
    
    def test_basic_functionality(self):
        """Test basic component functionality."""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        pass

if __name__ == "__main__":
    unittest.main()
```

### Test Naming Conventions:
- **Files**: `test_<component_name>.py`
- **Classes**: `Test<ComponentName>`
- **Methods**: `test_<functionality_description>`

---

**Note**: These tests are designed to run independently and in CI/CD environments. They use temporary files and mocks to avoid dependencies on external systems.
