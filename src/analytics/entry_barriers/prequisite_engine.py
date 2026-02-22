import pandas as pd

class PrerequisiteEngine:
    def __init__(self):
        # The Tech Tree: Key = Skill, Value = List of Prerequisites
        self.skill_tree = {
            'Machine Learning': ['Statistics', 'Python'],
            'Statistics': ['Calculus', 'Basic Math'],
            'Deep Learning': ['Machine Learning', 'Linear Algebra'],
            'Data Science': ['Statistics', 'Python', 'SQL'],
            'React': ['JavaScript'],
            'JavaScript': ['HTML', 'CSS'],
            'Calculus': ['Basic Math'],
            'Linear Algebra': ['Basic Math'],
            'Python': ['Logic'],
            'SQL': ['Logic']
        }

    def _get_max_depth(self, skill, current_depth=0):
        """Recursive function to find the depth of a skill's requirements."""
        if skill not in self.skill_tree or not self.skill_tree[skill]:
            return current_depth
        
        # Check all prerequisites and find the longest path
        depths = [self._get_max_depth(prereq, current_depth + 1) for prereq in self.skill_tree[skill]]
        return max(depths)

    def analyze_prerequisites(self, df, target_domain, user_skills):
        # 1. Get typical required skills for the domain from the data
        domain_df = df[df['TItle_Cleaned'].str.contains(target_domain, case=False, na=False)]
        
        # Extract unique skills (assuming they are comma-separated in 'Combined_Skills')
        all_skills = domain_df['Combined_Skills'].str.cat(sep=',').split(',')
        required_skills = list(set([s.strip() for s in all_skills if s.strip() != ""]))
        
        if not required_skills:
            return {"error": "No skills data found for this domain."}

        # 2. Calculate Depth for the "Heaviest" Skill in the domain
        # This tells us how complex the background needs to be
        max_path = 0
        for skill in required_skills:
            depth = self._get_max_depth(skill)
            if depth > max_path:
                max_path = depth
        
        # 3. Classification Based on Depth
        if max_path == 0:
            classification = "None / Direct Entry"
        elif max_path == 1:
            classification = "Basic Programming / Scripting"
        else:
            classification = "Math + Stats + Logic (High Complexity)"

        # 4. Skill Overlap Score (Personalized)
        user_skills_set = set([s.lower() for s in user_skills])
        required_skills_set = set([s.lower() for s in required_skills])
        
        common_skills = user_skills_set.intersection(required_skills_set)
        overlap_score = len(common_skills) / len(required_skills_set)

        if overlap_score > 0.7:
            status = "You're close"
        elif overlap_score < 0.3:
            status = "Significant gap"
        else:
            status = "Moderate progress"

        return {
            "Domain": target_domain,
            "Prerequisite_Depth": max_path,
            "Classification": classification,
            "Overlap_Score": round(overlap_score, 2),
            "Status": status,
            "Missing_Key_Skills": list(required_skills_set - user_skills_set)[:5] # Show top 5 missing
        }

if __name__ == "__main__":
    # Example usage
    df = pd.read_csv(r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv")
    engine = PrerequisiteEngine()

    report  = engine.analyze_prerequisites(df, "Data Scientist", ["Python", "Logic"])
    print(report)