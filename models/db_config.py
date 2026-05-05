import psycopg2
from psycopg2 import extras
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'postgres') 

def get_db_connection():
    # Try Supabase/Postgres first
    supabase_url = os.getenv('SUPABASE_DB_URL')
    if supabase_url:
        try:
            connection = psycopg2.connect(supabase_url)
            # Initialize tables for Postgres
            init_postgres_tables(connection)
            return DBConnection(connection, False, True)
        except Exception as e:
            print(f"Supabase connection failed: {e}")
            # If we are on Vercel, we can't use SQLite fallback easily
            if os.getenv('VERCEL'):
                raise e
    
    # Fallback to SQLite (local only)
    if not os.getenv('VERCEL'):
        try:
            return DBConnection(get_sqlite_conn_internal(), True, False)
        except Exception as e:
            print(f"SQLite fallback failed: {e}")
            return None
    return None

class DBConnection:
    def __init__(self, conn, is_sqlite, is_postgres=False):
        self.conn = conn
        self.is_sqlite = is_sqlite
        self.is_postgres = is_postgres

    def cursor(self, dictionary=True):
        if self.is_sqlite:
            return SQLiteCursor(self.conn.cursor())
        elif self.is_postgres:
            return self.conn.cursor(cursor_factory=extras.RealDictCursor)
        else:
            return self.conn.cursor(dictionary=dictionary)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

class SQLiteCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    def execute(self, query, params=None):
        query = query.replace('%s', '?')
        # Handle cases where MONTH() or DATE_FORMAT() are used (MySQL specific)
        query = query.replace("DATE_FORMAT(date, '%b %Y')", "strftime('%m %Y', date)")
        query = query.replace("MONTH(date) = MONTH(CURDATE())", "strftime('%m', date) = strftime('%m', 'now')")
        query = query.replace("DATE_SUB(CURDATE(), INTERVAL 6 MONTH)", "date('now', '-6 months')")
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

def init_postgres_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            amount NUMERIC,
            category TEXT,
            date TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            amount NUMERIC,
            source TEXT,
            date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            limit_amount NUMERIC,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()

def get_sqlite_conn_internal():
    db_path = 'finance_tracker.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT UNIQUE, password TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, category TEXT, date TEXT, description TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, source TEXT, date TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, limit_amount REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    return conn

def close_connection(connection):
    if connection:
        connection.close()

def query_db(query, params=(), one=False):
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE']):
            conn.commit()
        
        rv = []
        try:
            rv = cursor.fetchall()
        except:
            pass 

        return (rv[0] if rv else None) if one else rv
    finally:
        cursor.close()
        conn.close()
