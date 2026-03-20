#!/usr/bin/env python3
"""
Test Runner Script for Scraping Pipelines
Comprehensive test execution with reporting and coverage

Author: QA Team
Date: 2025-03-14
Usage: python run_tests.py [options]
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description, cwd=None):
    """Run a command and handle the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or project_root,
            capture_output=True,
            text=True,
            check=True
        )
        
        elapsed_time = time.time() - start_time
        print(f"✅ {description} completed successfully in {elapsed_time:.2f}s")
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        return True, result.stdout, result.stderr
        
    except subprocess.CalledProcessError as e:
        elapsed_time = time.time() - start_time
        print(f"❌ {description} failed after {elapsed_time:.2f}s")
        print(f"Return code: {e.returncode}")
        
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        
        return False, e.stdout, e.stderr


def check_dependencies():
    """Check if test dependencies are installed"""
    print("Checking test dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-cov',
        'pytest-mock',
        'coverage'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r tests/requirements_test.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests only"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "-m", "unit",
        "tests/test_scraping_pipelines.py",
        "--tb=short"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/pipelines",
            "--cov=src/scrapers", 
            "--cov=src/storage",
            "--cov-report=html:tests/coverage_html",
            "--cov-report=term-missing"
        ])
    
    success, stdout, stderr = run_command(cmd, "Unit Tests")
    return success


def run_integration_tests(verbose=False):
    """Run integration tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "-m", "integration",
        "tests/test_pipeline_integration.py",
        "--tb=short"
    ])
    
    success, stdout, stderr = run_command(cmd, "Integration Tests")
    return success


def run_all_tests(verbose=False, coverage=True):
    """Run all tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "tests/",
        "--tb=short",
        "--html=tests/test_report.html",
        "--self-contained-html"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/pipelines",
            "--cov=src/scrapers",
            "--cov=src/storage", 
            "--cov-report=html:tests/coverage_html",
            "--cov-report=xml:tests/coverage.xml",
            "--cov-report=term-missing"
        ])
    
    success, stdout, stderr = run_command(cmd, "All Tests")
    return success


def run_performance_tests():
    """Run performance tests"""
    cmd = [
        "python", "-m", "pytest",
        "-m", "performance",
        "tests/test_scraping_pipelines.py::TestPipelinePerformance",
        "--benchmark-only",
        "--benchmark-json=tests/benchmark.json"
    ]
    
    success, stdout, stderr = run_command(cmd, "Performance Tests")
    return success


def run_code_quality_checks():
    """Run code quality checks on test files"""
    print("Running code quality checks on test files...")
    
    # Black formatting check
    success, _, _ = run_command(
        ["black", "--check", "tests/"],
        "Black Formatting Check"
    )
    
    if not success:
        print("Run 'black tests/' to fix formatting issues")
        return False
    
    # Flake8 linting
    success, _, _ = run_command(
        ["flake8", "tests/", "--max-line-length=100", "--ignore=E203,W503"],
        "Flake8 Linting"
    )
    
    if not success:
        return False
    
    print("✅ All code quality checks passed")
    return True


def generate_test_report():
    """Generate comprehensive test report"""
    print("Generating test report...")
    
    # Create test report directory
    test_reports_dir = project_root / "tests" / "reports"
    test_reports_dir.mkdir(exist_ok=True)
    
    # Generate summary report
    report_content = f"""
# Scraping Pipelines Test Report
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

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
"""
    
    report_file = test_reports_dir / "README.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Test report generated: {report_file}")
    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Test Runner for Scraping Pipelines")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quality-check", action="store_true", help="Run code quality checks")
    parser.add_argument("--report-only", action="store_true", help="Generate report only")
    
    args = parser.parse_args()
    
    print("🧪 Scraping Pipelines Test Runner")
    print("="*60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create test directories
    (project_root / "tests" / "coverage_html").mkdir(exist_ok=True)
    (project_root / "tests" / "reports").mkdir(exist_ok=True)
    
    # Run code quality checks if requested
    if args.quality_check:
        if not run_code_quality_checks():
            print("❌ Code quality checks failed")
            sys.exit(1)
    
    # Generate report only if requested
    if args.report_only:
        generate_test_report()
        sys.exit(0)
    
    # Determine which tests to run
    coverage = not args.no_coverage
    all_success = True
    
    if args.unit:
        all_success &= run_unit_tests(args.verbose, coverage)
    elif args.integration:
        all_success &= run_integration_tests(args.verbose)
    elif args.performance:
        all_success &= run_performance_tests()
    else:  # Default: run all tests
        all_success &= run_all_tests(args.verbose, coverage)
    
    # Generate test report
    generate_test_report()
    
    # Final summary
    print(f"\n{'='*60}")
    if all_success:
        print("✅ All tests completed successfully!")
        print(f"📊 Coverage report: tests/coverage_html/index.html")
        print(f"📄 Test report: tests/test_report.html")
    else:
        print("❌ Some tests failed!")
        print("Check the output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
