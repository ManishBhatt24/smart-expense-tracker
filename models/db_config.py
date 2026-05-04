import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

# We expect SUPABASE_DB_URL in the .env file
# Format: postgresql://postgres.xxxx:password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
DB_URL = os.getenv('SUPABASE_DB_URL')

def get_db_connection():
    if not DB_URL:
        print("SUPABASE_DB_URL is not set in .env. Please configure your Supabase connection string.")
        return None
    try:
        conn = psycopg2.connect(DB_URL)
        return conn
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        return None

def query_db(query, params=(), one=False):
    conn = get_db_connection()
    if not conn:
        return None if one else []
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(query, params)
        
        # Commit for data-modifying queries
        if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP']):
            conn.commit()
            rv = None
        else:
            rv = cursor.fetchall()
            
    except Exception as e:
        print(f"Database error executing query '{query}': {e}")
        rv = []
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        
    return (rv[0] if rv else None) if one else rv

def init_db():
    conn = get_db_connection()
    if not conn:
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                email VARCHAR(255) UNIQUE,
                password VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                amount DECIMAL(10, 2),
                category VARCHAR(255),
                date DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                amount DECIMAL(10, 2),
                source VARCHAR(255),
                date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                limit_amount DECIMAL(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error initializing Supabase tables: {e}")
    finally:
        cursor.close()
        conn.close()
