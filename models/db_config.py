import psycopg2
from psycopg2.extras import DictCursor
import os
from dotenv import load_dotenv

load_dotenv()

class DBConnection:
    def __init__(self, conn):
        self.conn = conn
    
    def cursor(self, dictionary=True):
        if dictionary:
            return self.conn.cursor(cursor_factory=DictCursor)
        else:
            return self.conn.cursor()
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

def get_db_connection():
    # Only connect using Supabase Postgres URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set. Please check your .env file or Vercel settings.")
        return None

    try:
        connection = psycopg2.connect(database_url)
        
        # Ensure tables exist in Supabase Postgres on startup
        cursor = connection.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY, 
                name VARCHAR(255) NOT NULL, 
                email VARCHAR(255) UNIQUE NOT NULL, 
                password TEXT NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
                amount DECIMAL(10, 2) NOT NULL, 
                category VARCHAR(255) NOT NULL, 
                date DATE NOT NULL, 
                description TEXT, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create income table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
                amount DECIMAL(10, 2) NOT NULL, 
                source VARCHAR(255) NOT NULL, 
                date DATE NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create budget table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget (
                id SERIAL PRIMARY KEY, 
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, 
                limit_amount DECIMAL(10, 2) NOT NULL, 
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        connection.commit()
        cursor.close()
        
        return DBConnection(connection)
        
    except Exception as e:
        print(f"Supabase Connection Error: {e}")
        return None

def close_connection(connection):
    if connection:
        connection.close()

def query_db(query, params=(), one=False):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params)
        
        # Commit for mutating queries
        if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE', 'CREATE']):
            conn.commit()
        
        # Fetch results safely
        if cursor.description: 
            rv = cursor.fetchall()
        else:
            rv = []
    except Exception as e:
        print(f"Database Query Error: {e}")
        rv = []
    finally:
        cursor.close()
        conn.close()
        
    return (rv[0] if rv else None) if one else rv
