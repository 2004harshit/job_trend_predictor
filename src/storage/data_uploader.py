# upload_to_neon.py
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import re

load_dotenv()

NEON_URL = os.getenv('NEON_URL')
CSV_PATH = os.getenv('CSV_PATH')

neon_engine = create_engine(NEON_URL)

# ══════════════════════════════════════════════
# PART 1 — GENERAL JOBS (CSV → Neon)
# ══════════════════════════════════════════════

print("=" * 50)
print("PART 1: General Jobs CSV Upload")
print("=" * 50)

print("📂 CSV load ho raha hai — thoda time lagega...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"   ✅ Loaded — {len(df)} rows, {df.memory_usage().sum()/1024/1024:.1f} MB")

# ── Sirf zaruri columns rakho ─────────────────
keep_columns = [
    'title', 'company', 'min_salary', 'max_salary', 'avg_salary',
       'ug_degree', 'ug_specialization', 'pg_degree', 'pg_specialization',
       'description', 'role', 'role_category', 'industry_type', 'department',
       'skills', 'skill_count', 'min_experience', 'max_experience', 'location',
       'timestamp', 'last_apply_date', 'no_of_applicant', 'no_of_opening',
       'posted_timestamp']


# Sirf woh columns lo jo exist karti hain
existing_cols = [c for c in keep_columns if c in df.columns]
missing_cols  = [c for c in keep_columns if c not in df.columns]

if missing_cols:
    print(f"   ⚠️  Yeh columns nahi mile: {missing_cols}")

df = df[existing_cols]
print(f"   Columns: 40 → {len(df.columns)}")

# # ── Column names standardize karo ─────────────
# df.columns = [
#     col.lower().replace(' ', '_')
#     for col in df.columns
# ]

# # ── Data types fix karo ───────────────────────
# for col in ['min_salary', 'max_salary', 'avg_salary']:
#     if col in df.columns:
#         df[col] = pd.to_numeric(df[col], errors='coerce')

# for col in ['min_experience', 'max_experience']:
#     if col in df.columns:
#         df[col] = pd.to_numeric(df[col], errors='coerce')

# if 'posted_date' in df.columns:
#     df['posted_date'] = pd.to_datetime(
#         df['posted_date'], errors='coerce'
#     )

# # ── Basic cleaning ────────────────────────────
# str_cols = ['location', 'title_cleaned', 'company_cleaned']
# for col in str_cols:
#     if col in df.columns:
#         df[col] = df[col].str.strip().str.title()

# # ── Salary outliers hatao ─────────────────────
# if 'avg_salary' in df.columns:
#     before = len(df)
#     df = df[
#         (df['avg_salary'].isna()) |
#         ((df['avg_salary'] >= 0) &
#          (df['avg_salary'] <= 10000000))
#     ]
#     print(f"   Outliers removed: {before - len(df)} rows")

# ── Neon mein upload karo ─────────────────────
print(f"\n☁️  Neon mein upload ho raha hai...")
print(f"   Rows: {len(df)} | Columns: {len(df.columns)}")
print(f"   Yeh 3-5 minute le sakta hai — wait karo...")

chunk_size = 500
total_chunks = len(df) // chunk_size + 1

for i, chunk_start in enumerate(range(0, len(df), chunk_size)):
    chunk = df.iloc[chunk_start:chunk_start + chunk_size]
    chunk.to_sql(
        'general_job_data',
        neon_engine,
        if_exists='replace' if i == 0 else 'append',
        index=False,
        method='multi'
    )
    # Progress show karo
    progress = min(chunk_start + chunk_size, len(df))
    print(f"   Progress: {progress}/{len(df)} rows "
          f"({progress/len(df)*100:.0f}%)", end='\r')

print(f"\n✅ General jobs done! — {len(df)} rows uploaded")


# # ══════════════════════════════════════════════
# # PART 2 — FRESHER JOBS (MySQL → Neon)
# # ══════════════════════════════════════════════

# print("\n" + "=" * 50)
# print("PART 2: Fresher Jobs MySQL Upload")
# print("=" * 50)

# try:
#     mysql_conn = mysql.connector.connect(
#         host=os.getenv('MYSQL_HOST'),
#         user=os.getenv('MYSQL_USER'),
#         password=os.getenv('MYSQL_PASSWORD'),
#         database=os.getenv('MYSQL_DATABASE')
#     )
#     print("✅ MySQL connected!")

#     df_f = pd.read_sql("SELECT * FROM raw_job_data", mysql_conn)
#     mysql_conn.close()
#     print(f"   Loaded — {len(df_f)} rows")

#     # ── Unnecessary columns drop karo ─────────
#     drop_cols = ['description', 'job_url', 'scraped_at', 'id']
#     df_f = df_f.drop(
#         columns=[c for c in drop_cols if c in df_f.columns]
#     )

#     # ── Skills combine karo ───────────────────
#     df_f['combined_skills'] = (
#         df_f['star_skills'].fillna('') + ',' +
#         df_f['normal_skills'].fillna('')
#     ).str.strip(',')
#     df_f = df_f.drop(
#         columns=['star_skills', 'normal_skills'],
#         errors='ignore'
#     )

#     # ── Experience extract karo ───────────────
#     def extract_exp(exp_str):
#         if pd.isna(exp_str):
#             return None, None
#         nums = re.findall(r'\d+', str(exp_str))
#         if len(nums) >= 2:
#             return int(nums[0]), int(nums[1])
#         elif len(nums) == 1:
#             return int(nums[0]), int(nums[0])
#         return None, None

#     df_f[['min_experience', 'max_experience']] = (
#         df_f['experience']
#         .apply(lambda x: pd.Series(extract_exp(x)))
#     )

#     # ── Salary extract karo ───────────────────
#     def extract_salary(sal_str):
#         if pd.isna(sal_str):
#             return None, None, None
#         nums = re.findall(
#             r'[\d.]+',
#             str(sal_str).replace(',', '')
#         )
#         nums = [float(n) for n in nums if float(n) > 0]
#         if len(nums) >= 2:
#             return nums[0], nums[1], (nums[0]+nums[1])/2
#         elif len(nums) == 1:
#             return nums[0], nums[0], nums[0]
#         return None, None, None

#     df_f[['min_salary', 'max_salary', 'avg_salary']] = (
#         df_f['salary']
#         .apply(lambda x: pd.Series(extract_salary(x)))
#     )

#     # ── Date fix karo ─────────────────────────
#     df_f['posted_date'] = pd.to_datetime(
#         df_f['posted_date'], errors='coerce'
#     )
#     df_f['location'] = df_f['location'].str.strip().str.title()

#     # ── Neon mein upload karo ─────────────────
#     print("☁️  Fresher jobs Neon mein upload ho rahe hain...")
#     df_f.to_sql(
#         'fresher_jobs',
#         neon_engine,
#         if_exists='replace',
#         index=False,
#         chunksize=500,
#         method='multi'
#     )
#     print(f"✅ Fresher jobs done! — {len(df_f)} rows uploaded")

# except Exception as e:
#     print(f"❌ MySQL Error: {e}")
#     print("   Fresher data baad mein upload kar sakte ho")


# # ══════════════════════════════════════════════
# # PART 3 — VERIFY
# # ══════════════════════════════════════════════

# print("\n" + "=" * 50)
# print("PART 3: Verification")
# print("=" * 50)

# with neon_engine.connect() as conn:
#     tables = ['general_jobs', 'fresher_jobs']
#     for table in tables:
#         try:
#             count = conn.execute(
#                 text(f"SELECT COUNT(*) FROM {table}")
#             ).scalar()
#             print(f"   ✅ {table}: {count} rows")
#         except:
#             print(f"   ❌ {table}: table nahi mili")

# print("\n🎉 Upload complete!")
# print("Neon dashboard pe jaake verify karo:")
# print("Tables → general_jobs aur fresher_jobs dikhni chahiye")