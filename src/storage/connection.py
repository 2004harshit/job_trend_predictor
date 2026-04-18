# src/storage/connection.py
# Ek jagah se saare connections manage honge

from sqlalchemy import create_engine
from dotenv import load_dotenv
import mysql.connector
import os

load_dotenv()

def get_neon_engine():
    """Neon PostgreSQL connection"""
    url = os.getenv('NEON_URL')
    if not url:
        raise ValueError("NEON_URL .env mein nahi mili")
    return create_engine(url)

def get_mysql_connection():
    """Local MySQL connection"""
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )