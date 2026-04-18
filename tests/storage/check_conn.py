# test_connection.py
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv()

NEON_URL = os.getenv('NEON_URL')

try:
    engine = create_engine(NEON_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("✅ Neon connected!")
        print(f"   PostgreSQL: {result.fetchone()[0]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")