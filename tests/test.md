# Scraping Pipelines Test Suite

Comprehensive QA testing implementation for the Job Trend Predictor scraping pipelines.

## 📋 Test Overview

This test suite provides thorough testing coverage for:

- **Naukri General Job Scraping Pipeline**
- **Naukri Fresher Job Scraping Pipeline**
- **Storage Handlers (CSV, MySQL)**
- **Error Handling and Recovery**
- **Performance and Load Testing**
- **Integration Testing**

## 🗂️ Test Structure

```
tests/
├── test_scraping_pipelines.py      # Scraping pipelines unit tests
├── test_pipeline_integration.py    # Scraping pipelines integration tests
├── test_cleaning_pipeline.py        # Existing cleaning pipeline tests
├── test_analytics_module.py         # Analytics module comprehensive tests
├── test_analytics_performance.py    # Analytics performance and load tests
├── test_analytics_integration.py    # Analytics integration tests
├── run_tests.py                     # Scraping pipelines test runner
├── run_analytics_tests.py          # Analytics module test runner
├── requirements_test.txt            # Test dependencies
├── pytest.ini                      # pytest configuration
├── coverage_html/                   # Coverage reports (generated)
├── analytics_coverage_html/         # Analytics coverage reports (generated)
├── reports/                        # Test reports (generated)
├── analytics_reports/               # Analytics test reports (generated)
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
pip install -r tests/requirements_test.txt
```

### 2. Run Scraping Pipelines Tests

```bash
# Run all scraping tests with coverage
python tests/run_tests.py --all

# Or use pytest directly
pytest tests/test_scraping_pipelines.py -v --cov=src/pipelines --cov-report=html
```

### 3. Run Analytics Module Tests

```bash
# Run all analytics tests with coverage
python tests/run_analytics_tests.py --all

# Or use pytest directly
pytest tests/test_analytics_module.py -v --cov=src/analytics --cov-report=html
```

### 4. Run Specific Test Categories

#### Scraping Pipelines Tests
```bash
# Unit tests only
python tests/run_tests.py --unit

# Integration tests only
python tests/run_tests.py --integration

# Performance tests only
python tests/run_tests.py --performance

# With verbose output
python tests/run_tests.py --all --verbose
```

#### Analytics Module Tests
```bash
# Unit tests only
python tests/run_analytics_tests.py --unit

# Performance tests only
python tests/run_analytics_tests.py --performance

# Integration tests only
python tests/run_analytics_tests.py --integration

# Analytics benchmarks
python tests/run_analytics_tests.py --benchmarks

# With verbose output
python tests/run_analytics_tests.py --all --verbose
```

### 5. Code Quality Checks

```bash
python tests/run_tests.py --quality-check
```

## 📊 Test Categories

### 🧪 Scraping Pipelines Unit Tests (`test_scraping_pipelines.py`)

**Purpose**: Test individual scraping components in isolation

**Coverage**:
- Pipeline initialization validation
- Configuration validation
- Success and failure scenarios
- Error handling
- Edge cases

**Test Classes**:
- `TestNaukriGeneralPipeline` - General pipeline tests
- `TestNaukriFresherPipeline` - Fresher pipeline tests
- `TestPipelineIntegration` - Multi-component integration
- `TestPipelinePerformance` - Performance and load testing
- `TestPipelineErrorHandling` - Error scenarios

### 🔗 Scraping Pipelines Integration Tests (`test_pipeline_integration.py`)

**Purpose**: Test end-to-end scraping scenarios with real components

**Coverage**:
- CSV storage integration
- Database storage integration
- Real scraper simulation
- Data validation
- Error recovery

### 🧪 Analytics Module Unit Tests (`test_analytics_module.py`)

**Purpose**: Test individual analytics engines in isolation

**Coverage**:
- **Career Insights** (2 engines): CareerPathEngine, RoleEvaluationEngine
- **Domain Analysis** (4 engines): AIReplacementRiskEngine, DomainStabilityEngine, SalaryGrowthEngine, SkillTransferabilityEngine
- **Entry Barriers** (4 engines): InterviewDifficultyEngine, HiddenBlockerDetector, PrequisiteEngine, ProjectComplexityEvaluator
- **Market Analysis** (5 engines): DemandScoreCalculator, AverageSalaryCalculator, CompetitionLevelCalculator, JobMarketVelocityCalculator, SaturationRiskIndicator

**Test Classes**:
- `TestCareerPathEngine` - Learning path and readiness testing
- `TestAIReplacementRiskEngine` - Automation risk assessment
- `TestInterviewDifficultyEngine` - Interview complexity analysis
- `TestMarketDemandEngine` - Market demand scoring
- `TestOtherAnalyticsEngines` - Remaining analytics engines
- `TestAnalyticsIntegration` - Cross-engine integration

### ⚡ Analytics Performance Tests (`test_analytics_performance.py`)

**Purpose**: Test analytics performance under various conditions

**Coverage**:
- Large dataset processing (5000+ records)
- Memory usage monitoring
- Execution time benchmarks
- Concurrent execution testing
- Scalability analysis
- Memory leak detection
- Performance profiling

**Test Classes**:
- `TestCareerPathEnginePerformance` - Career path performance
- `TestAIReplacementRiskEnginePerformance` - Risk assessment performance
- `TestMarketDemandEnginePerformance` - Demand analysis performance
- `TestAnalyticsScalability` - Scalability testing
- `TestAnalyticsMemoryLeaks` - Memory leak detection
- `TestAnalyticsProfiling` - Detailed profiling

### 🔗 Analytics Integration Tests (`test_analytics_integration.py`)

**Purpose**: Test end-to-end analytics scenarios with realistic data

**Coverage**:
- Real-world career analysis workflows
- Career transition scenarios
- Experienced professional analysis
- Entry-level fresher analysis
- Market intelligence gathering
- Cross-domain consistency validation
- Data flow testing
- Error handling in integration

**Test Classes**:
- `TestRealWorldScenarios` - Realistic user scenarios
- `TestAnalyticsDataFlow` - Data flow validation
- `TestAnalyticsErrorHandling` - Integration error handling

### ⚡ Performance Tests

**Purpose**: Test performance under various conditions

**Coverage**:
- Large job lists (100+ jobs)
- Memory usage
- Execution time
- Concurrent operations

**Benchmarks**:
- Pipeline execution time
- Memory consumption
- Storage performance
- Scalability limits

## � Coverage Reports

### Scraping Pipelines Coverage
- **Location**: `tests/coverage_html/index.html`
- **Features**: Interactive coverage visualization
- **Usage**: Open in browser to explore coverage details

### Analytics Module Coverage
- **Location**: `tests/analytics_coverage_html/index.html`
- **Features**: Interactive coverage visualization for analytics engines
- **Usage**: Open in browser to explore analytics coverage details

### Coverage Metrics
- **Target**: >90% code coverage
- **Current**: Check coverage reports for latest results
- **Components Covered**:
  - **Scraping Pipelines**: Pipeline classes, storage handlers, scraper interfaces
  - **Analytics Module**: 15 analytics engines across 4 categories
    - Career Insights (2 engines)
    - Domain Analysis (4 engines)
    - Entry Barriers (4 engines)
    - Market Analysis (5 engines)

## 🐛 Error Handling Tests

### Test Scenarios

1. **Configuration Errors**
   - Missing extractors
   - Missing handlers
   - Invalid file paths

2. **Runtime Errors**
   - Scraper failures
   - Storage failures
   - Network issues

3. **Data Issues**
   - Empty results
   - Invalid data formats
   - Missing fields

4. **Edge Cases**
   - Large datasets
   - Special characters
   - Invalid input types

### Example Error Test
```python
def test_pipeline_run_extractor_failure(self):
    """Test pipeline execution with extractor failure"""
    failing_extractor = MockJobExtractor("FailingExtractor", should_fail=True)
    pipeline = NaukriGeneralJobDataExtractionPipeline(...)
    
    result = pipeline.run()
    
    self.assertEqual(result['failed_jobs'], 2)
    self.assertEqual(result['successful_jobs'], 0)
```

## 🔧 Test Configuration

### pytest.ini
```ini
[tool:pytest]
addopts = --verbose --cov=src/pipelines --cov-report=html
markers =
    unit: Unit tests
    integration: Integration tests
    performance: Performance tests
    database: Database tests
```

### Test Markers
```python
@pytest.mark.unit
def test_unit_scenario():
    pass

@pytest.mark.integration
def test_integration_scenario():
    pass

@pytest.mark.performance
def test_performance_scenario():
    pass
```

## 📝 Writing New Tests

### Test Structure
```python
class TestNewFeature(unittest.TestCase):
    """Test cases for new feature"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_extractor = MockJobExtractor("TestExtractor")
        self.mock_storage = MockStorageHandler("TestStorage")
    
    def test_feature_success_case(self):
        """Test successful scenario"""
        # Arrange
        # Act
        # Assert
        pass
    
    def test_feature_error_case(self):
        """Test error scenario"""
        # Arrange
        # Act
        # Assert
        pass
```

### Mock Objects
```python
class MockJobExtractor(JobExtractor):
    """Mock implementation for testing"""
    
    def __init__(self, name, should_fail=False):
        self.name = name
        self.should_fail = should_fail
    
    def extract(self, job_name, locations):
        if self.should_fail:
            raise Exception("Mock failure")
        return [mock_job_data]
    
    def get_name(self):
        return self.name
```

## 🚨 CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Scraping Pipelines

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r tests/requirements_test.txt
    - name: Run tests
      run: python tests/run_tests.py --all
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 📊 Test Reports

### Generated Reports
- **HTML Test Report**: `tests/test_report.html`
- **JSON Report**: `tests/test_report.json`
- **Coverage Report**: `tests/coverage_html/`
- **Benchmark Report**: `tests/benchmark.json`

### Report Analysis
```bash
# View coverage report
open tests/coverage_html/index.html

# View test report
open tests/test_report.html

# Analyze benchmarks
cat tests/benchmark.json | python -m json.tool
```

## 🛠️ Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Missing Dependencies**
   ```bash
   # Install test dependencies
   pip install -r tests/requirements_test.txt
   ```

3. **Database Connection Issues**
   ```bash
   # Skip database tests if no database available
   pytest tests/ -m "not database"
   ```

4. **Network Issues**
   ```bash
   # Skip network-dependent tests
   pytest tests/ -m "not network"
   ```

### Debug Mode
```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run specific test with debug
pytest tests/test_scraping_pipelines.py::TestNaukriGeneralPipeline::test_pipeline_run_success -v -s
```

## 📋 Test Checklist

### Before Submitting Code
- [ ] All unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Code coverage >90%
- [ ] No new test failures
- [ ] Performance tests within acceptable limits
- [ ] Code quality checks pass

### Test Review Criteria
- [ ] Tests cover all public methods
- [ ] Error scenarios are tested
- [ ] Edge cases are covered
- [ ] Mock objects are realistic
- [ ] Test assertions are meaningful
- [ ] Test names are descriptive

## 🔮 Future Enhancements

### Planned Test Improvements
1. **Visual Testing**: Screenshot-based UI testing
2. **Load Testing**: Higher volume performance testing
3. **Contract Testing**: API contract validation
4. **Chaos Testing**: Random failure injection
5. **Security Testing**: Input validation and security checks

### Test Metrics to Track
- Test execution time trends
- Coverage percentage changes
- Failure rate analysis
- Performance benchmark trends
- Code quality metrics

## 📞 Support

### Getting Help
- Check existing test files for examples
- Review pytest documentation
- Consult test reports for failure details
- Use debug mode for troubleshooting

### Contributing Tests
1. Follow existing test patterns
2. Use descriptive test names
3. Include setup and teardown
4. Mock external dependencies
5. Add appropriate test markers
6. Update documentation

---

**Last Updated**: 2025-03-14  
**Test Suite Version**: 1.0.0  
**Coverage Target**: >90%
