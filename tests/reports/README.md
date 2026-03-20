
# Scraping Pipelines Test Report
Generated on: 2026-03-15 08:46:57

## Test Coverage
- HTML Report: tests/coverage_html/index.html
- XML Report: tests/coverage.xml

## Test Results
- HTML Report: tests/test_report.html
- JSON Report: tests/test_report.json

## Performance Benchmarks
- Benchmark Results: tests/benchmark.json (if performance tests were run)

## Test Categories
- Unit Tests: Fast, isolated tests for individual components
- Integration Tests: End-to-end tests with real components
- Performance Tests: Load and timing tests
- Error Handling Tests: Failure scenarios and recovery

## Running Tests
```bash
# Run all tests
python tests/run_tests.py --all

# Run unit tests only
python tests/run_tests.py --unit

# Run integration tests only
python tests/run_tests.py --integration

# Run performance tests
python tests/run_tests.py --performance

# Run with verbose output
python tests/run_tests.py --all --verbose
```
