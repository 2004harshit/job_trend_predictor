import pandas as pd
import numpy as np

class SkillTransferabilityEngine:
    def __init__(self):
        pass

    def _get_domain_skill_profile(self, df, domain):
        """Extracts unique skills and their market frequencies for a domain."""
        domain_df = df[df['TItle_Cleaned'].str.contains(domain, case=False, na=False)]
        if domain_df.empty:
            return {}, 0
        
        # Split and clean skills
        all_skills = domain_df['Combined_Skills'].str.cat(sep=',').split(',')
        all_skills = [s.strip().lower() for s in all_skills if s.strip()]
        
        # Calculate frequency of each skill within the domain (as a proxy for importance)
        total_postings = len(domain_df)
        skill_counts = pd.Series(all_skills).value_counts()
        skill_importance = (skill_counts / total_postings).to_dict()
        
        return skill_importance, len(all_skills)

    def calculate_transferability(self, df, source_domain, target_domain):
        # 1. Get Skill Profiles
        source_profile, total_s = self._get_domain_skill_profile(df, source_domain)
        target_profile, total_t = self._get_domain_skill_profile(df, target_domain)

        if not source_profile or not target_profile:
            return {"error": "Insufficient data for one or both domains"}

        source_skills = set(source_profile.keys())
        target_skills = set(target_profile.keys())

        # 2. Math Logic: Intersection (Common Skills)
        common_skills = source_skills.intersection(target_skills)

        # 3. Weighted Transferability
        # Σ(importance_in_source * importance_in_target)
        weighted_score = 0
        for skill in common_skills:
            # We multiply importance in both domains to find 'High Value' overlaps
            weighted_score += (source_profile[skill] * target_profile[skill])

        # Normalize the score (0.0 to 1.0)
        # Simple Overlap Ratio
        overlap_ratio = len(common_skills) / len(source_skills) if source_skills else 0
        
        # Final Interpretation
        if overlap_ratio > 0.6:
            status = "High (Easy Switch)"
        elif 0.3 <= overlap_ratio <= 0.6:
            status = "Medium (Moderate Effort)"
        else:
            status = "Low (Significant Reskilling)"

        return {
            "Path": f"{source_domain} → {target_domain}",
            "Transferability_Score": round(overlap_ratio, 2),
            "Weighted_Market_Value": round(weighted_score, 2),
            "Switch_Feasibility": status,
            "Shared_Bridge_Skills": list(common_skills)[:10],
            "New_Skills_To_Learn": list(target_skills - source_skills)[:5]
        }


if __name__ == "__main__":    # Example usage
    path = r"D:\DATA SCIENCE AND ML\Project\job_trend_predictor\data\processed\cleaned\cleaned_job_data.csv"
    df = pd.read_csv(path)
    ste = SkillTransferabilityEngine()
    # report = ste.calculate_transferability(df, "Data Scientist", "Machine Learning Engineer")
    report = ste.calculate_transferability(df, "Data Scientist", "Web Developer")
    print(report)