"""
Test script for Analytics API
Comprehensive test cases for all analytics endpoints

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

def test_market_demand():
    """Test market demand analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"],
            "weights": {
                "Job_Posting_Frequency": 0.30,
                "Trend_Direction": 0.25,
                "Applicant_Demand_Ratio": 0.20,
                "Skill_Diversity": 0.15,
                "Experience_Flexibility": 0.10
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/market/demand",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Market Demand Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Market demand passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['demand_analysis'].items():
                if 'error' not in analysis:
                    print(f"   {domain}: {analysis.get('Overall_Demand_Score', 'N/A')} demand score")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Market demand failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Market demand error: {str(e)}")
        return False

def test_competition_level():
    """Test competition level analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"],
            "location": "Bangalore",
            "experience_band": [0, 3]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/market/competition",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Competition Level Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Competition level passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['competition_analysis'].items():
                if 'error' not in analysis:
                    print(f"   {domain}: {analysis.get('Level', 'N/A')} competition")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Competition level failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Competition level error: {str(e)}")
        return False

def test_saturation_risk():
    """Test saturation risk analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/market/saturation",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Saturation Risk Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Saturation risk passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['saturation_analysis'].items():
                if 'error' not in analysis:
                    print(f"   {domain}: {analysis.get('Risk_Level', 'N/A')} risk level")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Saturation risk failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Saturation risk error: {str(e)}")
        return False

def test_salary_analysis():
    """Test salary analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"],
            "experience_level": "entry"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/market/salary",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Salary Analysis Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Salary analysis passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['salary_analysis'].items():
                if 'error' not in analysis:
                    avg_salary = analysis.get('Average_Salary', 'N/A')
                    print(f"   {domain}: {avg_salary}L average salary")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Salary analysis failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Salary analysis error: {str(e)}")
        return False

def test_market_velocity():
    """Test market velocity analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/market/velocity",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Market Velocity Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Market velocity passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['velocity_analysis'].items():
                if 'error' not in analysis:
                    velocity = analysis.get('Hiring_Velocity', 'N/A')
                    print(f"   {domain}: {velocity} hiring velocity")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Market velocity failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Market velocity error: {str(e)}")
        return False

def test_career_path():
    """Test career path analysis endpoint"""
    try:
        payload = {
            "target_domain": "data scientist",
            "user_skills": ["Python", "SQL", "Excel"],
            "current_experience": 2,
            "math_comfort": "Moderate"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/career/path",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Career Path Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data['career_path_analysis']
            
            if 'error' not in analysis:
                readiness = analysis.get('Readiness_Score', 'N/A')
                print(f"✅ Career path passed: {readiness} readiness score")
                timeline = analysis.get('Timeline_Months', 'N/A')
                print(f"   Timeline: {timeline} months")
                return True
            else:
                print(f"❌ Career path failed: {analysis['error']}")
                return False
        else:
            print(f"❌ Career path failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Career path error: {str(e)}")
        return False

def test_role_evaluation():
    """Test role evaluation endpoint"""
    try:
        payload = {
            "target_role": "senior data scientist",
            "user_profile": {
                "skills": ["Python", "Machine Learning", "SQL"],
                "experience_years": 3,
                "education": "Bachelor's",
                "certifications": ["AWS", "TensorFlow"]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/career/role-evaluation",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Role Evaluation Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data['role_evaluation']
            
            if 'error' not in analysis:
                fit_score = analysis.get('Fit_Score', 'N/A')
                print(f"✅ Role evaluation passed: {fit_score} fit score")
                readiness = analysis.get('Readiness_Level', 'N/A')
                print(f"   Readiness: {readiness}")
                return True
            else:
                print(f"❌ Role evaluation failed: {analysis['error']}")
                return False
        else:
            print(f"❌ Role evaluation failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Role evaluation error: {str(e)}")
        return False

def test_ai_risk():
    """Test AI replacement risk analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer", "data analyst"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/domain/ai-risk",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"AI Risk Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI risk passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['ai_risk_analysis'].items():
                if 'error' not in analysis:
                    risk_level = analysis.get('Automation_Risk', 'N/A')
                    print(f"   {domain}: {risk_level} automation risk")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ AI risk failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ AI risk error: {str(e)}")
        return False

def test_domain_stability():
    """Test domain stability analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/domain/stability",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Domain Stability Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Domain stability passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['stability_analysis'].items():
                if 'error' not in analysis:
                    stability = analysis.get('Stability_Score', 'N/A')
                    print(f"   {domain}: {stability} stability score")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Domain stability failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Domain stability error: {str(e)}")
        return False

def test_salary_growth():
    """Test salary growth analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/domain/salary-growth",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Salary Growth Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Salary growth passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['salary_growth_analysis'].items():
                if 'error' not in analysis:
                    growth_rate = analysis.get('Growth_Rate', 'N/A')
                    print(f"   {domain}: {growth_rate} growth rate")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Salary growth failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Salary growth error: {str(e)}")
        return False

def test_skill_transferability():
    """Test skill transferability analysis endpoint"""
    try:
        payload = {
            "source_domain": "software engineer",
            "target_domains": ["data scientist", "ml engineer"],
            "user_skills": ["Python", "SQL", "Git"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/domain/skill-transferability",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Skill Transferability Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Skill transferability passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['transferability_analysis'].items():
                if 'error' not in analysis:
                    score = analysis.get('Transferability_Score', 'N/A')
                    print(f"   {domain}: {score} transferability score")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Skill transferability failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Skill transferability error: {str(e)}")
        return False

def test_interview_difficulty():
    """Test interview difficulty analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/barriers/interview-difficulty",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Interview Difficulty Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Interview difficulty passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['interview_difficulty_analysis'].items():
                if 'error' not in analysis:
                    difficulty = analysis.get('Difficulty_Level', 'N/A')
                    print(f"   {domain}: {difficulty} difficulty")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Interview difficulty failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Interview difficulty error: {str(e)}")
        return False

def test_hidden_blockers():
    """Test hidden blockers detection endpoint"""
    try:
        payload = {
            "domains": ["data scientist"],
            "user_profile": {
                "education": "Bachelor's",
                "experience_years": 2,
                "skills": ["Python", "SQL"]
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/barriers/hidden-blockers",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Hidden Blockers Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Hidden blockers passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['hidden_blockers_analysis'].items():
                if 'error' not in analysis:
                    risk = analysis.get('Risk_Assessment', 'N/A')
                    print(f"   {domain}: {risk} risk assessment")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Hidden blockers failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Hidden blockers error: {str(e)}")
        return False

def test_prerequisites():
    """Test prerequisites analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/barriers/prerequisites",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Prerequisites Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Prerequisites passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['prerequisites_analysis'].items():
                if 'error' not in analysis:
                    barrier = analysis.get('Entry_Barrier_Level', 'N/A')
                    print(f"   {domain}: {barrier} entry barrier")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Prerequisites failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Prerequisites error: {str(e)}")
        return False

def test_project_complexity():
    """Test project complexity evaluation endpoint"""
    try:
        payload = {
            "domains": ["data scientist", "software engineer"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/barriers/project-complexity",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Project Complexity Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Project complexity passed: {data['total_domains_analyzed']} domains analyzed")
            
            for domain, analysis in data['project_complexity_analysis'].items():
                if 'error' not in analysis:
                    complexity = analysis.get('Complexity_Level', 'N/A')
                    print(f"   {domain}: {complexity} complexity")
                else:
                    print(f"   {domain}: Error - {analysis['error']}")
            
            return True
        else:
            print(f"❌ Project complexity failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Project complexity error: {str(e)}")
        return False

def test_comprehensive_analysis():
    """Test comprehensive analysis endpoint"""
    try:
        payload = {
            "domains": ["data scientist"],
            "user_profile": {
                "skills": ["Python", "SQL"],
                "experience_years": 2,
                "education": "Bachelor's"
            },
            "include_market": True,
            "include_career": True,
            "include_domain": True,
            "include_barriers": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/analytics/comprehensive",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Comprehensive Analysis Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            analysis = data['comprehensive_analysis']
            
            categories = list(analysis.keys())
            print(f"✅ Comprehensive analysis passed: {len(categories)} categories analyzed")
            print(f"   Categories: {', '.join(categories)}")
            return True
        else:
            print(f"❌ Comprehensive analysis failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Comprehensive analysis error: {str(e)}")
        return False

def main():
    """Run all analytics API tests"""
    print("🧪 Testing Analytics API")
    print("=" * 50)
    
    # Wait a moment for server to start
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health_check),
        ("Market Demand", test_market_demand),
        ("Competition Level", test_competition_level),
        ("Saturation Risk", test_saturation_risk),
        ("Salary Analysis", test_salary_analysis),
        ("Market Velocity", test_market_velocity),
        ("Career Path", test_career_path),
        ("Role Evaluation", test_role_evaluation),
        ("AI Risk", test_ai_risk),
        ("Domain Stability", test_domain_stability),
        ("Salary Growth", test_salary_growth),
        ("Skill Transferability", test_skill_transferability),
        ("Interview Difficulty", test_interview_difficulty),
        ("Hidden Blockers", test_hidden_blockers),
        ("Prerequisites", test_prerequisites),
        ("Project Complexity", test_project_complexity),
        ("Comprehensive Analysis", test_comprehensive_analysis),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- Testing {test_name} ---")
        if test_func():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
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
