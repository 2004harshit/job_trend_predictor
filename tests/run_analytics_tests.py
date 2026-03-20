#!/usr/bin/env python3
"""
Analytics Module Test Runner
Comprehensive test execution for all analytics engines

Author: QA Team
Date: 2025-03-14
Usage: python run_analytics_tests.py [options]
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


def check_analytics_dependencies():
    """Check if analytics dependencies are available"""
    print("Checking analytics module dependencies...")
    
    # Check if analytics modules can be imported
    required_modules = [
        'src.analytics.career_insights.career_path_engine',
        'src.analytics.domain_analysis.ai_replacement_risk_engine',
        'src.analytics.market_analysis.demand_score_calculator',
        'src.analytics.entry_barriers.interview_difficulty_engine'
    ]
    
    available_modules = []
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module.replace('.', '_'))
            available_modules.append(module)
            print(f"✅ {module} is available")
        except ImportError as e:
            missing_modules.append(module)
            print(f"❌ {module} is missing: {e}")
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        print("Make sure the analytics module is properly structured")
        return False
    
    print("✅ All analytics dependencies are available")
    return True


def run_unit_tests(verbose=False, coverage=True):
    """Run analytics unit tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "-m", "unit",
        "tests/test_analytics_module.py",
        "--tb=short"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/analytics",
            "--cov-report=html:tests/analytics_coverage_html",
            "--cov-report=term-missing"
        ])
    
    success, stdout, stderr = run_command(cmd, "Analytics Unit Tests")
    return success


def run_performance_tests(verbose=False):
    """Run analytics performance tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "-m", "performance",
        "tests/test_analytics_performance.py",
        "--tb=short"
    ])
    
    success, stdout, stderr = run_command(cmd, "Analytics Performance Tests")
    return success


def run_integration_tests(verbose=False):
    """Run analytics integration tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "-m", "integration",
        "tests/test_analytics_integration.py",
        "--tb=short"
    ])
    
    success, stdout, stderr = run_command(cmd, "Analytics Integration Tests")
    return success


def run_all_analytics_tests(verbose=False, coverage=True):
    """Run all analytics tests"""
    cmd = ["python", "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    
    cmd.extend([
        "tests/test_analytics_module.py",
        "tests/test_analytics_performance.py", 
        "tests/test_analytics_integration.py",
        "--tb=short",
        "--html=tests/analytics_test_report.html",
        "--self-contained-html"
    ])
    
    if coverage:
        cmd.extend([
            "--cov=src/analytics",
            "--cov-report=html:tests/analytics_coverage_html",
            "--cov-report=xml:tests/analytics_coverage.xml",
            "--cov-report=term-missing"
        ])
    
    success, stdout, stderr = run_command(cmd, "All Analytics Tests")
    return success


def run_analytics_benchmarks():
    """Run analytics performance benchmarks"""
    cmd = [
        "python", "-m", "pytest",
        "-m", "performance",
        "tests/test_analytics_performance.py::TestAnalyticsProfiling",
        "--benchmark-only",
        "--benchmark-json=tests/analytics_benchmark.json"
    ]
    
    success, stdout, stderr = run_command(cmd, "Analytics Benchmarks")
    return success


def validate_analytics_structure():
    """Validate analytics module structure"""
    print("Validating analytics module structure...")
    
    analytics_path = project_root / "src" / "analytics"
    
    if not analytics_path.exists():
        print(f"❌ Analytics directory not found: {analytics_path}")
        return False
    
    # Check required subdirectories
    required_subdirs = [
        "career_insights",
        "domain_analysis", 
        "entry_barriers",
        "market_analysis"
    ]
    
    missing_subdirs = []
    for subdir in required_subdirs:
        subdir_path = analytics_path / subdir
        if not subdir_path.exists():
            missing_subdirs.append(subdir)
        else:
            print(f"✅ {subdir} directory exists")
    
    if missing_subdirs:
        print(f"❌ Missing subdirectories: {', '.join(missing_subdirs)}")
        return False
    
    # Check for Python files in each subdirectory
    for subdir in required_subdirs:
        subdir_path = analytics_path / subdir
        py_files = list(subdir_path.glob("*.py"))
        py_files = [f for f in py_files if f.name != "__init__.py"]
        
        if py_files:
            print(f"✅ {subdir}: {len(py_files)} engine files found")
        else:
            print(f"⚠️  {subdir}: No engine files found")
    
    print("✅ Analytics module structure validation completed")
    return True


def generate_analytics_test_report():
    """Generate comprehensive analytics test report"""
    print("Generating analytics test report...")
    
    # Create test report directory
    test_reports_dir = project_root / "tests" / "analytics_reports"
    test_reports_dir.mkdir(exist_ok=True)
    
    # Generate summary report
    report_content = f"""
# Analytics Module Test Report
Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Coverage
- HTML Report: tests/analytics_coverage_html/index.html
- XML Report: tests/analytics_coverage.xml

## Test Results
- HTML Report: tests/analytics_test_report.html
- JSON Report: tests/analytics_test_report.json

## Performance Benchmarks
- Benchmark Results: tests/analytics_benchmark.json (if performance tests were run)

## Test Categories
- Unit Tests: Individual engine testing with mocked dependencies
- Performance Tests: Load testing, memory usage, and scalability
- Integration Tests: End-to-end scenarios with realistic data

## Analytics Engines Tested
### Career Insights
- CareerPathEngine: Learning path calculation and readiness assessment
- RoleEvaluationEngine: Role fit analysis and comparison

### Domain Analysis  
- AIReplacementRiskEngine: Automation risk assessment
- DomainStabilityEngine: Market volatility and growth analysis
- SalaryGrowthEngine: Salary trajectory and premium skill analysis
- SkillTransferabilityEngine: Cross-domain skill mapping

### Entry Barriers
- InterviewDifficultyEngine: Interview complexity assessment
- HiddenBlockerDetector: Non-obvious barrier identification
- PrequisiteEngine: Educational and skill requirements
- ProjectComplexityEvaluator: Project requirements analysis

### Market Analysis
- DemandScoreCalculator: Market demand scoring
- AverageSalaryCalculator: Salary benchmarking
- CompetitionLevelCalculator: Competition analysis
- JobMarketVelocityCalculator: Market dynamics
- SaturationRiskIndicator: Market saturation analysis

## Running Analytics Tests
```bash
# Run all analytics tests
python tests/run_analytics_tests.py --all

# Run unit tests only
python tests/run_analytics_tests.py --unit

# Run performance tests only
python tests/run_analytics_tests.py --performance

# Run integration tests only
python tests/run_analytics_tests.py --integration

# Run with verbose output
python tests/run_analytics_tests.py --all --verbose
```

## Test Data
- Realistic job market data with 5000+ records
- Multiple job types and skill combinations
- Real salary ranges and experience levels
- Geographic distribution across major Indian cities

## Performance Benchmarks
- Career path calculation: < 2 seconds
- AI risk assessment: < 1 second  
- Market demand analysis: < 3 seconds
- Memory usage: < 100MB for typical operations
- Concurrent execution: Efficient scaling with multiple threads

## Coverage Targets
- Overall Coverage: >90%
- Career Insights: >95%
- Domain Analysis: >90%
- Entry Barriers: >90%
- Market Analysis: >90%
"""
    
    report_file = test_reports_dir / "README.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"✅ Analytics test report generated: {report_file}")
    return True


def main():
    """Main test runner function for analytics module"""
    parser = argparse.ArgumentParser(description="Analytics Module Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--all", action="store_true", help="Run all analytics tests (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--benchmarks", action="store_true", help="Run performance benchmarks")
    parser.add_argument("--validate", action="store_true", help="Validate module structure only")
    parser.add_argument("--report-only", action="store_true", help="Generate report only")
    
    args = parser.parse_args()
    
    print("🧪 Analytics Module Test Runner")
    print("="*60)
    
    # Validate module structure
    if not validate_analytics_structure():
        print("❌ Module structure validation failed")
        sys.exit(1)
    
    # Generate report only if requested
    if args.report_only:
        generate_analytics_test_report()
        sys.exit(0)
    
    # Run benchmarks if requested
    if args.benchmarks:
        success = run_analytics_benchmarks()
        if not success:
            print("❌ Some benchmarks failed")
            sys.exit(1)
        print("✅ Benchmarks completed")
        sys.exit(0)
    
    # Create test directories
    (project_root / "tests" / "analytics_coverage_html").mkdir(exist_ok=True)
    (project_root / "tests" / "analytics_reports").mkdir(exist_ok=True)
    
    # Determine which tests to run
    coverage = not args.no_coverage
    all_success = True
    
    if args.unit:
        all_success &= run_unit_tests(args.verbose, coverage)
    elif args.performance:
        all_success &= run_performance_tests(args.verbose)
    elif args.integration:
        all_success &= run_integration_tests(args.verbose)
    else:  # Default: run all tests
        all_success &= run_all_analytics_tests(args.verbose, coverage)
    
    # Generate test report
    generate_analytics_test_report()
    
    # Final summary
    print(f"\n{'='*60}")
    if all_success:
        print("✅ All analytics tests completed successfully!")
        print(f"📊 Coverage report: tests/analytics_coverage_html/index.html")
        print(f"📄 Test report: tests/analytics_test_report.html")
    else:
        print("❌ Some analytics tests failed!")
        print("Check the output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
