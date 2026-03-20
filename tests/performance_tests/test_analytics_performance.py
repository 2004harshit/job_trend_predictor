"""
Performance and Load Testing for Analytics Module
Stress testing, performance benchmarks, and scalability tests

Author: QA Team
Date: 2025-03-14
Purpose: Ensure analytics engines perform well under various loads
"""

import pytest
import unittest
import time
import psutil
import os
import sys
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import gc
import threading
import concurrent.futures
from memory_profiler import profile
import cProfile
import pstats
import io

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import analytics engines
from src.analytics.career_insights.career_path_engine import CareerPathEngine
from src.analytics.domain_analysis.ai_replacement_risk_engine import AIReplacementRiskEngine
from src.analytics.market_analysis.demand_score_calculator import MarketDemandEngine
from src.analytics.entry_barriers.interview_difficulty_engine import InterviewDifficultyEngine


class PerformanceTestCase(unittest.TestCase):
    """Base class for performance tests with common utilities"""
    
    def setUp(self):
        """Set up performance monitoring"""
        self.start_time = None
        self.start_memory = None
        self.process = psutil.Process()
    
    def start_performance_monitoring(self):
        """Start performance monitoring"""
        gc.collect()  # Clean up before measuring
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def stop_performance_monitoring(self):
        """Stop performance monitoring and return metrics"""
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'execution_time': end_time - self.start_time,
            'memory_used': end_memory - self.start_memory,
            'peak_memory': end_memory
        }
    
    def assert_performance_within_limits(self, metrics, max_time=None, max_memory=None):
        """Assert performance metrics are within acceptable limits"""
        if max_time:
            self.assertLessEqual(
                metrics['execution_time'], max_time,
                f"Execution time {metrics['execution_time']:.2f}s exceeds limit {max_time}s"
            )
        
        if max_memory:
            self.assertLessEqual(
                metrics['memory_used'], max_memory,
                f"Memory usage {metrics['memory_used']:.2f}MB exceeds limit {max_memory}MB"
            )
    
    def create_large_dataset(self, size=10000):
        """Create large dataset for performance testing"""
        np.random.seed(42)  # For reproducible tests
        
        job_types = ['data scientist', 'software engineer', 'ml engineer', 'backend developer', 'frontend developer']
        skills_combinations = [
            'python, machine learning, statistics',
            'java, spring, microservices',
            'python, tensorflow, deep learning',
            'node.js, react, mongodb',
            'python, django, postgresql'
        ]
        
        data = {
            'Job_Type': np.random.choice(job_types, size),
            'Title_Cleaned': [f'Senior {jt}' for jt in np.random.choice(job_types, size)],
            'Min_Experience': np.random.randint(0, 10, size),
            'Max_Experience': np.random.randint(2, 15, size),
            'Skills': np.random.choice(skills_combinations, size),
            'Salary_Lakhs': np.random.normal(15, 8, size),
            'Company_Cleaned': [f'Company_{i}' for i in np.random.randint(1, 1000, size)],
            'Location_Cleaned': np.random.choice(['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai'], size),
            'Description': [f'Job description {i}' for i in range(size)],
            'Scraped_At_Cleaned': pd.date_range('2023-01-01', periods=size, freq='H'),
            'Posted_Date': pd.date_range('2023-01-01', periods=size, freq='D')
        }
        
        return pd.DataFrame(data)


class TestCareerPathEnginePerformance(PerformanceTestCase):
    """Performance tests for CareerPathEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.engine = CareerPathEngine()
        self.large_dataset = self.create_large_dataset(5000)
    
    def test_large_dataset_filtering_performance(self):
        """Test domain filtering performance with large dataset"""
        self.start_performance_monitoring()
        
        # Test filtering multiple domains
        domains = ['data scientist', 'software engineer', 'ml engineer']
        for domain in domains:
            result = self.engine._filter_domain(self.large_dataset, domain)
            self.assertIsInstance(result, pd.DataFrame)
        
        metrics = self.stop_performance_monitoring()
        
        # Should complete within 2 seconds for 5000 records
        self.assert_performance_within_limits(metrics, max_time=2.0, max_memory=50)
    
    def test_skill_extraction_performance(self):
        """Test skill extraction performance"""
        domain_df = self.engine._filter_domain(self.large_dataset, 'data scientist')
        
        self.start_performance_monitoring()
        
        result = self.engine._extract_required_skills(domain_df)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        self.assert_performance_within_limits(metrics, max_time=1.0, max_memory=20)
    
    def test_learning_path_calculation_performance(self):
        """Test learning path calculation performance"""
        user_skills = ['python', 'sql', 'basic_ml']
        target_role = 'data scientist'
        
        self.start_performance_monitoring()
        
        result = self.engine.calculate_learning_path(user_skills, target_role, 'basic')
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        self.assert_performance_within_limits(metrics, max_time=1.5, max_memory=30)
    
    def test_concurrent_learning_path_calculations(self):
        """Test concurrent learning path calculations"""
        user_skills_list = [
            ['python', 'sql'],
            ['java', 'spring'],
            ['javascript', 'react'],
            ['python', 'ml'],
            ['node.js', 'express']
        ]
        target_roles = ['data scientist', 'software engineer', 'frontend developer', 'ml engineer', 'backend developer']
        
        self.start_performance_monitoring()
        
        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i, (skills, role) in enumerate(zip(user_skills_list, target_roles)):
                future = executor.submit(
                    self.engine.calculate_learning_path, 
                    skills, role, 'basic'
                )
                futures.append(future)
            
            # Wait for all to complete
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsInstance(result, dict)
        
        # Should complete within 3 seconds for 5 concurrent calculations
        self.assert_performance_within_limits(metrics, max_time=3.0, max_memory=80)
    
    @profile
    def test_memory_usage_with_large_skill_sets(self):
        """Test memory usage with large skill sets"""
        large_skill_set = [f'skill_{i}' for i in range(1000)]
        target_role = 'data scientist'
        
        self.start_performance_monitoring()
        
        result = self.engine.calculate_learning_path(large_skill_set, target_role, 'basic')
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        # Memory usage should be reasonable even with 1000 skills
        self.assert_performance_within_limits(metrics, max_time=5.0, max_memory=100)


class TestAIReplacementRiskEnginePerformance(PerformanceTestCase):
    """Performance tests for AIReplacementRiskEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.engine = AIReplacementRiskEngine()
        self.large_dataset = self.create_large_dataset(3000)
    
    def test_risk_calculation_performance(self):
        """Test automation risk calculation performance"""
        role = 'data scientist'
        skills = ['python', 'machine learning', 'statistics', 'deep learning', 'nlp']
        
        self.start_performance_monitoring()
        
        result = self.engine.calculate_automation_risk(role, skills)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        self.assert_performance_within_limits(metrics, max_time=1.0, max_memory=20)
    
    def test_batch_risk_analysis_performance(self):
        """Test batch risk analysis performance"""
        roles = ['data scientist', 'software engineer', 'ml engineer', 'frontend developer', 'backend developer']
        skills_sets = [
            ['python', 'ml'],
            ['java', 'spring'],
            ['javascript', 'react'],
            ['python', 'django'],
            ['node.js', 'express']
        ]
        
        self.start_performance_monitoring()
        
        results = []
        for role, skills in zip(roles, skills_sets):
            result = self.engine.calculate_automation_risk(role, skills)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 5)
        self.assert_performance_within_limits(metrics, max_time=2.0, max_memory=50)
    
    def test_task_composition_analysis_performance(self):
        """Test task composition analysis performance"""
        descriptions = [
            "Strategic analysis and creative problem solving with client consultation and stakeholder management",
            "Routine data entry and report generation using templates and standardized procedures",
            "Complex system design and architectural decisions with distributed systems and cloud technologies",
            "Machine learning model development and deep learning research with innovative algorithms"
        ] * 1000  # 4000 descriptions
        
        self.start_performance_monitoring()
        
        results = []
        for description in descriptions:
            result = self.engine.analyze_task_composition(description)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 4000)
        self.assert_performance_within_limits(metrics, max_time=5.0, max_memory=150)
    
    def test_future_proof_skills_analysis_performance(self):
        """Test future-proof skills analysis performance"""
        domains = ['data science', 'software engineering', 'machine learning', 'artificial intelligence', 'cybersecurity']
        
        self.start_performance_monitoring()
        
        results = []
        for domain in domains:
            result = self.engine.identify_future_proof_skills(domain)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 5)
        self.assert_performance_within_limits(metrics, max_time=2.0, max_memory=40)


class TestMarketDemandEnginePerformance(PerformanceTestCase):
    """Performance tests for MarketDemandEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.large_dataset = self.create_large_dataset(10000)
        self.engine = MarketDemandEngine(self.large_dataset)
    
    def test_demand_score_calculation_performance(self):
        """Test demand score calculation performance with large dataset"""
        domains = ['data scientist', 'software engineer', 'ml engineer', 'frontend developer', 'backend developer']
        
        self.start_performance_monitoring()
        
        result = self.engine.calculate_demand_score(domains)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        self.assert_performance_within_limits(metrics, max_time=3.0, max_memory=100)
    
    def test_fresher_data_filtering_performance(self):
        """Test fresher data filtering performance"""
        self.start_performance_monitoring()
        
        result = self.engine._filter_fresher_data(self.large_dataset)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, pd.DataFrame)
        self.assert_performance_within_limits(metrics, max_time=1.0, max_memory=50)
    
    def test_frequency_score_calculation_performance(self):
        """Test frequency score calculation performance"""
        fresher_df = self.engine._filter_fresher_data(self.large_dataset)
        domains = ['data scientist', 'software engineer', 'ml engineer']
        max_freq = 1000
        
        self.start_performance_monitoring()
        
        results = []
        for domain in domains:
            result = self.engine._calculate_frequency_score(fresher_df, domain, max_freq)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 3)
        self.assert_performance_within_limits(metrics, max_time=2.0, max_memory=60)
    
    def test_trend_analysis_performance(self):
        """Test trend analysis performance"""
        fresher_df = self.engine._filter_fresher_data(self.large_dataset)
        domain = 'data scientist'
        
        # Define time periods
        first_this = pd.Timestamp('2023-02-01')
        first_prev = pd.Timestamp('2023-01-01')
        last_prev = pd.Timestamp('2023-01-31')
        
        self.start_performance_monitoring()
        
        result = self.engine._calculate_trend_score(fresher_df, domain, first_this, first_prev, last_prev)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, (int, float))
        self.assert_performance_within_limits(metrics, max_time=1.5, max_memory=40)


class TestInterviewDifficultyEnginePerformance(PerformanceTestCase):
    """Performance tests for InterviewDifficultyEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.engine = InterviewDifficultyEngine()
        self.large_dataset = self.create_large_dataset(5000)
    
    def test_difficulty_calculation_performance(self):
        """Test interview difficulty calculation performance"""
        role = 'data scientist'
        
        self.start_performance_monitoring()
        
        result = self.engine.calculate_interview_difficulty(self.large_dataset, role)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertIsInstance(result, dict)
        self.assert_performance_within_limits(metrics, max_time=2.0, max_memory=60)
    
    def test_preparation_time_estimation_performance(self):
        """Test preparation time estimation performance"""
        role = 'data scientist'
        candidate_profiles = [
            {'skills': ['python', 'basic_ml'], 'experience_years': 2, 'dsa_level': 'beginner'},
            {'skills': ['java', 'spring'], 'experience_years': 3, 'dsa_level': 'intermediate'},
            {'skills': ['javascript', 'react'], 'experience_years': 1, 'dsa_level': 'beginner'},
            {'skills': ['python', 'django'], 'experience_years': 4, 'dsa_level': 'advanced'},
            {'skills': ['node.js', 'express'], 'experience_years': 2, 'dsa_level': 'intermediate'}
        ]
        
        self.start_performance_monitoring()
        
        results = []
        for profile in candidate_profiles:
            result = self.engine.estimate_preparation_time(role, profile)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 5)
        self.assert_performance_within_limits(metrics, max_time=3.0, max_memory=80)
    
    def test_skill_requirements_analysis_performance(self):
        """Test skill requirements analysis performance"""
        roles = ['data scientist', 'software engineer', 'ml engineer', 'frontend developer', 'backend developer']
        
        self.start_performance_monitoring()
        
        results = []
        for role in roles:
            result = self.engine.analyze_skill_requirements(self.large_dataset, role)
            results.append(result)
        
        metrics = self.stop_performance_monitoring()
        
        self.assertEqual(len(results), 5)
        self.assert_performance_within_limits(metrics, max_time=4.0, max_memory=100)


class TestAnalyticsScalability(PerformanceTestCase):
    """Scalability tests for analytics module"""
    
    def test_scalability_with_increasing_dataset_sizes(self):
        """Test how analytics engines scale with increasing dataset sizes"""
        sizes = [1000, 5000, 10000, 20000]
        engine = CareerPathEngine()
        
        performance_results = {}
        
        for size in sizes:
            dataset = self.create_large_dataset(size)
            
            self.start_performance_monitoring()
            
            # Test domain filtering (common operation)
            result = engine._filter_domain(dataset, 'data scientist')
            
            metrics = self.stop_performance_monitoring()
            performance_results[size] = metrics
        
        # Check that performance scales reasonably
        # Execution time should not increase exponentially
        times = [performance_results[size]['execution_time'] for size in sizes]
        
        # Each 5x increase in data should not result in more than 5x increase in time
        for i in range(1, len(times)):
            ratio = times[i] / times[i-1]
            data_ratio = sizes[i] / sizes[i-1]
            self.assertLessEqual(ratio, data_ratio * 1.5, 
                              f"Performance degradation too high: {ratio:.2f}x time increase for {data_ratio}x data increase")
    
    def test_memory_scalability(self):
        """Test memory usage scalability"""
        sizes = [1000, 5000, 10000]
        engine = AIReplacementRiskEngine()
        
        memory_results = {}
        
        for size in sizes:
            dataset = self.create_large_dataset(size)
            
            self.start_performance_monitoring()
            
            # Test memory-intensive operation
            for i in range(min(100, size)):  # Limit iterations for large datasets
                role = 'data scientist'
                skills = ['python', 'ml', 'statistics']
                result = engine.calculate_automation_risk(role, skills)
            
            metrics = self.stop_performance_monitoring()
            memory_results[size] = metrics['memory_used']
        
        # Check memory usage doesn't grow excessively
        for i in range(1, len(sizes)):
            memory_ratio = memory_results[sizes[i]] / memory_results[sizes[i-1]]
            data_ratio = sizes[i] / sizes[i-1]
            self.assertLessEqual(memory_ratio, data_ratio * 2.0,
                              f"Memory usage too high: {memory_ratio:.2f}x memory increase for {data_ratio}x data increase")
    
    def test_concurrent_execution_scalability(self):
        """Test concurrent execution scalability"""
        engine = CareerPathEngine()
        num_threads = [1, 2, 4, 8]
        
        concurrency_results = {}
        
        for threads in num_threads:
            user_skills = [['python', 'sql']] * threads
            target_roles = ['data scientist'] * threads
            
            self.start_performance_monitoring()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                futures = []
                for skills, role in zip(user_skills, target_roles):
                    future = executor.submit(
                        engine.calculate_learning_path,
                        skills, role, 'basic'
                    )
                    futures.append(future)
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            metrics = self.stop_performance_monitoring()
            concurrency_results[threads] = {
                'metrics': metrics,
                'results_count': len(results)
            }
        
        # Check that concurrent execution provides benefits
        single_thread_time = concurrency_results[1]['metrics']['execution_time']
        multi_thread_time = concurrency_results[4]['metrics']['execution_time']
        
        # 4 threads should be faster than 1 thread (considering overhead)
        efficiency_ratio = single_thread_time / multi_thread_time
        self.assertGreater(efficiency_ratio, 1.5, 
                          f"Concurrent execution not efficient enough: {efficiency_ratio:.2f}x speedup with 4 threads")


class TestAnalyticsMemoryLeaks(PerformanceTestCase):
    """Memory leak detection tests"""
    
    def test_career_path_engine_memory_leaks(self):
        """Test CareerPathEngine for memory leaks"""
        engine = CareerPathEngine()
        dataset = self.create_large_dataset(1000)
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Run multiple operations
        for i in range(100):
            result = engine.calculate_learning_path(['python', 'sql'], 'data scientist', 'basic')
            del result  # Explicit cleanup
            
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (< 50MB)
        self.assertLess(memory_increase, 50, 
                       f"Potential memory leak detected: {memory_increase:.2f}MB increase")
    
    def test_market_demand_engine_memory_leaks(self):
        """Test MarketDemandEngine for memory leaks"""
        dataset = self.create_large_dataset(2000)
        engine = MarketDemandEngine(dataset)
        
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Run multiple calculations
        for i in range(50):
            domains = ['data scientist', 'software engineer']
            result = engine.calculate_demand_score(domains)
            del result
            
            if i % 10 == 0:
                gc.collect()
        
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        self.assertLess(memory_increase, 30, 
                       f"Potential memory leak in MarketDemandEngine: {memory_increase:.2f}MB increase")


class TestAnalyticsProfiling(PerformanceTestCase):
    """Profiling tests for detailed performance analysis"""
    
    def test_profile_career_path_engine(self):
        """Profile CareerPathEngine operations"""
        engine = CareerPathEngine()
        dataset = self.create_large_dataset(5000)
        
        # Create profiler
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Profile the operation
        start_time = time.time()
        result = engine.calculate_learning_path(['python', 'sql', 'ml'], 'data scientist', 'basic')
        end_time = time.time()
        
        profiler.disable()
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        profiling_output = s.getvalue()
        
        # Print profiling information
        print(f"\nCareer Path Engine Profiling Results:")
        print(f"Total execution time: {end_time - start_time:.4f}s")
        print(f"Top 20 functions by cumulative time:")
        print(profiling_output)
        
        self.assertIsInstance(result, dict)
        self.assertLess(end_time - start_time, 2.0)  # Should complete within 2 seconds
    
    def test_profile_ai_risk_engine(self):
        """Profile AIReplacementRiskEngine operations"""
        engine = AIReplacementRiskEngine()
        
        # Create profiler
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Profile the operation
        start_time = time.time()
        result = engine.calculate_automation_risk('data scientist', ['python', 'ml', 'statistics'])
        end_time = time.time()
        
        profiler.disable()
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)
        
        profiling_output = s.getvalue()
        
        # Print profiling information
        print(f"\nAI Risk Engine Profiling Results:")
        print(f"Total execution time: {end_time - start_time:.4f}s")
        print(f"Top 20 functions by cumulative time:")
        print(profiling_output)
        
        self.assertIsInstance(result, dict)
        self.assertLess(end_time - start_time, 1.0)  # Should complete within 1 second


def create_performance_test_suite():
    """Create and return a performance test suite"""
    suite = unittest.TestSuite()
    
    # Add performance test classes
    test_classes = [
        TestCareerPathEnginePerformance,
        TestAIReplacementRiskEnginePerformance,
        TestMarketDemandEnginePerformance,
        TestInterviewDifficultyEnginePerformance,
        TestAnalyticsScalability,
        TestAnalyticsMemoryLeaks,
        TestAnalyticsProfiling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_performance_tests():
    """Run performance tests with detailed reporting"""
    print("Running Analytics Module Performance Tests")
    print("="*60)
    
    # Monitor system resources before tests
    initial_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
    initial_cpu = psutil.cpu_percent(interval=1)
    
    print(f"Initial system memory usage: {initial_memory:.2f}MB")
    print(f"Initial CPU usage: {initial_cpu:.1f}%")
    print()
    
    # Create and run test suite
    suite = create_performance_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Monitor system resources after tests
    final_memory = psutil.virtual_memory().used / 1024 / 1024  # MB
    final_cpu = psutil.cpu_percent(interval=1)
    
    print(f"\nFinal system memory usage: {final_memory:.2f}MB")
    print(f"Final CPU usage: {final_cpu:.1f}%")
    print(f"Memory change: {final_memory - initial_memory:.2f}MB")
    
    # Performance summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Configure logging for performance tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = run_performance_tests()
    
    if success:
        print("\n✅ All performance tests passed!")
        exit(0)
    else:
        print("\n❌ Some performance tests failed!")
        exit(1)
