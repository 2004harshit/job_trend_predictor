import pandas as pd
import numpy as np

class RoleEvolutionEngine:
    def __init__(self):
        # Probability weights based on standard industry transitions
        # In a production environment, this is derived from career history datasets
        self.transition_probs = {
            'Junior Data Scientist': {'Mid Data Scientist': 0.75, 'Data Analyst': 0.15, 'ML Engineer': 0.10},
            'Mid Data Scientist': {'Senior Data Scientist': 0.60, 'ML Engineer': 0.25, 'Data Architect': 0.15},
            'Senior Data Scientist': {'Lead Data Scientist': 0.50, 'Principal Scientist': 0.30, 'Manager': 0.20}
        }

    def _get_time_in_role(self, df, title):
        """Math: Median(years_in_role) from experience range data"""
        role_df = df[df['TItle_Cleaned'].str.contains(title, case=False, na=False)]
        if role_df.empty: return 2.5 # Industry average fallback
        
        # Calculate span: Max_Exp - Min_Exp for that specific role title
        # This approximates how long people stay in this specific 'bracket'
        return (role_df['Max_Experience'] - role_df['Min_Experience']).median()

    def predict_evolution_path(self, df, current_role):
        path = []
        current = current_role
        total_probability = 1.0
        cumulative_years = 0

        # We predict 3 steps ahead (Junior -> Mid -> Senior -> Lead)
        for _ in range(3):
            if current not in self.transition_probs:
                break
            
            # 1. Find the Most Common Next Step (Highest Probability)
            next_role = max(self.transition_probs[current], key=self.transition_probs[current].get)
            prob = self.transition_probs[current][next_role]
            
            # 2. Calculate time in current role
            years = self._get_time_in_role(df, current)
            
            # 3. Update Path_Probability (Markov Chain Logic)
            total_probability *= prob
            cumulative_years += years
            
            path.append({
                "From": current,
                "To": next_role,
                "Transition_Probability": f"{round(prob * 100)}%",
                "Estimated_Duration": f"{round(years, 1)} Years"
            })
            
            current = next_role

        return {
            "Starting_Point": current_role,
            "Evolution_Path": path,
            "Full_Path_Confidence": f"{round(total_probability * 100, 2)}%",
            "Total_Years_to_Lead": round(cumulative_years, 1)
        }

if __name__ == "__main__":
    # Load your cleaned job data
    job_data = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    
    ree = RoleEvolutionEngine()
    # report = ree.predict_evolution_path(job_data, "Junior Data Scientist")
    # report = ree.predict_evolution_path(job_data, "Web Developer")
    report = ree.predict_evolution_path(job_data, "Frontend Developer")
    print(report)