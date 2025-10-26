"""
Model prediction utilities for Job Trend Predictor
"""
import joblib
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path for imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class SalaryPredictor:
    """Class to handle salary predictions using trained model"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.label_encoders = None
        self.feature_info = None
        self.models_dir = os.path.join(PROJECT_ROOT, 'models')
        self.loaded = False
    
    def load_models(self):
        """Load all trained model components"""
        try:
            # Load model
            self.model = joblib.load(os.path.join(self.models_dir, 'best_salary_model.pkl'))
            
            # Load scaler
            self.scaler = joblib.load(os.path.join(self.models_dir, 'salary_scaler.pkl'))
            
            # Load feature selector
            self.feature_selector = joblib.load(os.path.join(self.models_dir, 'feature_selector.pkl'))
            
            # Load label encoders
            self.label_encoders = joblib.load(os.path.join(self.models_dir, 'label_encoders.pkl'))
            
            # Load feature info
            self.feature_info = joblib.load(os.path.join(self.models_dir, 'feature_info.pkl'))
            
            self.loaded = True
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            self.loaded = False
            return False
    
    def predict_salary(self, user_data):
        """
        Predict salary based on user inputs
        
        Args:
            user_data: dict with keys:
                - experience: years of experience
                - location: 'Tier 1', 'Tier 2', or 'Tier 3'
                - education: 'Graduate', 'Postgraduate', or 'Other'
                - programming_skills: count
                - ml_skills: count
                - data_skills: count
                - cloud_skills: count
                - skills_input: comma-separated string
                - company_size: 'Small', 'Medium', or 'Large'
                - industry: industry type
        
        Returns:
            dict with predicted_salary, confidence, and additional info
        """
        if not self.loaded:
            if not self.load_models():
                return self._fallback_prediction(user_data)
        
        try:
            # Create feature vector
            features = self._create_features(user_data)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Apply feature selection
            features_selected = self.feature_selector.transform(features_scaled)
            
            # Predict
            salary_pred = self.model.predict(features_selected)[0]
            
            # Calculate confidence (simplified based on R² score from training)
            confidence = min(90, 50 + (user_data['experience'] * 2) + 
                           (user_data['programming_skills'] + user_data['ml_skills']) * 2)
            
            # Ensure positive salary
            salary_pred = max(2.0, float(salary_pred))
            
            return {
                'predicted_salary': round(salary_pred, 2),
                'confidence': round(confidence, 0),
                'model_used': 'ML Model'
            }
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            return self._fallback_prediction(user_data)
    
    def _create_features(self, user_data):
        """Create feature vector from user input"""
        # Initialize features dict
        features_dict = {}
        
        # Basic features
        features_dict['experience_years'] = user_data['experience']
        features_dict['programming_skills_count'] = user_data['programming_skills']
        features_dict['ml_skills_count'] = user_data['ml_skills']
        features_dict['data_skills_count'] = user_data['data_skills']
        features_dict['cloud_skills_count'] = user_data['cloud_skills']
        
        # Skills count
        skill_list = [s.strip().lower() for s in user_data.get('skills_input', '').split(',') if s.strip()]
        features_dict['skills_count'] = len(skill_list)
        
        # Compute skill diversity
        features_dict['skill_diversity'] = (
            features_dict['programming_skills_count'] +
            features_dict['ml_skills_count'] +
            features_dict['data_skills_count'] +
            features_dict['cloud_skills_count']
        )
        
        # Interaction features
        features_dict['exp_skill_interaction'] = (
            features_dict['experience_years'] * features_dict['skill_diversity']
        )
        
        # Company size (simplified encoding: Small=1, Medium=3, Large=10)
        company_size_map = {'Small': 1, 'Medium': 3, 'Large': 10}
        features_dict['company_size'] = company_size_map.get(user_data['company_size'], 1)
        
        features_dict['company_exp_interaction'] = (
            features_dict['company_size'] * features_dict['experience_years']
        )
        
        # Location premium
        location_premium_map = {'Tier 1': 1.2, 'Tier 2': 1.0, 'Tier 3': 0.8}
        features_dict['location_premium'] = location_premium_map.get(user_data['location'], 1.0)
        
        # Education numeric
        education_map = {'Graduate': 1, 'Postgraduate': 2, 'Other': 0.5}
        features_dict['education_numeric'] = education_map.get(user_data['education'], 1)
        
        # Industry multiplier (simplified)
        features_dict['industry_multiplier'] = 1.0
        
        # Skill binary features
        skill_features = [
            'python', 'sql', 'java', 'javascript', 'aws', 
            'machine learning', 'agile', 'html', 'project management',
            'mysql', 'devops', 'linux', 'ci/cd', 'css', 'data analysis'
        ]
        
        skills_lower = [s.lower() for s in skill_list]
        for skill in skill_features:
            features_dict[f'has_{skill.replace(" ", "_").replace("/", "_")}'] = (
                1 if skill.lower() in skills_lower else 0
            )
        
        # Categorical features encoding
        if self.label_encoders:
            try:
                features_dict['city_tier_encoded'] = self._safe_encode(
                    'city_tier', user_data['location']
                )
                features_dict['experience_level_encoded'] = self._get_experience_level(
                    user_data['experience']
                )
                features_dict['education_level_encoded'] = self._safe_encode(
                    'education_level', user_data['education']
                )
                features_dict['company_size_category_encoded'] = self._safe_encode(
                    'company_size_category', user_data['company_size']
                )
            except:
                features_dict['city_tier_encoded'] = 0
                features_dict['experience_level_encoded'] = 1
                features_dict['education_level_encoded'] = 0
                features_dict['company_size_category_encoded'] = 0
        
        # Create DataFrame in same order as training
        # Get feature names from feature_info or use defaults
        feature_names = [
            'experience_years', 'skills_count', 'programming_skills_count', 
            'ml_skills_count', 'data_skills_count', 'cloud_skills_count',
            'company_size', 'skill_diversity', 'exp_skill_interaction',
            'company_exp_interaction', 'location_premium', 'education_numeric',
            'industry_multiplier', 'has_python', 'has_sql', 'has_java',
            'has_javascript', 'has_aws', 'has_machine_learning', 'has_agile',
            'has_html', 'has_project_management', 'has_mysql', 'has_devops',
            'has_linux', 'has_ci/cd', 'has_css', 'has_data_analysis',
            'city_tier_encoded', 'experience_level_encoded', 
            'education_level_encoded', 'company_size_category_encoded'
        ]
        
        # Create DataFrame
        features_list = [features_dict.get(name, 0) for name in feature_names]
        features_df = pd.DataFrame([features_list], columns=feature_names)
        
        return features_df
    
    def _safe_encode(self, feature_name, value):
        """Safely encode categorical value"""
        if self.label_encoders and feature_name in self.label_encoders:
            try:
                return self.label_encoders[feature_name].transform([value])[0]
            except:
                return 0
        return 0
    
    def _get_experience_level(self, exp_years):
        """Get experience level encoding"""
        if exp_years <= 2:
            return 0  # Fresher
        elif exp_years <= 5:
            return 1  # Mid-level
        elif exp_years <= 10:
            return 2  # Senior
        else:
            return 3  # Expert
    
    def _fallback_prediction(self, user_data):
        """Fallback prediction when model is not available"""
        base_salary = (3.5 + (user_data['experience'] * 0.8) + 
                      (user_data['programming_skills'] * 0.3) + 
                      (user_data['ml_skills'] * 0.4))
        
        location_multiplier = {"Tier 1": 1.2, "Tier 2": 1.0, "Tier 3": 0.8}[user_data['location']]
        education_multiplier = {"Graduate": 1.0, "Postgraduate": 1.2, "Other": 0.9}[user_data['education']]
        
        predicted_salary = base_salary * location_multiplier * education_multiplier
        confidence = min(95, 60 + (user_data['experience'] * 2) + 
                        (user_data['programming_skills'] + user_data['ml_skills'] + user_data['data_skills']) * 3)
        
        return {
            'predicted_salary': round(predicted_salary, 2),
            'confidence': round(confidence, 0),
            'model_used': 'Heuristic (ML Model not loaded)'
        }


# Global instance
_predictor_instance = None

def get_predictor():
    """Get singleton predictor instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = SalaryPredictor()
        _predictor_instance.load_models()
    return _predictor_instance
