"""
Integration Tests for Analytics Module
End-to-end testing with real data scenarios and cross-engine validation

Author: QA Team
Date: 2025-03-14
Purpose: Validate analytics module integration with real-world scenarios
"""

import pytest
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Any
import tempfile
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all analytics engines
from src.analytics.career_insights.career_path_engine import CareerPathEngine
from src.analytics.career_insights.role_evaluation_engine import RoleEvaluationEngine
from src.analytics.domain_analysis.ai_replacement_risk_engine import AIReplacementRiskEngine
from src.analytics.domain_analysis.domain_stability_engine import DomainStabilityEngine
from src.analytics.domain_analysis.salary_growth_engine import SalaryGrowthEngine
from src.analytics.domain_analysis.skill_transferability_engine import SkillTransferabilityEngine
from src.analytics.entry_barriers.interview_difficulty_engine import InterviewDifficultyEngine
from src.analytics.entry_barriers.hidden_blocker_detector import HiddenBlockerDetector
from src.analytics.entry_barriers.prequisite_engine import PrequisiteEngine
from src.analytics.entry_barriers.project_complexity_evaluator import ProjectComplexityEvaluator
from src.analytics.market_analysis.demand_score_calculator import MarketDemandEngine
from src.analytics.market_analysis.average_salary_calculator import AverageSalaryCalculator
from src.analytics.market_analysis.competition_level_calculator import CompetitionLevelCalculator
from src.analytics.market_analysis.job_market_velocity_calculator import JobMarketVelocityCalculator
from src.analytics.market_analysis.saturation_risk_indicator import SaturationRiskIndicator


class TestRealWorldScenarios(unittest.TestCase):
    """Integration tests with real-world scenarios"""
    
    def setUp(self):
        """Set up realistic test data"""
        # Create realistic job market data
        np.random.seed(42)  # For reproducible tests
        
        # Generate realistic data distribution
        job_types = ['data scientist', 'software engineer', 'ml engineer', 'backend developer', 
                     'frontend developer', 'full stack developer', 'devops engineer', 'data analyst']
        
        # Weighted distribution (more common roles appear more frequently)
        job_weights = [0.15, 0.25, 0.10, 0.15, 0.10, 0.10, 0.08, 0.07]
        
        size = 5000
        job_data = np.random.choice(job_types, size=size, p=job_weights)
        
        # Realistic salary ranges by role
        salary_ranges = {
            'data scientist': (8, 35),
            'software engineer': (6, 25),
            'ml engineer': (12, 45),
            'backend developer': (7, 28),
            'frontend developer': (6, 22),
            'full stack developer': (8, 30),
            'devops engineer': (10, 32),
            'data analyst': (5, 18)
        }
        
        salaries = []
        for job in job_data:
            min_sal, max_sal = salary_ranges[job]
            salaries.append(np.random.normal((min_sal + max_sal) / 2, (max_sal - min_sal) / 6))
        
        # Realistic skill combinations by role
        skill_templates = {
            'data scientist': ['python, machine learning, statistics, sql, tensorflow',
                              'r, python, data analysis, machine learning, deep learning',
                              'python, pandas, numpy, scikit-learn, nlp'],
            'software engineer': ['java, spring, microservices, sql, git',
                                  'python, django, rest api, postgresql, docker',
                                  'javascript, node.js, express, mongodb, react'],
            'ml engineer': ['python, tensorflow, pytorch, kubernetes, aws',
                            'python, machine learning, deep learning, mlops, gitlab ci'],
            'backend developer': ['java, spring boot, mysql, redis, kafka',
                                 'python, flask, postgresql, docker, nginx'],
            'frontend developer': ['javascript, react, typescript, css, html',
                                  'vue.js, javascript, sass, webpack, api'],
            'full stack developer': ['python, django, react, postgresql, docker',
                                   'node.js, express, react, mongodb, aws'],
            'devops engineer': ['kubernetes, docker, jenkins, aws, terraform',
                               'linux, ansible, puppet, monitoring, ci/cd'],
            'data analyst': ['sql, excel, python, pandas, tableau',
                            'r, python, data visualization, statistics, reporting']
        }
        
        skills = []
        for job in job_data:
            template = np.random.choice(skill_templates[job])
            skills.append(template)
        
        # Realistic locations
        locations = ['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai', 'Delhi NCR', 'Kolkata']
        location_weights = [0.30, 0.20, 0.15, 0.12, 0.10, 0.08, 0.05]
        job_locations = np.random.choice(locations, size=size, p=location_weights)
        
        # Realistic experience distribution
        experience_levels = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 
                                          size=size, p=[0.15, 0.20, 0.25, 0.15, 0.10, 0.05, 0.03, 0.03, 0.02, 0.01, 0.01])
        
        # Generate realistic dates
        base_date = datetime.now()
        posted_dates = [base_date - timedelta(days=np.random.randint(0, 90)) for _ in range(size)]
        scraped_dates = [base_date - timedelta(days=np.random.randint(0, 30)) for _ in range(size)]
        
        # Company names
        companies = [f'TechCorp_{i}' for i in range(1, 50)] + \
                   [f'StartUp_{i}' for i in range(1, 100)] + \
                   [f'Enterprise_{i}' for i in range(1, 30)]
        
        self.realistic_data = pd.DataFrame({
            'Job_Type': job_data,
            'Title_Cleaned': [f'Senior {jt}' if np.random.random() > 0.6 else f'Junior {jt}' 
                            for jt in job_data],
            'Min_Experience': experience_levels,
            'Max_Experience': experience_levels + np.random.randint(1, 4, size),
            'Skills': skills,
            'Salary_Lakhs': salaries,
            'Company_Cleaned': np.random.choice(companies, size),
            'Location_Cleaned': job_locations,
            'Description': [f'Job description for {jt} position with required skills and responsibilities' 
                          for jt in job_data],
            'Scraped_At_Cleaned': scraped_dates,
            'Posted_Date': posted_dates
        })
        
        # Ensure salary is positive
        self.realistic_data['Salary_Lakhs'] = np.abs(self.realistic_data['Salary_Lakhs'])
    
    def test_complete_career_analysis_workflow(self):
        """Test complete career analysis workflow from user perspective"""
        # User scenario: Fresh graduate looking to become a Data Scientist
        user_profile = {
            'skills': ['python', 'sql', 'basic_statistics'],
            'experience_years': 0,
            'education_level': 'bachelor',
            'projects': ['academic_project'],
            'preferred_locations': ['Bangalore', 'Hyderabad']
        }
        
        target_role = 'data scientist'
        
        # Step 1: Career Path Analysis
        career_engine = CareerPathEngine()
        learning_path = career_engine.calculate_learning_path(
            user_profile['skills'], target_role, 'basic'
        )
        
        self.assertIsInstance(learning_path, dict)
        self.assertIn('learning_path', learning_path)
        self.assertIn('readiness_score', learning_path)
        
        # Step 2: Role Fit Evaluation
        role_engine = RoleEvaluationEngine()
        role_fit = role_engine.evaluate_role_fit(user_profile, target_role)
        
        self.assertIsInstance(role_fit, dict)
        self.assertIn('overall_score', role_fit)
        self.assertIn('skill_match', role_fit)
        
        # Step 3: AI Risk Assessment
        risk_engine = AIReplacementRiskEngine()
        ai_risk = risk_engine.calculate_automation_risk(target_role, user_profile['skills'])
        
        self.assertIsInstance(ai_risk, dict)
        self.assertIn('risk_score', ai_risk)
        self.assertIn('risk_level', ai_risk)
        
        # Step 4: Interview Difficulty Assessment
        interview_engine = InterviewDifficultyEngine()
        interview_difficulty = interview_engine.calculate_interview_difficulty(
            self.realistic_data, target_role
        )
        
        self.assertIsInstance(interview_difficulty, dict)
        self.assertIn('overall_difficulty', interview_difficulty)
        
        # Step 5: Market Demand Analysis
        demand_engine = MarketDemandEngine(self.realistic_data)
        market_demand = demand_engine.calculate_demand_score([target_role])
        
        self.assertIsInstance(market_demand, dict)
        if target_role in market_demand:
            self.assertIn('overall_score', market_demand[target_role])
        
        # Step 6: Salary Analysis
        salary_engine = SalaryGrowthEngine()
        salary_projection = salary_engine.predict_salary_trajectory(
            self.realistic_data, target_role, 3  # 3 years projection
        )
        
        self.assertIsInstance(salary_projection, dict)
        self.assertIn('predicted_salary', salary_projection)
        
        # Validate workflow consistency
        self.assertGreater(learning_path['readiness_score'], 0)
        self.assertGreater(role_fit['overall_score'], 0)
        self.assertGreaterEqual(ai_risk['risk_score'], 0)
        self.assertGreaterEqual(interview_difficulty['overall_difficulty'], 0)
        self.assertGreater(salary_projection['predicted_salary'], 0)
    
    def test_career_transition_scenario(self):
        """Test career transition scenario (Software Engineer to Data Scientist)"""
        # User scenario: Software Engineer wanting to transition to Data Science
        user_profile = {
            'skills': ['java', 'spring', 'sql', 'git', 'basic_python'],
            'experience_years': 3,
            'education_level': 'bachelor',
            'projects': ['web_application', 'api_development']
        }
        
        from_role = 'software engineer'
        to_role = 'data scientist'
        
        # Step 1: Skill Transferability Analysis
        transfer_engine = SkillTransferabilityEngine()
        transferability = transfer_engine.evaluate_skill_transferability(
            user_profile['skills'], from_role, to_role
        )
        
        self.assertIsInstance(transferability, dict)
        self.assertIn('transferability_score', transferability)
        self.assertIn('transferable_skills', transferability)
        self.assertIn('missing_skills', transferability)
        
        # Step 2: Learning Path for Transition
        career_engine = CareerPathEngine()
        transition_path = career_engine.calculate_learning_path(
            user_profile['skills'], to_role, 'intermediate'
        )
        
        self.assertIsInstance(transition_path, dict)
        self.assertIn('learning_path', transition_path)
        
        # Step 3: Compare Role Requirements
        role_engine = RoleEvaluationEngine()
        current_fit = role_engine.evaluate_role_fit(user_profile, from_role)
        target_fit = role_engine.evaluate_role_fit(user_profile, to_role)
        
        self.assertIsInstance(current_fit, dict)
        self.assertIsInstance(target_fit, dict)
        
        # Validate transition analysis
        self.assertGreaterEqual(transferability['transferability_score'], 0)
        self.assertLessEqual(transferability['transferability_score'], 1)
        
        # Current role should have better fit than target role
        self.assertGreater(current_fit['overall_score'], target_fit['overall_score'])
    
    def test_experienced_professional_scenario(self):
        """Test scenario for experienced professional seeking growth"""
        # User scenario: 5-year experienced professional
        user_profile = {
            'skills': ['python', 'machine_learning', 'sql', 'aws', 'docker', 'kubernetes'],
            'experience_years': 5,
            'education_level': 'master',
            'projects': ['ml_models', 'data_pipelines', 'mlops_system'],
            'current_role': 'data scientist'
        }
        
        target_roles = ['ml engineer', 'senior data scientist', 'ai engineer', 'data science lead']
        
        # Step 1: Role Comparison
        role_engine = RoleEvaluationEngine()
        role_comparison = role_engine.compare_roles(user_profile, target_roles)
        
        self.assertIsInstance(role_comparison, dict)
        self.assertEqual(len(role_comparison), len(target_roles))
        
        # Step 2: Advanced Role Analysis
        career_engine = CareerPathEngine()
        advanced_paths = {}
        
        for role in target_roles:
            path = career_engine.calculate_learning_path(
                user_profile['skills'], role, 'advanced'
            )
            advanced_paths[role] = path
        
        self.assertEqual(len(advanced_paths), len(target_roles))
        
        # Step 3: Market Analysis for Senior Roles
        demand_engine = MarketDemandEngine(self.realistic_data)
        market_analysis = demand_engine.calculate_demand_score(target_roles)
        
        self.assertIsInstance(market_analysis, dict)
        
        # Step 4: Salary Growth Projection
        salary_engine = SalaryGrowthEngine()
        salary_projections = {}
        
        for role in target_roles:
            projection = salary_engine.predict_salary_trajectory(
                self.realistic_data, role, user_profile['experience_years'] + 2
            )
            salary_projections[role] = projection
        
        self.assertEqual(len(salary_projections), len(target_roles))
        
        # Validate experienced professional analysis
        for role in target_roles:
            self.assertIn(role, role_comparison)
            self.assertIn('overall_score', role_comparison[role])
            self.assertIn(role, advanced_paths)
            self.assertIn('predicted_salary', salary_projections[role])
    
    def test_entry_level_fresher_scenario(self):
        """Test scenario for entry-level fresher"""
        # User scenario: Recent graduate with minimal experience
        user_profile = {
            'skills': ['python', 'basic_sql', 'html', 'css'],
            'experience_years': 0,
            'education_level': 'bachelor',
            'projects': ['college_project'],
            'internships': []
        }
        
        entry_level_roles = ['junior software engineer', 'data analyst', 'frontend developer', 'junior qa engineer']
        
        # Step 1: Entry Barrier Analysis
        blocker_detector = HiddenBlockerDetector()
        entry_barriers = {}
        
        for role in entry_level_roles:
            barriers = blocker_detector.detect_hidden_blockers(self.realistic_data, role)
            entry_barriers[role] = barriers
        
        self.assertEqual(len(entry_barriers), len(entry_level_roles))
        
        # Step 2: Prerequisites Analysis
        prereq_engine = PrequisiteEngine()
        prerequisites = {}
        
        for role in entry_level_roles:
            prereq = prereq_engine.analyze_prerequisites(self.realistic_data, role)
            prerequisites[role] = prereq
        
        self.assertEqual(len(prerequisites), len(entry_level_roles))
        
        # Step 3: Interview Preparation Analysis
        interview_engine = InterviewDifficultyEngine()
        interview_analysis = {}
        
        for role in entry_level_roles:
            analysis = interview_engine.estimate_preparation_time(user_profile, role)
            interview_analysis[role] = analysis
        
        self.assertEqual(len(interview_analysis), len(entry_level_roles))
        
        # Step 4: Fresher-Friendly Market Analysis
        fresher_data = self.realistic_data[self.realistic_data['Min_Experience'] <= 1]
        demand_engine = MarketDemandEngine(fresher_data)
        fresher_demand = demand_engine.calculate_demand_score(entry_level_roles)
        
        self.assertIsInstance(fresher_demand, dict)
        
        # Validate fresher analysis
        for role in entry_level_roles:
            self.assertIn(role, entry_barriers)
            self.assertIn(role, prerequisites)
            self.assertIn(role, interview_analysis)
            self.assertIn('total_weeks', interview_analysis[role])
    
    def test_market_intelligence_scenario(self):
        """Test market intelligence gathering scenario"""
        # Scenario: Career counselor needing market insights
        domains = ['data scientist', 'software engineer', 'ml engineer', 'devops engineer']
        locations = ['Bangalore', 'Hyderabad', 'Pune']
        
        # Step 1: Market Demand Analysis
        demand_engine = MarketDemandEngine(self.realistic_data)
        market_demand = demand_engine.calculate_demand_score(domains)
        
        self.assertIsInstance(market_demand, dict)
        
        # Step 2: Salary Analysis by Location
        salary_engine = SalaryGrowthEngine()
        location_salary_analysis = {}
        
        for location in locations:
            location_data = self.realistic_data[self.realistic_data['Location_Cleaned'] == location]
            analysis = salary_engine.analyze_location_adjustments(location_data, 'data scientist', [location])
            location_salary_analysis[location] = analysis
        
        self.assertEqual(len(location_salary_analysis), len(locations))
        
        # Step 3: Competition Analysis
        competition_engine = CompetitionLevelCalculator()
        competition_analysis = {}
        
        for domain in domains:
            competition = competition_engine.calculate_competition_level(self.realistic_data, domain)
            competition_analysis[domain] = competition
        
        self.assertEqual(len(competition_analysis), len(domains))
        
        # Step 4: Market Velocity Analysis
        velocity_engine = JobMarketVelocityCalculator()
        velocity_analysis = {}
        
        for domain in domains:
            velocity = velocity_engine.calculate_market_velocity(self.realistic_data, domain)
            velocity_analysis[domain] = velocity
        
        self.assertEqual(len(velocity_analysis), len(domains))
        
        # Step 5: Saturation Risk Analysis
        saturation_engine = SaturationRiskIndicator()
        saturation_analysis = {}
        
        for domain in domains:
            saturation = saturation_engine.assess_saturation_risk(self.realistic_data, domain)
            saturation_analysis[domain] = saturation
        
        self.assertEqual(len(saturation_analysis), len(domains))
        
        # Validate market intelligence
        for domain in domains:
            if domain in market_demand:
                self.assertIn('overall_score', market_demand[domain])
            self.assertIn(domain, competition_analysis)
            self.assertIn(domain, velocity_analysis)
            self.assertIn(domain, saturation_analysis)
    
    def test_cross_domain_consistency_validation(self):
        """Test consistency across different analytics engines"""
        domain = 'data scientist'
        skills = ['python', 'machine learning', 'sql']
        
        # Get insights from multiple engines
        career_engine = CareerPathEngine()
        role_engine = RoleEvaluationEngine()
        risk_engine = AIReplacementRiskEngine()
        interview_engine = InterviewDifficultyEngine()
        demand_engine = MarketDemandEngine(self.realistic_data)
        salary_engine = SalaryGrowthEngine()
        
        # Collect all insights
        insights = {
            'learning_path': career_engine.calculate_learning_path(skills, domain, 'basic'),
            'role_fit': role_engine.evaluate_role_fit({'skills': skills, 'experience_years': 2}, domain),
            'ai_risk': risk_engine.calculate_automation_risk(domain, skills),
            'interview_difficulty': interview_engine.calculate_interview_difficulty(self.realistic_data, domain),
            'market_demand': demand_engine.calculate_demand_score([domain]),
            'salary_projection': salary_engine.predict_salary_trajectory(self.realistic_data, domain, 3)
        }
        
        # Validate data types and basic structure
        for key, value in insights.items():
            self.assertIsInstance(value, dict)
        
        # Check for logical consistency
        if domain in insights['market_demand']:
            demand_score = insights['market_demand'][domain].get('overall_score', 0)
            self.assertGreaterEqual(demand_score, 0)
            self.assertLessEqual(demand_score, 10)
        
        # Check skill relevance consistency
        skill_relevance_scores = [
            insights['role_fit'].get('skill_match', 0),
            insights['learning_path'].get('readiness_score', 0)
        ]
        
        for score in skill_relevance_scores:
            self.assertGreaterEqual(score, 0)
        
        # Check risk vs difficulty correlation
        ai_risk_score = insights['ai_risk'].get('risk_score', 0)
        interview_difficulty_score = insights['interview_difficulty'].get('overall_difficulty', 0)
        
        self.assertGreaterEqual(ai_risk_score, 0)
        self.assertLessEqual(ai_risk_score, 1)
        self.assertGreaterEqual(interview_difficulty_score, 0)
        self.assertLessEqual(interview_difficulty_score, 10)


class TestAnalyticsDataFlow(unittest.TestCase):
    """Test data flow and transformation across analytics engines"""
    
    def setUp(self):
        """Set up test data for data flow testing"""
        self.test_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 100,
            'Title_Cleaned': ['Senior Data Scientist'] * 50 + ['Junior Data Scientist'] * 50,
            'Min_Experience': [0, 1, 2, 3, 4, 5] * 16 + [0, 1, 2, 3],
            'Max_Experience': [2, 3, 4, 5, 6, 7] * 16 + [2, 3, 4, 5],
            'Skills': ['python, ml, statistics'] * 100,
            'Salary_Lakhs': np.random.normal(15, 5, 100),
            'Company_Cleaned': [f'Company_{i}' for i in range(50)] * 2,
            'Location_Cleaned': ['Bangalore'] * 60 + ['Hyderabad'] * 40,
            'Description': ['Data science role'] * 100,
            'Scraped_At_Cleaned': pd.date_range('2023-01-01', periods=100, freq='D'),
            'Posted_Date': pd.date_range('2023-01-01', periods=100, freq='D')
        })
    
    def test_data_preprocessing_consistency(self):
        """Test data preprocessing consistency across engines"""
        engines = [
            CareerPathEngine(),
            InterviewDifficultyEngine(),
            MarketDemandEngine(self.test_data)
        ]
        
        # Test domain filtering
        domain = 'data scientist'
        filtered_results = {}
        
        for engine in engines:
            if hasattr(engine, '_filter_domain'):
                filtered_data = engine._filter_domain(self.test_data, domain)
                filtered_results[engine.__class__.__name__] = filtered_data
            elif hasattr(engine, '_filter_fresher_data'):
                filtered_data = engine._filter_fresher_data(self.test_data)
                filtered_results[engine.__class__.__name__] = filtered_data
        
        # Validate filtering results
        for engine_name, filtered_data in filtered_results.items():
            self.assertIsInstance(filtered_data, pd.DataFrame)
            if not filtered_data.empty:
                self.assertTrue(all(filtered_data['Job_Type'] == domain))
    
    def test_skill_extraction_consistency(self):
        """Test skill extraction consistency"""
        career_engine = CareerPathEngine()
        
        # Filter data for domain
        domain_df = career_engine._filter_domain(self.test_data, 'data scientist')
        
        # Extract skills
        skills = career_engine._extract_required_skills(domain_df)
        
        self.assertIsInstance(skills, dict)
        self.assertGreater(len(skills), 0)
        
        # Validate skill scores
        for skill, score in skills.items():
            self.assertIsInstance(skill, str)
            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
    
    def test_experience_band_filtering(self):
        """Test experience band filtering across engines"""
        career_engine = CareerPathEngine()
        
        experience_bands = [(0, 2), (2, 5), (5, 10)]
        domain = 'data scientist'
        
        band_results = {}
        for min_exp, max_exp in experience_bands:
            filtered_data = career_engine._filter_domain(self.test_data, domain, (min_exp, max_exp))
            band_results[f"{min_exp}-{max_exp}"] = filtered_data
        
        # Validate experience filtering
        for band_name, filtered_data in band_results.items():
            if not filtered_data.empty:
                min_exp, max_exp = map(int, band_name.split('-'))
                self.assertTrue(all(filtered_data['Min_Experience'] >= min_exp))
                self.assertTrue(all(filtered_data['Min_Experience'] <= max_exp + 1))


class TestAnalyticsErrorHandling(unittest.TestCase):
    """Test error handling and edge cases in integration scenarios"""
    
    def setUp(self):
        """Set up test data for error handling"""
        self.minimal_data = pd.DataFrame({
            'Job_Type': ['data scientist'],
            'Skills': ['python'],
            'Salary_Lakhs': [10],
            'Company_Cleaned': ['Test Company'],
            'Location_Cleaned': ['Bangalore'],
            'Description': ['Test description'],
            'Scraped_At_Cleaned': [pd.Timestamp('2023-01-01')],
            'Posted_Date': [pd.Timestamp('2023-01-01')]
        })
        
        self.empty_data = pd.DataFrame(columns=[
            'Job_Type', 'Skills', 'Salary_Lakhs', 'Company_Cleaned', 
            'Location_Cleaned', 'Description', 'Scraped_At_Cleaned', 'Posted_Date'
        ])
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        career_engine = CareerPathEngine()
        
        # Test with minimal data
        result = career_engine._filter_domain(self.minimal_data, 'data scientist')
        self.assertIsInstance(result, pd.DataFrame)
        
        # Test with empty data
        result = career_engine._filter_domain(self.empty_data, 'data scientist')
        self.assertTrue(result.empty)
        
        # Test learning path with minimal data
        learning_path = career_engine.calculate_learning_path(['python'], 'data scientist', 'basic')
        self.assertIsInstance(learning_path, dict)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs"""
        career_engine = CareerPathEngine()
        risk_engine = AIReplacementRiskEngine()
        
        # Test with empty skills
        learning_path = career_engine.calculate_learning_path([], 'data scientist', 'basic')
        self.assertIsInstance(learning_path, dict)
        
        # Test with invalid role
        learning_path = career_engine.calculate_learning_path(['python'], 'nonexistent_role', 'basic')
        self.assertIsInstance(learning_path, dict)
        
        # Test with invalid domain
        ai_risk = risk_engine.calculate_automation_risk('nonexistent_role', ['python'])
        self.assertIsInstance(ai_risk, dict)
    
    def test_missing_columns_handling(self):
        """Test handling of missing required columns"""
        # Create data with missing columns
        incomplete_data = pd.DataFrame({
            'Job_Type': ['data scientist'],
            'Skills': ['python']
            # Missing other required columns
        })
        
        # Test MarketDemandEngine with incomplete data
        with self.assertRaises(ValueError):
            MarketDemandEngine(incomplete_data)
    
    def test_corrupted_data_handling(self):
        """Test handling of corrupted or malformed data"""
        # Create data with corrupted values
        corrupted_data = self.minimal_data.copy()
        corrupted_data.loc[0, 'Salary_Lakhs'] = np.nan
        corrupted_data.loc[0, 'Skills'] = ''
        
        career_engine = CareerPathEngine()
        
        # Test with corrupted data
        result = career_engine._filter_domain(corrupted_data, 'data scientist')
        self.assertIsInstance(result, pd.DataFrame)
        
        # Test skill extraction with corrupted data
        skills = career_engine._extract_required_skills(corrupted_data)
        self.assertIsInstance(skills, dict)


def create_integration_test_suite():
    """Create and return an integration test suite"""
    suite = unittest.TestSuite()
    
    # Add integration test classes
    test_classes = [
        TestRealWorldScenarios,
        TestAnalyticsDataFlow,
        TestAnalyticsErrorHandling
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_integration_tests():
    """Run integration tests with detailed reporting"""
    print("Running Analytics Module Integration Tests")
    print("="*60)
    
    # Create and run test suite
    suite = create_integration_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Integration test summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Configure logging for integration tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    success = run_integration_tests()
    
    if success:
        print("\n✅ All integration tests passed!")
        exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        exit(1)
