import pandas as pd
import numpy as np

class CareerPathEngine:
    def __init__(self):
        # Configuration for Learning Times (Base hours per skill)
        self.base_skill_hours = 40 
        
        # Interview Weights (Alpha, Beta, Gamma) per Domain
        self.domain_weights = {
            'ml engineer': {'alpha': 0.3, 'beta': 0.4, 'gamma': 0.3},
            'data scientist': {'alpha': 0.2, 'beta': 0.5, 'gamma': 0.3},
            'web development': {'alpha': 0.5, 'beta': 0.4, 'gamma': 0.1}
        }

    def calculate_learning_readiness(self, df, target_domain, user_skills, prior_knowledge="basic"):
        # 1. Filter Domain Data
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)].copy()
        avg_req_skills = int(domain_df['Skill_Count'].mean()) if not domain_df.empty else 5

        # --- METRIC 1: Learning Time ---
        pk_factor = {"none": 1.0, "basic": 0.7, "advanced": 1.5}.get(prior_knowledge, 1.0)
        learning_time_hours = (avg_req_skills * self.base_skill_hours) * 1.2 * pk_factor # 1.2 is the 20% buffer
        
        # --- METRIC 2: Prerequisites & Overlap ---
        required_skills_set = set(domain_df['Combined_Skills'].str.cat(sep=',').split(','))
        user_skills_set = set(user_skills)
        common_skills = user_skills_set.intersection(required_skills_set)
        
        overlap_score = len(common_skills) / avg_req_skills if avg_req_skills > 0 else 0
        readiness_status = "You're close" if overlap_score > 0.7 else "Significant gap"

        # --- METRIC 3: Project Complexity ---
        # w1*features + w2*stack + w3*apis + w4*deploy
        # Benchmarking against median expectations
        complexity_score = (0.4 * 5) + (0.3 * 4) + (0.2 * 2) + (0.1 * 1) # Example weights
        project_level = "Advanced" if complexity_score > 3.5 else "Medium"

        # --- METRIC 4: Interview Difficulty ---
        weights = self.domain_weights.get(target_domain.lower(), {'alpha': 0.33, 'beta': 0.33, 'gamma': 0.33})
        # Mocking DSA scores for the engine logic
        dsa_score = (0.6 * 0.3) + (0.3 * 0.5) + (0.1 * 0.2) # 60% Easy, 30% Med, 10% Hard
        interview_diff = (weights['alpha'] * dsa_score) + (weights['beta'] * 0.7) + (weights['gamma'] * 0.5)

        # --- METRIC 5: Hidden Blocker Alert ---
        blockers = []
        fresher_jobs_pct = (len(domain_df[domain_df['Min_Experience'] <= 1]) / len(domain_df)) * 100 if not domain_df.empty else 0
        
        if target_domain.lower() == "ml engineer" and "Math" in str(domain_df['Description_Cleaned']):
            blockers.append({"type": "Math-heavy", "severity": 0.8})
        if fresher_jobs_pct < 30:
            blockers.append({"type": "Internship Required", "severity": 0.9})

        return {
            "Time_To_Ready": f"{round(learning_time_hours)} Hours",
            "Skill_Overlap": f"{round(overlap_score * 100)}%",
            "Readiness": readiness_status,
            "Required_Project_Level": project_level,
            "Interview_Difficulty_Index": round(interview_diff, 2),
            "Alerts": blockers
        }
    

if __name__ == "__main__":

    # Load your cleaned job data
    job_data = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    # 1. Instantiate the engine
    cpe = CareerPathEngine()

    # 2. Define the user's current situation
    user_current_skills = ['Python', 'Pandas', 'Basic Statistics', 'Excel']
    target_role = "Data Scientist"

    # 3. Call the engine
    # You can specify prior_knowledge as "none", "basic", or "advanced"
    readiness_report = cpe.calculate_learning_readiness(
        df=job_data, 
        target_domain=target_role, 
        user_skills=user_current_skills,
        prior_knowledge="basic"
    )

    # 4. Access the metrics
    print(f"Time to get Job-Ready: {readiness_report['Time_To_Ready']}")
    print(f"Current Skill Overlap: {readiness_report['Skill_Overlap']}")
    print(f"Interview Difficulty: {readiness_report['Interview_Difficulty_Index']}")