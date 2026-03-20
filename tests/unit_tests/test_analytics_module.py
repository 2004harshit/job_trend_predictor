"""
Comprehensive Unit Test Suite for Analytics Module
QA Testing Implementation for all analytics engines and calculators

Author: QA Team
Date: 2025-03-14
Coverage: Career Insights, Domain Analysis, Entry Barriers, Market Analysis
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import analytics engines
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


class TestCareerPathEngine(unittest.TestCase):
    """Test cases for CareerPathEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = CareerPathEngine()
        
        # Create sample data
        self.sample_df = pd.DataFrame({
            'Job_Type': ['data scientist', 'software engineer', 'data scientist'] * 10,
            'Title_Cleaned': ['Senior Data Scientist', 'Python Developer', 'ML Engineer'] * 10,
            'Min_Experience': [2, 1, 3] * 10,
            'Max_Experience': [5, 3, 6] * 10,
            'Skills': ['python, ml, statistics', 'python, django, sql', 'python, tensorflow, deep learning'] * 10,
            'Company_Cleaned': ['Tech Corp', 'Startup Inc', 'Data Co'] * 10,
            'Location_Cleaned': ['Bangalore', 'Hyderabad', 'Pune'] * 10,
            'Salary_Lakhs': [15, 8, 20] * 10
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = CareerPathEngine()
        self.assertIsNotNone(engine.logger)
        self.assertEqual(engine.MIN_SAMPLES, 8)
        self.assertEqual(engine.BASE_HOURS_PER_SKILL, 35)
    
    def test_initialization_with_engines(self):
        """Test initialization with sub-engines"""
        mock_prereq = Mock()
        mock_transfer = Mock()
        engine = CareerPathEngine(
            prerequisite_engine=mock_prereq,
            transferability_engine=mock_transfer
        )
        
        self.assertEqual(engine.prereq_engine, mock_prereq)
        self.assertEqual(engine.transfer_engine, mock_transfer)
    
    def test_domain_weights_structure(self):
        """Test domain weights structure and values"""
        weights = CareerPathEngine.DOMAIN_WEIGHTS
        
        # Check required domains exist
        required_domains = ['data scientist', 'ml engineer', 'software engineer']
        for domain in required_domains:
            self.assertIn(domain, weights)
        
        # Check weight structure (alpha, beta, gamma)
        for domain, weight_config in weights.items():
            self.assertIn('alpha', weight_config)
            self.assertIn('beta', weight_config)
            self.assertIn('gamma', weight_config)
            
            # Check weights sum to 1.0
            total = weight_config['alpha'] + weight_config['beta'] + weight_config['gamma']
            self.assertAlmostEqual(total, 1.0, places=2)
    
    def test_prior_knowledge_factors(self):
        """Test prior knowledge factors"""
        factors = CareerPathEngine.PRIOR_KNOWLEDGE_FACTORS
        
        expected_factors = {
            "none": 1.30,
            "basic": 1.00,
            "intermediate": 0.75,
            "advanced": 0.50
        }
        
        self.assertEqual(factors, expected_factors)
        
        # Check logical ordering
        self.assertGreater(factors["none"], factors["basic"])
        self.assertGreater(factors["basic"], factors["intermediate"])
        self.assertGreater(factors["intermediate"], factors["advanced"])
    
    def test_readiness_thresholds(self):
        """Test readiness thresholds structure"""
        thresholds = CareerPathEngine.READINESS_THRESHOLDS
        
        # Check threshold structure
        for (low, high), (label, color) in thresholds.items():
            self.assertIsInstance(low, int)
            self.assertIsInstance(high, int)
            self.assertIsInstance(label, str)
            self.assertIsInstance(color, str)
            self.assertGreater(high, low)
    
    def test_filter_domain_by_job_type(self):
        """Test domain filtering by Job_Type column"""
        result = self.engine._filter_domain(self.sample_df, 'data scientist')
        
        self.assertFalse(result.empty)
        self.assertEqual(len(result), 20)  # 2 out of 3 rows * 10
        self.assertTrue(all(result['Job_Type'] == 'data scientist'))
    
    def test_filter_domain_by_title_fallback(self):
        """Test domain filtering by Title_Cleaned when Job_Type fails"""
        # Create data without matching Job_Type
        df_no_match = self.sample_df.copy()
        df_no_match['Job_Type'] = 'other_role'
        
        result = self.engine._filter_domain(df_no_match, 'data scientist')
        
        # Should find matches in Title_Cleaned
        self.assertFalse(result.empty)
        self.assertTrue(result['Title_Cleaned'].str.contains('data scientist', case=False).any())
    
    def test_filter_domain_with_experience_band(self):
        """Test domain filtering with experience band"""
        result = self.engine._filter_domain(self.sample_df, 'data scientist', experience_band=(2, 4))
        
        self.assertFalse(result.empty)
        self.assertTrue(all(result['Min_Experience'] >= 2))
        self.assertTrue(all(result['Min_Experience'] <= 5))  # max_e + 1
    
    def test_filter_domain_empty_result(self):
        """Test domain filtering with no matches"""
        result = self.engine._filter_domain(self.sample_df, 'nonexistent_role')
        
        self.assertTrue(result.empty)
    
    def test_extract_required_skills(self):
        """Test skill extraction from domain data"""
        domain_df = self.engine._filter_domain(self.sample_df, 'data scientist')
        skills = self.engine._extract_required_skills(domain_df)
        
        self.assertIsInstance(skills, dict)
        self.assertGreater(len(skills), 0)
        
        # Check skill scores are positive
        for skill, score in skills.items():
            self.assertGreaterEqual(score, 0)
    
    def test_calculate_learning_path(self):
        """Test learning path calculation"""
        user_skills = ['python', 'sql']
        target_role = 'data scientist'
        prior_knowledge = 'basic'
        
        result = self.engine.calculate_learning_path(user_skills, target_role, prior_knowledge)
        
        self.assertIsInstance(result, dict)
        self.assertIn('learning_path', result)
        self.assertIn('total_months', result)
        self.assertIn('readiness_score', result)
        self.assertIn('verdict', result)
        
        # Check learning path structure
        learning_path = result['learning_path']
        self.assertIsInstance(learning_path, list)
        if learning_path:
            self.assertIn('skill', learning_path[0])
            self.assertIn('duration_months', learning_path[0])
            self.assertIn('priority', learning_path[0])
    
    def test_estimate_time_to_role(self):
        """Test time estimation for role"""
        learning_path = [
            {'skill': 'python', 'duration_months': 2, 'priority': 'high'},
            {'skill': 'ml', 'duration_months': 4, 'priority': 'medium'}
        ]
        
        result = self.engine.estimate_time_to_role(learning_path)
        
        self.assertIsInstance(result, (int, float))
        self.assertGreater(result, 0)
        self.assertEqual(result, 6)  # 2 + 4 months
    
    def test_suggest_skill_priorities(self):
        """Test skill priority suggestions"""
        target_role = 'data scientist'
        
        result = self.engine.suggest_skill_priorities(target_role)
        
        self.assertIsInstance(result, list)
        if result:
            self.assertIn('skill', result[0])
            self.assertIn('priority', result[0])
            self.assertIn('importance_score', result[0])


class TestRoleEvaluationEngine(unittest.TestCase):
    """Test cases for RoleEvaluationEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = RoleEvaluationEngine()
        
        self.user_profile = {
            'skills': ['python', 'sql', 'basic_ml'],
            'experience_years': 2,
            'education_level': 'bachelor',
            'projects': ['data_analysis_project']
        }
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = RoleEvaluationEngine()
        self.assertIsNotNone(engine.logger)
    
    def test_evaluate_role_fit(self):
        """Test role fit evaluation"""
        role = 'data scientist'
        
        result = self.engine.evaluate_role_fit(self.user_profile, role)
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_score', result)
        self.assertIn('skill_match', result)
        self.assertIn('experience_match', result)
        self.assertIn('education_match', result)
        self.assertIn('recommendations', result)
        
        # Check score ranges
        self.assertGreaterEqual(result['overall_score'], 0)
        self.assertLessEqual(result['overall_score'], 100)
    
    def test_compare_roles(self):
        """Test role comparison"""
        roles = ['data scientist', 'software engineer', 'ml engineer']
        
        result = self.engine.compare_roles(self.user_profile, roles)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), len(roles))
        
        for role in roles:
            self.assertIn(role, result)
            self.assertIn('overall_score', result[role])
        
        # Check that scores are comparable
        scores = [result[role]['overall_score'] for role in roles]
        self.assertEqual(len(scores), len(roles))
    
    def test_evaluate_role_fit_invalid_profile(self):
        """Test role evaluation with invalid profile"""
        invalid_profile = {'skills': []}  # Missing required fields
        
        result = self.engine.evaluate_role_fit(invalid_profile, 'data scientist')
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('overall_score', result)


class TestAIReplacementRiskEngine(unittest.TestCase):
    """Test cases for AIReplacementRiskEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = AIReplacementRiskEngine()
        
        self.sample_job_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 5,
            'Description': [
                'Strategic analysis and machine learning model development',
                'Data entry and report generation using templates',
                'Creative problem solving and client consultation',
                'Routine data cleaning and scheduled reporting',
                'Research and innovation in AI algorithms'
            ],
            'Skills': [
                'machine learning, python, statistics',
                'excel, data entry, reporting',
                'communication, presentation, problem solving',
                'data cleaning, sql, reporting',
                'deep learning, research, innovation'
            ]
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = AIReplacementRiskEngine()
        self.assertIsNotNone(engine.logger)
        self.assertEqual(engine.MIN_SAMPLES, 5)
    
    def test_initialization_with_custom_weights(self):
        """Test initialization with custom weights"""
        custom_weights = {
            "routine_exposure": 0.25,
            "codified_knowledge": 0.25,
            "creativity_gap": 0.25,
            "skill_automation": 0.15,
            "human_factor": 0.10
        }
        
        engine = AIReplacementRiskEngine(weights=custom_weights)
        self.assertEqual(engine.weights, custom_weights)
    
    def test_keyword_banks_completeness(self):
        """Test completeness of keyword banks"""
        keyword_banks = {
            'ROUTINE_KEYWORDS': self.engine.ROUTINE_KEYWORDS,
            'CODIFIED_KEYWORDS': self.engine.CODIFIED_KEYWORDS,
            'CREATIVE_KEYWORDS': self.engine.CREATIVE_KEYWORDS,
            'HUMAN_FACTOR_KEYWORDS': self.engine.HUMAN_FACTOR_KEYWORDS
        }
        
        for bank_name, keywords in keyword_banks.items():
            self.assertIsInstance(keywords, list)
            self.assertGreater(len(keywords), 10, f"{bank_name} should have more than 10 keywords")
            
            # Check all keywords are strings
            for keyword in keywords:
                self.assertIsInstance(keyword, str)
                self.assertGreater(len(keyword), 0)
    
    def test_skill_ai_risk_scores(self):
        """Test skill AI risk scores"""
        skill_risks = self.engine.SKILL_AI_RISK
        
        # Check structure
        for skill, risk_score in skill_risks.items():
            self.assertIsInstance(skill, str)
            self.assertIsInstance(risk_score, (int, float))
            self.assertGreaterEqual(risk_score, 0)
            self.assertLessEqual(risk_score, 1)
        
        # Check specific skills
        self.assertIn('data entry', skill_risks)
        self.assertIn('machine learning', skill_risks)
        self.assertIn('python', skill_risks)
        
        # Check logical risk ordering
        self.assertGreater(skill_risks['data entry'], skill_risks['python'])
        self.assertGreater(skill_risks['python'], skill_risks['machine learning'])
    
    def test_calculate_automation_risk(self):
        """Test automation risk calculation"""
        role = 'data scientist'
        skills = ['python', 'machine learning', 'statistics']
        
        result = self.engine.calculate_automation_risk(role, skills)
        
        self.assertIsInstance(result, dict)
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('factors', result)
        self.assertIn('recommendations', result)
        
        # Check risk score range
        self.assertGreaterEqual(result['risk_score'], 0)
        self.assertLessEqual(result['risk_score'], 1)
        
        # Check risk level is valid
        valid_levels = ['Low', 'Medium', 'High']
        self.assertIn(result['risk_level'], valid_levels)
    
    def test_identify_future_proof_skills(self):
        """Test future-proof skill identification"""
        domain = 'data science'
        
        result = self.engine.identify_future_proof_skills(domain)
        
        self.assertIsInstance(result, list)
        
        if result:
            for skill_info in result:
                self.assertIsInstance(skill_info, dict)
                self.assertIn('skill', skill_info)
                self.assertIn('risk_score', skill_info)
                self.assertIn('reasoning', skill_info)
    
    def test_analyze_task_composition(self):
        """Test task composition analysis"""
        description = "Strategic analysis and creative problem solving with client consultation"
        
        result = self.engine.analyze_task_composition(description)
        
        self.assertIsInstance(result, dict)
        self.assertIn('routine_score', result)
        self.assertIn('codified_score', result)
        self.assertIn('creative_score', result)
        self.assertIn('human_factor_score', result)
        
        # Check scores sum to reasonable value
        total_score = sum([
            result['routine_score'],
            result['codified_score'],
            result['creative_score'],
            result['human_factor_score']
        ])
        self.assertGreater(total_score, 0)


class TestDomainStabilityEngine(unittest.TestCase):
    """Test cases for DomainStabilityEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = DomainStabilityEngine()
        
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 20,
            'Posted_Date': pd.date_range('2023-01-01', periods=20, freq='D'),
            'Company_Cleaned': ['Company_' + str(i) for i in range(10)] * 2,
            'Location_Cleaned': ['Bangalore', 'Hyderabad', 'Pune', 'Chennai'] * 5,
            'Salary_Lakhs': np.random.normal(15, 5, 20)
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = DomainStabilityEngine()
        self.assertIsNotNone(engine.logger)
    
    def test_calculate_market_volatility(self):
        """Test market volatility calculation"""
        domain = 'data scientist'
        
        result = self.engine.calculate_market_volatility(self.sample_data, domain)
        
        self.assertIsInstance(result, dict)
        self.assertIn('volatility_score', result)
        self.assertIn('volatility_level', result)
        self.assertIn('growth_trend', result)
        self.assertIn('market_maturity', result)
        
        # Check volatility score range
        self.assertGreaterEqual(result['volatility_score'], 0)
        self.assertLessEqual(result['volatility_score'], 1)
    
    def test_predict_domain_growth(self):
        """Test domain growth prediction"""
        domain = 'data scientist'
        
        result = self.engine.predict_domain_growth(self.sample_data, domain)
        
        self.assertIsInstance(result, dict)
        self.assertIn('growth_prediction', result)
        self.assertIn('confidence_interval', result)
        self.assertIn('time_horizon_months', result)
        self.assertIn('market_factors', result)
    
    def test_analyze_market_maturity(self):
        """Test market maturity analysis"""
        domain = 'data scientist'
        
        result = self.engine.analyze_market_maturity(self.sample_data, domain)
        
        self.assertIsInstance(result, dict)
        self.assertIn('maturity_level', result)
        self.assertIn('market_saturation', result)
        self.assertIn('competition_intensity', result)
    
    def test_insufficient_data_handling(self):
        """Test handling of insufficient data"""
        small_data = self.sample_data.head(3)  # Less than minimum required
        
        result = self.engine.calculate_market_volatility(small_data, 'data scientist')
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('error', result) or result.get('volatility_score') is None


class TestSalaryGrowthEngine(unittest.TestCase):
    """Test cases for SalaryGrowthEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = SalaryGrowthEngine()
        
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 15,
            'Min_Experience': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            'Max_Experience': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16],
            'Salary_Lakhs': [6, 8, 10, 12, 15, 18, 22, 26, 30, 35, 40, 45, 50, 55, 60],
            'Location_Cleaned': ['Bangalore'] * 15
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = SalaryGrowthEngine()
        self.assertIsNotNone(engine.logger)
    
    def test_predict_salary_trajectory(self):
        """Test salary trajectory prediction"""
        role = 'data scientist'
        experience_years = 5
        
        result = self.engine.predict_salary_trajectory(self.sample_data, role, experience_years)
        
        self.assertIsInstance(result, dict)
        self.assertIn('predicted_salary', result)
        self.assertIn('salary_range', result)
        self.assertIn('growth_rate', result)
        self.assertIn('career_stage', result)
        self.assertIn('percentile_ranking', result)
        
        # Check predicted salary is reasonable
        self.assertGreater(result['predicted_salary'], 0)
        self.assertIsInstance(result['predicted_salary'], (int, float))
    
    def test_identify_premium_skills(self):
        """Test premium skill identification"""
        domain = 'data science'
        
        result = self.engine.identify_premium_skills(self.sample_data, domain)
        
        self.assertIsInstance(result, list)
        
        if result:
            for skill_info in result:
                self.assertIsInstance(skill_info, dict)
                self.assertIn('skill', skill_info)
                self.assertIn('salary_premium', skill_info)
                self.assertIn('demand_factor', skill_info)
    
    def test_calculate_experience_ladder(self):
        """Test experience ladder calculation"""
        domain = 'data scientist'
        
        result = self.engine.calculate_experience_ladder(self.sample_data, domain)
        
        self.assertIsInstance(result, dict)
        
        # Check for different experience levels
        expected_levels = ['fresher', 'junior', 'mid', 'senior', 'lead']
        for level in expected_levels:
            if level in result:
                self.assertIsInstance(result[level], dict)
                self.assertIn('median_salary', result[level])
                self.assertIn('salary_range', result[level])
    
    def test_analyze_location_adjustments(self):
        """Test location-based salary adjustments"""
        domain = 'data scientist'
        locations = ['Bangalore', 'Hyderabad', 'Pune']
        
        result = self.engine.analyze_location_adjustments(self.sample_data, domain, locations)
        
        self.assertIsInstance(result, dict)
        
        for location in locations:
            if location in result:
                self.assertIn('adjustment_factor', result[location])
                self.assertIn('adjusted_median', result[location])


class TestSkillTransferabilityEngine(unittest.TestCase):
    """Test cases for SkillTransferabilityEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = SkillTransferabilityEngine()
        
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist', 'software engineer', 'ml engineer'] * 10,
            'Skills': [
                'python, machine learning, statistics',
                'python, django, javascript',
                'python, tensorflow, deep learning'
            ] * 10
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = SkillTransferabilityEngine()
        self.assertIsNotNone(engine.logger)
    
    def test_evaluate_skill_transferability(self):
        """Test skill transferability evaluation"""
        skills = ['python', 'sql']
        from_domain = 'data scientist'
        to_domain = 'software engineer'
        
        result = self.engine.evaluate_skill_transferability(skills, from_domain, to_domain)
        
        self.assertIsInstance(result, dict)
        self.assertIn('transferability_score', result)
        self.assertIn('transferable_skills', result)
        self.assertIn('missing_skills', result)
        self.assertIn('transition_difficulty', result)
        self.assertIn('learning_recommendations', result)
        
        # Check score range
        self.assertGreaterEqual(result['transferability_score'], 0)
        self.assertLessEqual(result['transferability_score'], 1)
    
    def test_find_similar_domains(self):
        """Test finding similar domains"""
        current_domain = 'data scientist'
        
        result = self.engine.find_similar_domains(current_domain)
        
        self.assertIsInstance(result, list)
        
        if result:
            for domain_info in result:
                self.assertIsInstance(domain_info, dict)
                self.assertIn('domain', domain_info)
                self.assertIn('similarity_score', domain_info)
                self.assertIn('shared_skills', domain_info)
    
    def test_map_skill_evolution(self):
        """Test skill evolution mapping"""
        skill_path = ['python', 'machine learning', 'deep learning']
        
        result = self.engine.map_skill_evolution(skill_path)
        
        self.assertIsInstance(result, dict)
        self.assertIn('evolution_path', result)
        self.assertIn('skill_progression', result)
        self.assertIn('career_impact', result)
    
    def test_analyze_cross_domain_opportunities(self):
        """Test cross-domain opportunity analysis"""
        skills = ['python', 'data analysis', 'communication']
        
        result = self.engine.analyze_cross_domain_opportunities(skills)
        
        self.assertIsInstance(result, list)
        
        if result:
            for opportunity in result:
                self.assertIsInstance(opportunity, dict)
                self.assertIn('domain', opportunity)
                self.assertIn('fit_score', opportunity)
                self.assertIn('skill_utilization', opportunity)


class TestInterviewDifficultyEngine(unittest.TestCase):
    """Test cases for InterviewDifficultyEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = InterviewDifficultyEngine()
        
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 10,
            'Description': [
                'Looking for candidates with strong DSA and system design skills',
                'Basic coding skills required, no complex algorithms',
                'Advanced machine learning and deep learning expertise needed',
                'Frontend development with React and modern frameworks',
                'Full stack development with microservices architecture',
                'Entry level position, basic programming skills sufficient',
                'Senior role requiring system design and distributed systems',
                'Data analysis role with focus on SQL and Python',
                'DevOps position with Kubernetes and cloud experience',
                'Mobile development with React Native'
            ],
            'Skills': [
                'dsa, algorithms, system design',
                'basic coding, python',
                'machine learning, deep learning, tensorflow',
                'react, javascript, frontend',
                'full stack, microservices, docker',
                'python, basic programming',
                'system design, distributed systems, architecture',
                'sql, python, data analysis',
                'kubernetes, aws, devops',
                'react native, mobile development'
            ]
        })
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = InterviewDifficultyEngine()
        self.assertIsNotNone(engine.logger)
        self.assertEqual(engine.MIN_SAMPLES, 8)
    
    def test_domain_weights_structure(self):
        """Test domain weights structure"""
        weights = self.engine.DOMAIN_WEIGHTS
        
        # Check required domains
        required_domains = ['software engineer', 'data scientist', 'frontend developer']
        for domain in required_domains:
            self.assertIn(domain, weights)
        
        # Check weight structure (a, b, g)
        for domain, weight_config in weights.items():
            self.assertIn('a', weight_config)  # DSA
            self.assertIn('b', weight_config)  # Domain Knowledge
            self.assertIn('g', weight_config)  # System Design
            
            # Check weights sum to 1.0
            total = weight_config['a'] + weight_config['b'] + weight_config['g']
            self.assertAlmostEqual(total, 1.0, places=2)
    
    def test_dsa_keywords_structure(self):
        """Test DSA keywords structure"""
        dsa_keywords = self.engine.DSA_KEYWORDS
        
        required_levels = ['easy', 'medium', 'hard', 'direct_hard', 'direct_easy']
        for level in required_levels:
            self.assertIn(level, dsa_keywords)
            self.assertIsInstance(dsa_keywords[level], list)
            self.assertGreater(len(dsa_keywords[level]), 0)
    
    def test_system_design_keywords_structure(self):
        """Test system design keywords structure"""
        sd_keywords = self.engine.SYSTEM_DESIGN_KEYWORDS
        
        required_levels = ['basic', 'intermediate', 'advanced']
        for level in required_levels:
            self.assertIn(level, sd_keywords)
            self.assertIsInstance(sd_keywords[level], list)
            self.assertGreater(len(sd_keywords[level]), 0)
    
    def test_calculate_interview_difficulty(self):
        """Test interview difficulty calculation"""
        role = 'data scientist'
        
        result = self.engine.calculate_interview_difficulty(self.sample_data, role)
        
        self.assertIsInstance(result, dict)
        self.assertIn('overall_difficulty', result)
        self.assertIn('difficulty_level', result)
        self.assertIn('dsa_difficulty', result)
        self.assertIn('domain_difficulty', result)
        self.assertIn('system_design_difficulty', result)
        self.assertIn('technical_rounds', result)
        self.assertIn('success_rate', result)
        
        # Check difficulty score range
        self.assertGreaterEqual(result['overall_difficulty'], 0)
        self.assertLessEqual(result['overall_difficulty'], 10)
    
    def test_estimate_preparation_time(self):
        """Test preparation time estimation"""
        role = 'data scientist'
        candidate_profile = {
            'skills': ['python', 'basic_ml'],
            'experience_years': 2,
            'dsa_level': 'beginner'
        }
        
        result = self.engine.estimate_preparation_time(role, candidate_profile)
        
        self.assertIsInstance(result, dict)
        self.assertIn('total_weeks', result)
        self.assertIn('preparation_plan', result)
        self.assertIn('focus_areas', result)
        self.assertIn('difficulty_gap', result)
        
        # Check preparation time is reasonable
        self.assertGreater(result['total_weeks'], 0)
        self.assertIsInstance(result['total_weeks'], (int, float))
    
    def test_get_interview_format(self):
        """Test interview format prediction"""
        role = 'data scientist'
        
        result = self.engine.get_interview_format(self.sample_data, role)
        
        self.assertIsInstance(result, dict)
        self.assertIn('round_structure', result)
        self.assertIn('round_details', result)
        self.assertIn('total_rounds', result)
        self.assertIn('average_duration', result)
    
    def test_analyze_skill_requirements(self):
        """Test skill requirements analysis"""
        role = 'data scientist'
        
        result = self.engine.analyze_skill_requirements(self.sample_data, role)
        
        self.assertIsInstance(result, dict)
        self.assertIn('core_skills', result)
        self.assertIn('preferred_skills', result)
        self.assertIn('skill_weights', result)
        self.assertIn('skill_trends', result)


class TestMarketDemandEngine(unittest.TestCase):
    """Test cases for MarketDemandEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create sample data with required columns
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist', 'software engineer', 'data scientist'] * 20,
            'Scraped_At_Cleaned': pd.date_range('2023-01-01', periods=60, freq='D'),
            'Posted_Date': pd.date_range('2023-01-01', periods=60, freq='D'),
            'Min_Experience': [0, 1, 2] * 20,
            'Max_Experience': [2, 3, 4] * 20,
            'Company_Cleaned': ['Company_' + str(i) for i in range(30)] * 2,
            'Skills': ['python, ml', 'java, spring'] * 20,
            'Location_Cleaned': ['Bangalore', 'Hyderabad', 'Pune'] * 20
        })
        
        self.engine = MarketDemandEngine(self.sample_data)
    
    def test_initialization_success(self):
        """Test successful engine initialization"""
        engine = MarketDemandEngine(self.sample_data)
        self.assertIsNotNone(engine.demand_report)
        self.assertIsInstance(engine.weights, dict)
    
    def test_initialization_invalid_data(self):
        """Test initialization with invalid data"""
        invalid_data = pd.DataFrame({'column1': [1, 2, 3]})
        
        with self.assertRaises(ValueError):
            MarketDemandEngine(invalid_data)
    
    def test_initialization_invalid_weights(self):
        """Test initialization with invalid weights"""
        invalid_weights = {"weight1": 0.5, "weight2": 0.8}  # Sum > 1.0
        
        with self.assertRaises(ValueError):
            MarketDemandEngine(self.sample_data, invalid_weights)
    
    def test_calculate_demand_score(self):
        """Test demand score calculation"""
        domains = ['data scientist', 'software engineer']
        
        result = self.engine.calculate_demand_score(domains)
        
        self.assertIsInstance(result, dict)
        
        for domain in domains:
            if domain in result:
                self.assertIsInstance(result[domain], dict)
                self.assertIn('overall_score', result[domain])
                self.assertIn('breakdown', result[domain])
                self.assertIn('trend', result[domain])
                
                # Check score range
                score = result[domain]['overall_score']
                self.assertGreaterEqual(score, 0)
                self.assertLessEqual(score, 10)
    
    def test_filter_fresher_data(self):
        """Test fresher data filtering"""
        result = self.engine._filter_fresher_data(self.sample_data)
        
        self.assertIsInstance(result, pd.DataFrame)
        
        # Check experience filtering
        if not result.empty:
            self.assertTrue(all(result['Min_Experience'] >= 0))
            self.assertTrue(all(result['Max_Experience'] <= 5))
    
    def test_get_valid_domains(self):
        """Test valid domain filtering"""
        fresher_df = self.engine._filter_fresher_data(self.sample_data)
        domains = ['data scientist', 'software engineer', 'nonexistent_domain']
        
        valid_domains, counts = self.engine._get_valid_domains(fresher_df, domains)
        
        self.assertIsInstance(valid_domains, list)
        self.assertIsInstance(counts, pd.Series)
        
        # Check that valid domains have sufficient data
        for domain in valid_domains:
            self.assertGreaterEqual(counts.get(domain, 0), self.engine.MIN_SAMPLE_THRESHOLD)
    
    def test_calculate_frequency_score(self):
        """Test frequency score calculation"""
        fresher_df = self.engine._filter_fresher_data(self.sample_data)
        domain = 'data scientist'
        max_freq = 100
        
        result = self.engine._calculate_frequency_score(fresher_df, domain, max_freq)
        
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 10)
    
    def test_calculate_trend_score(self):
        """Test trend score calculation"""
        fresher_df = self.engine._filter_fresher_data(self.sample_data)
        domain = 'data scientist'
        
        # Define time periods
        first_this = pd.Timestamp('2023-02-01')
        first_prev = pd.Timestamp('2023-01-01')
        last_prev = pd.Timestamp('2023-01-31')
        
        result = self.engine._calculate_trend_score(fresher_df, domain, first_this, first_prev, last_prev)
        
        self.assertIsInstance(result, (int, float))
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 10)


class TestOtherAnalyticsEngines(unittest.TestCase):
    """Test cases for other analytics engines"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist'] * 10,
            'Salary_Lakhs': [10, 12, 15, 18, 20, 22, 25, 28, 30, 35],
            'Skills': ['python, ml'] * 10,
            'Company_Cleaned': ['Company_' + str(i) for i in range(10)],
            'Location_Cleaned': ['Bangalore'] * 10,
            'Description': ['Data science role'] * 10
        })
    
    def test_hidden_blocker_detector(self):
        """Test HiddenBlockerDetector"""
        detector = HiddenBlockerDetector()
        
        result = detector.detect_hidden_blockers(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('blockers', result)
        self.assertIn('severity_levels', result)
    
    def test_prequisite_engine(self):
        """Test PrequisiteEngine"""
        engine = PrequisiteEngine()
        
        result = engine.analyze_prerequisites(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('required_skills', result)
        self.assertIn('education_requirements', result)
    
    def test_project_complexity_evaluator(self):
        """Test ProjectComplexityEvaluator"""
        evaluator = ProjectComplexityEvaluator()
        
        result = evaluator.evaluate_project_complexity(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('complexity_score', result)
        self.assertIn('complexity_level', result)
    
    def test_average_salary_calculator(self):
        """Test AverageSalaryCalculator"""
        calculator = AverageSalaryCalculator()
        
        result = calculator.calculate_average_salary(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('average_salary', result)
        self.assertIn('salary_range', result)
    
    def test_competition_level_calculator(self):
        """Test CompetitionLevelCalculator"""
        calculator = CompetitionLevelCalculator()
        
        result = calculator.calculate_competition_level(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('competition_score', result)
        self.assertIn('competition_level', result)
    
    def test_job_market_velocity_calculator(self):
        """Test JobMarketVelocityCalculator"""
        calculator = JobMarketVelocityCalculator()
        
        result = calculator.calculate_market_velocity(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('velocity_score', result)
        self.assertIn('growth_rate', result)
    
    def test_saturation_risk_indicator(self):
        """Test SaturationRiskIndicator"""
        indicator = SaturationRiskIndicator()
        
        result = indicator.assess_saturation_risk(self.sample_data, 'data scientist')
        
        self.assertIsInstance(result, dict)
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)


class TestAnalyticsIntegration(unittest.TestCase):
    """Integration tests for analytics module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.sample_data = pd.DataFrame({
            'Job_Type': ['data scientist', 'software engineer', 'ml engineer'] * 20,
            'Title_Cleaned': ['Senior Data Scientist', 'Python Developer', 'ML Engineer'] * 20,
            'Min_Experience': [0, 1, 2, 3, 4, 5] * 10,
            'Max_Experience': [2, 3, 4, 5, 6, 7] * 10,
            'Skills': [
                'python, machine learning, statistics',
                'python, django, javascript',
                'python, tensorflow, deep learning'
            ] * 20,
            'Salary_Lakhs': [15, 8, 20, 25, 30, 35] * 10,
            'Company_Cleaned': ['Company_' + str(i) for i in range(30)] * 2,
            'Location_Cleaned': ['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai'] * 12,
            'Description': [
                'Data science role with ML requirements',
                'Software development position',
                'Machine learning engineer role'
            ] * 20,
            'Scraped_At_Cleaned': pd.date_range('2023-01-01', periods=60, freq='D'),
            'Posted_Date': pd.date_range('2023-01-01', periods=60, freq='D')
        })
    
    def test_career_insights_integration(self):
        """Test career insights engines integration"""
        career_engine = CareerPathEngine()
        role_engine = RoleEvaluationEngine()
        
        # Test career path analysis
        user_skills = ['python', 'sql']
        target_role = 'data scientist'
        
        career_result = career_engine.calculate_learning_path(user_skills, target_role, 'basic')
        self.assertIsInstance(career_result, dict)
        
        # Test role evaluation
        user_profile = {
            'skills': user_skills,
            'experience_years': 2,
            'education_level': 'bachelor'
        }
        
        role_result = role_engine.evaluate_role_fit(user_profile, target_role)
        self.assertIsInstance(role_result, dict)
        
        # Check consistency between results
        self.assertIn('learning_path', career_result)
        self.assertIn('overall_score', role_result)
    
    def test_domain_analysis_integration(self):
        """Test domain analysis engines integration"""
        risk_engine = AIReplacementRiskEngine()
        stability_engine = DomainStabilityEngine()
        salary_engine = SalaryGrowthEngine()
        
        domain = 'data scientist'
        
        # Test AI risk analysis
        risk_result = risk_engine.calculate_automation_risk(domain, ['python', 'ml'])
        self.assertIsInstance(risk_result, dict)
        
        # Test stability analysis
        stability_result = stability_engine.calculate_market_volatility(self.sample_data, domain)
        self.assertIsInstance(stability_result, dict)
        
        # Test salary analysis
        salary_result = salary_engine.predict_salary_trajectory(self.sample_data, domain, 3)
        self.assertIsInstance(salary_result, dict)
        
        # Check cross-engine consistency
        self.assertIn('risk_score', risk_result)
        self.assertIn('volatility_score', stability_result)
        self.assertIn('predicted_salary', salary_result)
    
    def test_entry_barriers_integration(self):
        """Test entry barriers engines integration"""
        interview_engine = InterviewDifficultyEngine()
        blocker_detector = HiddenBlockerDetector()
        prereq_engine = PrequisiteEngine()
        
        role = 'data scientist'
        
        # Test interview difficulty
        interview_result = interview_engine.calculate_interview_difficulty(self.sample_data, role)
        self.assertIsInstance(interview_result, dict)
        
        # Test hidden blockers
        blocker_result = blocker_detector.detect_hidden_blockers(self.sample_data, role)
        self.assertIsInstance(blocker_result, dict)
        
        # Test prerequisites
        prereq_result = prereq_engine.analyze_prerequisites(self.sample_data, role)
        self.assertIsInstance(prereq_result, dict)
        
        # Check result completeness
        self.assertIn('overall_difficulty', interview_result)
        self.assertIn('blockers', blocker_result)
        self.assertIn('required_skills', prereq_result)
    
    def test_market_analysis_integration(self):
        """Test market analysis engines integration"""
        demand_engine = MarketDemandEngine(self.sample_data)
        salary_calc = AverageSalaryCalculator()
        competition_calc = CompetitionLevelCalculator()
        
        domains = ['data scientist', 'software engineer']
        
        # Test demand analysis
        demand_result = demand_engine.calculate_demand_score(domains)
        self.assertIsInstance(demand_result, dict)
        
        # Test salary calculation
        salary_result = salary_calc.calculate_average_salary(self.sample_data, 'data scientist')
        self.assertIsInstance(salary_result, dict)
        
        # Test competition calculation
        competition_result = competition_calc.calculate_competition_level(self.sample_data, 'data scientist')
        self.assertIsInstance(competition_result, dict)
        
        # Check data consistency across engines
        if 'data scientist' in demand_result:
            self.assertIn('overall_score', demand_result['data scientist'])
        self.assertIn('average_salary', salary_result)
        self.assertIn('competition_score', competition_result)


# Test Suite Configuration and Runner
def create_analytics_test_suite():
    """Create and return a test suite with all analytics test cases"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCareerPathEngine,
        TestRoleEvaluationEngine,
        TestAIReplacementRiskEngine,
        TestDomainStabilityEngine,
        TestSalaryGrowthEngine,
        TestSkillTransferabilityEngine,
        TestInterviewDifficultyEngine,
        TestMarketDemandEngine,
        TestOtherAnalyticsEngines,
        TestAnalyticsIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_analytics_tests_with_coverage():
    """Run analytics tests with coverage reporting"""
    import coverage
    
    # Initialize coverage
    cov = coverage.Coverage()
    cov.start()
    
    # Create and run test suite
    suite = create_analytics_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Stop coverage and generate report
    cov.stop()
    cov.save()
    
    print("\n" + "="*60)
    print("ANALYTICS MODULE COVERAGE REPORT")
    print("="*60)
    cov.report()
    
    # Generate HTML coverage report
    cov.html_report(directory='tests/analytics_coverage_html')
    print(f"\nHTML coverage report generated in: tests/analytics_coverage_html/")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.WARNING)
    
    print("Running Analytics Module Unit Tests")
    print("="*60)
    
    # Run tests
    success = run_analytics_tests_with_coverage()
    
    if success:
        print("\n✅ All analytics tests passed!")
        exit(0)
    else:
        print("\n❌ Some analytics tests failed!")
        exit(1)
