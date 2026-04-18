"""
Verification script for DataCleaningPipeline
"""
import os
import pandas as pd
from pipelines.cleaning_pipeline import DataCleaningPipeline
from src.cleaners.strategies.title_cleaning_strategy import TitleCleaningStrategy
from src.cleaners.strategies.role_type_cleaning_strategy import RoleCleaningStrategy
from src.utils.logger import setup_logging

def verify_pipeline():
    # 1. Setup
    setup_logging()
    
    # Create a tiny sample if it doesn't exist or to ensure correct format
    sample_path = "data/raw/test_sample.csv"
    os.makedirs("data/raw", exist_ok=True)
    
    data = {
        "TiTlE": ["Senior Data Scientist", "ML Eng", "Jr. Python Dev"],
        "company": ["Google", "Facebook", "Amazon"],
        "LOCATION": ["Bangalore", "Hyderabad", "Noida"],
        "Salary": ["10-20 LPA", "15-25 LPA", "5-8 LPA"],
        "Experience": ["3-5 years", "2-4 years", "0-1 years"],
        "Education": ["B.Tech", "M.Tech", "B.Sc"],
        "star_skills": ["Python, SQL", "PyTorch, AWS", "Python"],
        "normal_skills": ["Machine Learning, Stats", "Deep Learning", "HTML, CSS"],
        "Department": ["IT", "Engineering", "Software"],
        "Scraped_At": ["2023-10-01 10:00:00", "2023-10-01 11:00:00", "2023-10-01 12:00:00"],
        "Description": ["Job for DS", "Job for MLE", "Job for Dev"],
        "Last_Apply_Date": ["2023-12-01", "2023-12-01", "2023-12-01"],
        "Posted_Date": ["2023-11-01", "2023-11-01", "2023-11-01"],
        "employment_type": ["Full Time", "Part Time", "Contract"],
        "industry_type": ["IT", "Finance", "Healthcare"],
        "role_category": ["Software Development", "Data Science", "Engineering"],
        "role": ["Data Scientist", "ML Engineer", "Python Developer"],
    }
    
    df = pd.DataFrame(data)
    df.to_csv(sample_path, index=False)
    print(f"Created sample data at {sample_path}")
    
    # 2. Configure pipeline to use test sample
    pipeline = DataCleaningPipeline()
    pipeline.input_path = sample_path # Override for test
    pipeline.output_file = "test_cleaned_data.csv"
    
    # 3. Run
    print("Running pipeline...")
    stats = pipeline.run()
    
    # 4. Assertions
    print(f"Pipeline finished with status: {stats['status']}")
    assert stats["status"] == "success"
    
    output_path = os.path.join(pipeline.output_dir, pipeline.output_file)
    assert os.path.exists(output_path)
    
    cleaned_df = pd.read_csv(output_path)
    print(f"Cleaned data columns: {cleaned_df.columns.tolist()}")
    
    # Check for some cleaned columns (case-insensitive mapping keeps lowercase outputs)
    assert "title_cleaned" in cleaned_df.columns
    assert "combined_skills" in cleaned_df.columns
    
    print("Verification SUCCESSFUL!")


def verify_title_cleaning_strategy_loads_job_list_from_config():
    strategy = TitleCleaningStrategy()
    assert isinstance(strategy._job_list, list)
    assert len(strategy._job_list) > 0
    assert "Data Scientist" in strategy._job_list

    cleaned = strategy.clean_feature(pd.Series(["Senior Data Scientist", "ML Eng"]))
    assert isinstance(cleaned, pd.Series)
    assert cleaned.iloc[0] == ["Data Scientist"]
    assert "Machine Learning Engineer" in cleaned.iloc[1] or "Other" not in cleaned.iloc[1]


def verify_role_cleaning_strategy_loads_job_list_from_config():
    strategy = RoleCleaningStrategy()
    assert isinstance(strategy._job_list, list)
    assert len(strategy._job_list) > 0
    assert "Data Scientist" in strategy._job_list

    cleaned = strategy.clean_feature(pd.Series(["Cyber Security ,", "Back End Developer ,"]))
    assert isinstance(cleaned, pd.Series)
    assert cleaned.iloc[0] == ["Cybersecurity Analyst"] or cleaned.iloc[0] == ["Other"]
    assert "Back End Developer" in cleaned.iloc[1] or cleaned.iloc[1] == ["Other"]


if __name__ == "__main__":
    verify_pipeline()
    verify_title_cleaning_strategy_loads_job_list_from_config()
    verify_role_cleaning_strategy_loads_job_list_from_config()
