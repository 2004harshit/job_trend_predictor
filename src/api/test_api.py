"""
Test script for Job Trend Predictor API
Simple test cases to verify API functionality

Author: Development Team
Date: 2025-03-18
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Check Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            return True
        else:
            print(f"❌ Health check failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {str(e)}")
        return False

def test_get_domains():
    """Test get all domains endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/recommend/domains")
        print(f"Get Domains Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get domains passed: {data['total_domains']} domains found")
            print(f"   Domains: {data['domains'][:5]}...")  # Show first 5
            return True
        else:
            print(f"❌ Get domains failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Get domains error: {str(e)}")
        return False

def test_recommendations():
    """Test recommendations endpoint"""
    try:
        user_profile = {
            "skills": ["Python", "SQL", "Machine Learning"],
            "experience": "Fresher",
            "location": "Bangalore",
            "math_comfort": "Moderate",
            "top_n": 3
        }
        
        response = requests.post(
            f"{BASE_URL}/api/recommend",
            json=user_profile,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Recommendations Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Recommendations passed: {data['total_recommendations']} recommendations")
            
            for i, rec in enumerate(data['recommendations']):
                print(f"   {i+1}. {rec['domain']} - {rec['match_percentage']}% match")
                print(f"      Reason: {rec['reasoning'][:100]}...")
            
            return True
        else:
            print(f"❌ Recommendations failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Recommendations error: {str(e)}")
        return False

def test_analyze_domain():
    """Test analyze domain endpoint"""
    try:
        payload = {
            "domain": "data scientist",
            "user_profile": {
                "skills": ["Python", "SQL"],
                "experience": "Fresher",
                "location": "Bangalore"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/recommend/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Analyze Domain Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data['analysis']
            print(f"✅ Analyze domain passed: {analysis['domain']}")
            print(f"   Total Score: {analysis['score_breakdown']['total_score']}")
            print(f"   Match Percentage: {analysis['detailed_analysis']['match_percentage']}%")
            return True
        else:
            print(f"❌ Analyze domain failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Analyze domain error: {str(e)}")
        return False

def test_compare_domains():
    """Test compare domains endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer", "ml engineer"],
            "user_profile": {
                "skills": ["Python", "SQL"],
                "experience": "Fresher",
                "location": "Bangalore"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/recommend/compare",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Compare Domains Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Compare domains passed: {len(data['comparisons'])} domains compared")
            
            for rank in data['ranking_summary']:
                print(f"   {rank['rank']}. {rank['domain']} - {rank['match_percentage']}% match")
            
            return True
        else:
            print(f"❌ Compare domains failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Compare domains error: {str(e)}")
        return False

def test_market_signals():
    """Test market signals endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/market/signals/data scientist?location=Bangalore")
        print(f"Market Signals Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            signals = data['market_signals']
            print(f"✅ Market signals passed: {data['domain']}")
            print(f"   Demand Score: {signals['demand_score']}")
            print(f"   Competition Level: {signals['comp_level']}")
            print(f"   Saturation Risk: {signals['sat_risk']}")
            return True
        else:
            print(f"❌ Market signals failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Market signals error: {str(e)}")
        return False

def test_data_stats():
    """Test data statistics endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/api/data/stats")
        print(f"Data Stats Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            stats = data['stats']
            print(f"✅ Data stats passed: {stats['total_records']} records")
            print(f"   Job Types: {len(stats['job_types'])}")
            print(f"   Mean Salary: {stats['salary_stats']['mean']:.2f} Lakhs")
            return True
        else:
            print(f"❌ Data stats failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Data stats error: {str(e)}")
        return False

def test_error_cases():
    """Test error handling"""
    print("\n--- Testing Error Cases ---")
    
    # Test invalid domain
    try:
        response = requests.post(
            f"{BASE_URL}/api/recommend/analyze",
            json={"domain": "invalid_domain", "user_profile": {"skills": ["Python"]}},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✅ Invalid domain error handled correctly")
        else:
            print(f"❌ Invalid domain error not handled: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid domain test error: {str(e)}")
    
    # Test invalid user profile
    try:
        response = requests.post(
            f"{BASE_URL}/api/recommend",
            json={"skills": [], "experience": "invalid"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 400:
            print("✅ Invalid profile error handled correctly")
        else:
            print(f"❌ Invalid profile error not handled: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid profile test error: {str(e)}")

def main():
    """Run all API tests"""
    print("🧪 Testing Job Trend Predictor API")
    print("=" * 50)
    
    # Wait a moment for server to start
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Get Domains", test_get_domains),
        ("Recommendations", test_recommendations),
        ("Analyze Domain", test_analyze_domain),
        ("Compare Domains", test_compare_domains),
        ("Market Signals", test_market_signals),
        ("Data Stats", test_data_stats),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    # Test error cases
    test_error_cases()
    
    print(f"\n{'=' * 50}")
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed")
    
    return passed == total

if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:5000")
    print("Start with: python src/api/routes.py")
    print("\nPress Enter to start testing...")
    input()
    
    success = main()
    exit(0 if success else 1)
