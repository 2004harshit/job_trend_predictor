# src/storage/migrations/fresher_jobs.py
import pandas as pd
import re
from src.storage.connection import get_neon_engine, get_mysql_connection

def extract_exp(exp_str):
    if pd.isna(exp_str): return None, None
    nums = re.findall(r'\d+', str(exp_str))
    if len(nums) >= 2: return int(nums[0]), int(nums[1])
    if len(nums) == 1: return int(nums[0]), int(nums[0])
    return None, None

def extract_salary(sal_str):
    if pd.isna(sal_str): return None, None, None
    nums = [float(n) for n in re.findall(
        r'[\d.]+', str(sal_str).replace(',', '')
    ) if float(n) > 0]
    if len(nums) >= 2: return nums[0], nums[1], (nums[0]+nums[1])/2
    if len(nums) == 1: return nums[0], nums[0], nums[0]
    return None, None, None

def migrate_fresher_jobs():
    print("=" * 50)
    print("PART 2: Fresher Jobs MySQL → Neon")
    print("=" * 50)

    neon_engine = get_neon_engine()

    try:
        mysql_conn = get_mysql_connection()
        print("✅ MySQL connected!")

        df = pd.read_sql("SELECT * FROM raw_job_data", mysql_conn)
        mysql_conn.close()
        print(f"   Loaded — {len(df)} rows")

        # Clean
        drop_cols = ['description', 'job_url', 'scraped_at', 'id']
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])

        df['combined_skills'] = (
            df['star_skills'].fillna('') + ',' +
            df['normal_skills'].fillna('')
        ).str.strip(',')
        df = df.drop(
            columns=['star_skills', 'normal_skills'], errors='ignore'
        )

        df[['min_experience','max_experience']] = (
            df['experience'].apply(
                lambda x: pd.Series(extract_exp(x))
            )
        )
        df[['min_salary','max_salary','avg_salary']] = (
            df['salary'].apply(
                lambda x: pd.Series(extract_salary(x))
            )
        )
        df['posted_date'] = pd.to_datetime(
            df['posted_date'], errors='coerce'
        )
        df['location'] = df['location'].str.strip().str.title()

        # Upload
        print("☁️  Fresher jobs upload ho rahe hain...")
        df.to_sql(
            'fresher_jobs', neon_engine,
            if_exists='replace', index=False,
            chunksize=500, method='multi'
        )
        print(f"✅ Fresher jobs done — {len(df)} rows")
        return len(df)

    except Exception as e:
        print(f"❌ Error: {e}")
        return 0