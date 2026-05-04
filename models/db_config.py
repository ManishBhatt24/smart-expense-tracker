import psycopg2
from psycopg2.extras import DictCursor
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DBConnection:
    def __init__(self, conn, is_sqlite):
        self.conn = conn
        self.is_sqlite = is_sqlite
    
    def cursor(self, dictionary=True):
        if self.is_sqlite:
            cursor = self.conn.cursor()
            return SQLiteCursor(cursor)
        else:
            if dictionary:
                return self.conn.cursor(cursor_factory=DictCursor)
            else:
                return self.conn.cursor()
    
    def commit(self):
        self.conn.commit()
    
    def close(self):
        self.conn.close()

class SQLiteCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    
    def execute(self, query, params=None):
        query = query.replace('%s', '?')
        # Handle PostgreSQL/MySQL specific functions for SQLite fallback
        query = query.replace("DATE_FORMAT(date, '%b %Y')", "strftime('%m %Y', date)")
        query = query.replace("MONTH(date) = MONTH(CURRENT_DATE)", "strftime('%m', date) = strftime('%m', 'now')")
        query = query.replace("MONTH(date) = MONTH(CURDATE())", "strftime('%m', date) = strftime('%m', 'now')")
        return self.cursor.execute(query, params or ())
    
    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def fetchall(self):
        return [dict(row) for row in self.cursor.fetchall()]
    
    def close(self):
        self.cursor.close()

    @property
    def description(self):
        return self.cursor.description

def get_db_connection():
    # Try PostgreSQL (Supabase) first
    database_url = os.getenv('DATABASE_URL')
    host = os.getenv('DB_HOST')
    
    if database_url or host:
        try:
            if database_url:
                connection = psycopg2.connect(database_url)
            else:
                connection = psycopg2.connect(
                    host=host,
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', ''),
                    database=os.getenv('DB_NAME', 'postgres'),
                    port=int(os.getenv('DB_PORT', 5432))
                )
            # Ensure tables exist in Postgres
            cursor = connection.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(255), email VARCHAR(255) UNIQUE, password TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cursor.execute("CREATE TABLE IF NOT EXISTS expenses (id SERIAL PRIMARY KEY, user_id INTEGER, amount DECIMAL, category VARCHAR(255), date DATE, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cursor.execute("CREATE TABLE IF NOT EXISTS income (id SERIAL PRIMARY KEY, user_id INTEGER, amount DECIMAL, source VARCHAR(255), date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            cursor.execute("CREATE TABLE IF NOT EXISTS budget (id SERIAL PRIMARY KEY, user_id INTEGER, limit_amount DECIMAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            connection.commit()
            cursor.close()
            
            return DBConnection(connection, False)
        except Exception as e:
            print(f"PostgreSQL/Supabase Connection Error: {e}")
    
    # Fallback to SQLite
    db_path = 'finance_tracker.db'
    if os.getenv('VERCEL'):
        db_path = '/tmp/finance_tracker.db'
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Auto-initialize SQLite
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, category TEXT, date TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, source TEXT, date TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, limit_amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    
    return DBConnection(conn, True)

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
        if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE', 'CREATE']):
            conn.commit()
        
        # Postgres returns tuples/lists even with DictCursor if there are no results or it's a mutation, 
        # but DictCursor fetchall() returns dict-like objects.
        if cursor.description: # If there are results to fetch
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
