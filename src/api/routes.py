"""
API Routes for Job Trend Predictor
Flask endpoints for RuleBasedRecommender and analytics services

Author: Development Team
Date: 2025-03-18
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
import sys
from typing import Dict, List, Any
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import recommender engine
from src.recommender.rule_based_recommendation_engine import DomainRecommendationEngine

# Import PostgreSQL ingestor
from src.preprocessing.postgres_ingestor import PostgreSQLIngestor, DatabaseIngestionFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables for engines
recommender_engine = None
job_data = None

def initialize_engines():
    """Initialize the recommender engine with job data from PostgreSQL"""
    global recommender_engine, job_data
    
    try:
        # Try PostgreSQL first (for production)
        try:
            postgres_ingestor = DatabaseIngestionFactory.get_ingestor('postgres')
            
            # Test connection
            if postgres_ingestor.test_connection():
                job_data = postgres_ingestor.get_job_data()
                logger.info(f"Loaded job data from PostgreSQL with {len(job_data)} records")
                
                # Initialize recommender engine with PostgreSQL data
                recommender_engine = DomainRecommendationEngine(job_data)
                logger.info("Recommender engine initialized with PostgreSQL data")
                return
            else:
                logger.warning("PostgreSQL connection failed, falling back to CSV")
                
        except Exception as postgres_error:
            logger.warning(f"PostgreSQL initialization failed: {str(postgres_error)}. Falling back to CSV.")
        
        # Fallback to CSV (for local development)
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'processed',
            'cleaned',
            'cleaned_job_data.csv'
        )
        
        if os.path.exists(data_path):
            job_data = pd.read_csv(data_path)
            logger.info(f"Loaded job data from CSV with {len(job_data)} records")
        else:
            # Create sample data if file doesn't exist
            logger.warning(f"Job data file not found at {data_path}. Using sample data.")
            job_data = create_sample_data()
        
        # Initialize recommender engine
        recommender_engine = DomainRecommendationEngine(job_data)
        logger.info("Recommender engine initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing engines: {str(e)}")
        # Create fallback sample data
        job_data = create_sample_data()
        recommender_engine = DomainRecommendationEngine(job_data)

def create_sample_data() -> pd.DataFrame:
    """Create sample job data for testing"""
    sample_data = {
        'Job_Type': ['data scientist', 'software engineer', 'ml engineer', 'data analyst', 'backend developer'] * 20,
        'Skills': ['python, machine learning, statistics', 'java, spring, sql', 'python, tensorflow, deep learning', 
                  'sql, excel, python', 'python, django, postgresql'] * 20,
        'Min_Experience': [0, 1, 2, 0, 1] * 20,
        'Max_Experience': [3, 4, 5, 2, 4] * 20,
        'Location': ['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai'] * 20,
        'Salary_Lakhs': [12, 8, 15, 6, 10] * 20,
        'Company': ['TechCorp', 'StartupInc', 'DataCo', 'AnalyticsLtd', 'DevOps'] * 20,
        'Posted_Date': ['2023-01-01'] * 100,
        'No of applicant applied cleaned': [50, 30, 40, 60, 25] * 20,
        'No of job opening cleaned ': [10, 15, 8, 12, 6] * 20
    }
    return pd.DataFrame(sample_data)

def validate_user_profile(profile: Dict) -> tuple:
    """Validate user profile data"""
    errors = []
    
    # Check required fields
    required_fields = ['skills', 'experience', 'location']
    for field in required_fields:
        if field not in profile:
            errors.append(f"Missing required field: {field}")
    
    # Validate skills
    if 'skills' in profile:
        if not isinstance(profile['skills'], list):
            errors.append("Skills must be a list")
        elif len(profile['skills']) == 0:
            errors.append("Skills list cannot be empty")
    
    # Validate experience
    if 'experience' in profile:
        valid_experiences = ['Fresher', '1-2 years', '3-5 years', '5+ years']
        if profile['experience'] not in valid_experiences:
            errors.append(f"Experience must be one of: {valid_experiences}")
    
    # Validate math comfort
    if 'math_comfort' in profile:
        valid_math = ['Weak', 'Moderate', 'Strong']
        if profile['math_comfort'] not in valid_math:
            errors.append(f"Math comfort must be one of: {valid_math}")
    
    return len(errors) == 0, errors

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Job Trend Predictor API',
        'version': '1.0.0'
    })

@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """Get domain recommendations based on user profile"""
    try:
        # Initialize engines if not done
        if recommender_engine is None:
            initialize_engines()
        
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'No data provided',
                'message': 'Request body is empty'
            }), 400
        
        # Validate user profile
        is_valid, errors = validate_user_profile(data)
        if not is_valid:
            return jsonify({
                'error': 'Invalid user profile',
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Get top_n parameter (default to 3)
        top_n = data.get('top_n', 3)
        if not isinstance(top_n, int) or top_n < 1 or top_n > 10:
            return jsonify({
                'error': 'Invalid top_n parameter',
                'message': 'top_n must be an integer between 1 and 10'
            }), 400
        
        # Get recommendations
        recommendations = recommender_engine.get_recommendations(data, top_n)
        
        # Format response
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'user_profile': data,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to generate recommendations',
            'details': str(e)
        }), 500

@app.route('/api/recommend/domains', methods=['GET'])
def get_all_domains():
    """Get all available domains for recommendations"""
    try:
        if recommender_engine is None:
            initialize_engines()
        
        domains = recommender_engine.domains
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'domains': domains,
            'total_domains': len(domains)
        })
        
    except Exception as e:
        logger.error(f"Error in get_all_domains: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve domains',
            'details': str(e)
        }), 500

@app.route('/api/recommend/analyze', methods=['POST'])
def analyze_domain():
    """Analyze a specific domain for a user profile"""
    try:
        if recommender_engine is None:
            initialize_engines()
        
        data = request.get_json()
        
        if not data or 'domain' not in data:
            return jsonify({
                'error': 'Missing domain',
                'message': 'Domain is required'
            }), 400
        
        domain = data['domain']
        user_profile = data.get('user_profile', {})
        
        # Validate domain
        if domain not in recommender_engine.domains:
            return jsonify({
                'error': 'Invalid domain',
                'message': f'Domain "{domain}" not found',
                'available_domains': recommender_engine.domains
            }), 400
        
        # Validate user profile
        is_valid, errors = validate_user_profile(user_profile)
        if not is_valid:
            return jsonify({
                'error': 'Invalid user profile',
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Get market signals for the domain
        location = user_profile.get('location', 'Bangalore')
        market_signals = recommender_engine._fetch_market_signals(domain, location)
        
        # Calculate score breakdown
        score_breakdown = recommender_engine._calculate_domain_score(domain, user_profile, market_signals)
        
        # Format detailed analysis
        analysis = {
            'domain': domain,
            'user_profile': user_profile,
            'market_signals': market_signals,
            'score_breakdown': score_breakdown,
            'detailed_analysis': recommender_engine._format_output(domain, score_breakdown, user_profile),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_domain: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to analyze domain',
            'details': str(e)
        }), 500

@app.route('/api/recommend/compare', methods=['POST'])
def compare_domains():
    """Compare multiple domains for a user profile"""
    try:
        if recommender_engine is None:
            initialize_engines()
        
        data = request.get_json()
        
        if not data or 'domains' not in data:
            return jsonify({
                'error': 'Missing domains',
                'message': 'Domains list is required'
            }), 400
        
        domains = data['domains']
        user_profile = data.get('user_profile', {})
        
        # Validate domains
        if not isinstance(domains, list) or len(domains) == 0:
            return jsonify({
                'error': 'Invalid domains',
                'message': 'Domains must be a non-empty list'
            }), 400
        
        invalid_domains = [d for d in domains if d not in recommender_engine.domains]
        if invalid_domains:
            return jsonify({
                'error': 'Invalid domains',
                'message': f'Domains not found: {invalid_domains}',
                'available_domains': recommender_engine.domains
            }), 400
        
        # Validate user profile
        is_valid, errors = validate_user_profile(user_profile)
        if not is_valid:
            return jsonify({
                'error': 'Invalid user profile',
                'message': 'Validation failed',
                'errors': errors
            }), 400
        
        # Compare domains
        comparisons = []
        location = user_profile.get('location', 'Bangalore')
        
        for domain in domains:
            market_signals = recommender_engine._fetch_market_signals(domain, location)
            score_breakdown = recommender_engine._calculate_domain_score(domain, user_profile, market_signals)
            
            comparison = {
                'domain': domain,
                'score_breakdown': score_breakdown,
                'detailed_analysis': recommender_engine._format_output(domain, score_breakdown, user_profile),
                'market_signals': market_signals
            }
            comparisons.append(comparison)
        
        # Sort by total score
        comparisons.sort(key=lambda x: x['score_breakdown']['total_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'user_profile': user_profile,
            'comparisons': comparisons,
            'ranking_summary': [
                {
                    'rank': i + 1,
                    'domain': comp['domain'],
                    'total_score': comp['score_breakdown']['total_score'],
                    'match_percentage': comp['detailed_analysis']['match_percentage']
                }
                for i, comp in enumerate(comparisons)
            ]
        })
        
    except Exception as e:
        logger.error(f"Error in compare_domains: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to compare domains',
            'details': str(e)
        }), 500

@app.route('/api/market/signals/<domain>', methods=['GET'])
def get_market_signals(domain):
    """Get market signals for a specific domain"""
    try:
        if recommender_engine is None:
            initialize_engines()
        
        if domain not in recommender_engine.domains:
            return jsonify({
                'error': 'Invalid domain',
                'message': f'Domain "{domain}" not found',
                'available_domains': recommender_engine.domains
            }), 400
        
        location = request.args.get('location', 'Bangalore')
        market_signals = recommender_engine._fetch_market_signals(domain, location)
        
        return jsonify({
            'success': True,
            'domain': domain,
            'location': location,
            'market_signals': market_signals,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_market_signals: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get market signals',
            'details': str(e)
        }), 500

@app.route('/api/data/stats', methods=['GET'])
def get_data_stats():
    """Get statistics about the job data"""
    try:
        # Try PostgreSQL first
        try:
            postgres_ingestor = DatabaseIngestionFactory.get_ingestor('postgres')
            
            # Test connection and get stats
            if postgres_ingestor.test_connection():
                stats = postgres_ingestor.get_data_stats()
                stats['data_source'] = 'postgresql'
                stats['last_updated'] = datetime.now().isoformat()
                
                return jsonify({
                    'success': True,
                    'stats': stats
                })
            else:
                logger.warning("PostgreSQL connection failed for stats, using in-memory data")
                
        except Exception as postgres_error:
            logger.warning(f"PostgreSQL stats failed: {str(postgres_error)}. Using in-memory data.")
        
        # Fallback to in-memory data
        if job_data is None:
            initialize_engines()
        
        stats = {
            'total_records': len(job_data),
            'job_types': job_data['Job_Type'].value_counts().to_dict(),
            'experience_distribution': job_data['Min_Experience'].value_counts().to_dict(),
            'location_distribution': job_data['Location'].value_counts().to_dict(),
            'salary_stats': {
                'mean': float(job_data['Salary_Lakhs'].mean()),
                'median': float(job_data['Salary_Lakhs'].median()),
                'min': float(job_data['Salary_Lakhs'].min()),
                'max': float(job_data['Salary_Lakhs'].max())
            },
            'data_columns': list(job_data.columns),
            'data_source': 'memory',
            'last_updated': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error in get_data_stats: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to get data statistics',
            'details': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist',
        'available_endpoints': [
            '/api/health',
            '/api/recommend',
            '/api/recommend/domains',
            '/api/recommend/analyze',
            '/api/recommend/compare',
            '/api/market/signals/<domain>',
            '/api/data/stats'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500

# Initialize engines on startup
initialize_engines()

if __name__ == '__main__':
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )