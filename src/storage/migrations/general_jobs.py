# src/storage/migrations/general_jobs.py
import pandas as pd
from src.storage.connection import get_neon_engine
from dotenv import load_dotenv
import os

load_dotenv()

KEEP_COLUMNS = [
    'title', 'company', 'min_salary', 'max_salary', 'avg_salary',
    'ug_degree', 'ug_specialization', 'pg_degree', 'pg_specialization',
    'description', 'role', 'role_category', 'industry_type', 'department',
    'skills', 'skill_count', 'min_experience', 'max_experience', 'location',
    'timestamp', 'last_apply_date', 'no_of_applicant', 'no_of_opening',
    'posted_timestamp'
]

def migrate_general_jobs():
    print("=" * 50)
    print("PART 1: General Jobs CSV → Neon")
    print("=" * 50)

    csv_path = os.getenv('CSV_PATH')
    neon_engine = get_neon_engine()

    # Load CSV
    print("📂 CSV load ho raha hai...")
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"   ✅ Loaded — {len(df)} rows")

    # Columns filter
    existing_cols = [c for c in KEEP_COLUMNS if c in df.columns]
    missing_cols  = [c for c in KEEP_COLUMNS if c not in df.columns]
    if missing_cols:
        print(f"   ⚠️  Missing columns: {missing_cols}")
    df = df[existing_cols]

    # Upload in chunks
    print(f"☁️  Neon mein upload ho raha hai ({len(df)} rows)...")
    chunk_size = 500
    for i, start in enumerate(range(0, len(df), chunk_size)):
        chunk = df.iloc[start:start + chunk_size]
        chunk.to_sql(
            'general_job_data',
            neon_engine,
            if_exists='replace' if i == 0 else 'append',
            index=False,
            method='multi'
        )
        progress = min(start + chunk_size, len(df))
        print(f"   Progress: {progress}/{len(df)} "
              f"({progress/len(df)*100:.0f}%)", end='\r')

    print(f"\n✅ General jobs done — {len(df)} rows")
    return len(df)