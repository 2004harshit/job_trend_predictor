"""
Test Runner - Execute all unit tests
Job Trend Predictor - Test Suite
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_cleaner_tests():
    """Run all cleaner tests."""
    print("🧹 Running Cleaner Tests...")
    
    # Discover and run cleaner tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/cleaners', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_scraper_tests():
    """Run all scraper tests."""
    print("🕷️  Running Scraper Tests...")
    
    # Discover and run scraper tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/scrapers', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_storage_tests():
    """Run all storage tests."""
    print("💾 Running Storage Tests...")
    
    # Discover and run storage tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/storage', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_pipeline_tests():
    """Run all pipeline tests."""
    print("🔄 Running Pipeline Tests...")
    
    # Discover and run pipeline tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests/pipeline', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_all_tests():
    """Run all tests and return overall result."""
    print("🚀 Running All Unit Tests...")
    print("=" * 50)
    
    results = []
    
    # Run all test suites
    results.append(run_cleaner_tests())
    print()
    
    results.append(run_scraper_tests())
    print()
    
    results.append(run_storage_tests())
    print()
    
    results.append(run_pipeline_tests())
    print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Summary:")
    
    test_suites = ["Cleaners", "Scrapers", "Storage", "Pipelines"]
    for i, (suite_name, success) in enumerate(zip(test_suites, results)):
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {suite_name:<10} : {status}")
    
    overall_success = all(results)
    overall_status = "✅ ALL PASSED" if overall_success else "❌ SOME FAILED"
    
    print(f"\n🎯 Overall: {overall_status}")
    print("=" * 50)
    
    return overall_success

def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Job Trend Predictor unit tests")
    parser.add_argument(
        '--suite', 
        choices=['cleaners', 'scrapers', 'storage', 'pipelines', 'all'],
        default='all',
        help='Test suite to run (default: all)'
    )
    
    args = parser.parse_args()
    
    if args.suite == 'cleaners':
        success = run_cleaner_tests()
    elif args.suite == 'scrapers':
        success = run_scraper_tests()
    elif args.suite == 'storage':
        success = run_storage_tests()
    elif args.suite == 'pipelines':
        success = run_pipeline_tests()
    else:
        success = run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
