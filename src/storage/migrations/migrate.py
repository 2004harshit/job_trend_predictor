# src/storage/migrations/migrate.py
# Yeh chalao: python -m src.storage.migrations.migrate

from sqlalchemy import text
from src.storage.connection import get_neon_engine
from src.storage.migrations.general_jobs import migrate_general_jobs
from src.storage.migrations.fresher_jobs import migrate_fresher_jobs

def verify():
    print("\n" + "=" * 50)
    print("VERIFICATION")
    print("=" * 50)
    engine = get_neon_engine()
    with engine.connect() as conn:
        for table in ['general_job_data', 'fresher_jobs']:
            try:
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                ).scalar()
                print(f"   ✅ {table}: {count} rows")
            except Exception as e:
                print(f"   ❌ {table}: {e}")

if __name__ == "__main__":
    migrate_general_jobs()
    migrate_fresher_jobs()
    verify()
    print("\n🎉 Migration complete!")