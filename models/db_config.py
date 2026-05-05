import os
import sqlite3
import mysql.connector
from mysql.connector import Error
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
from dotenv import load_dotenv

load_dotenv()

class SQLiteCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    def execute(self, query, params=None):
        query = query.replace('%s', '?')
        # Handle MySQL/Postgres specific date functions in SQLite fallback
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

class DBConnection:
    def __init__(self, conn, is_sqlite=False, is_postgres=False):
        self.conn = conn
        self.is_sqlite = is_sqlite
        self.is_postgres = is_postgres
    def cursor(self, dictionary=True):
        if self.is_sqlite:
            return SQLiteCursor(self.conn.cursor())
        elif self.is_postgres:
            return self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            return self.conn.cursor(dictionary=dictionary)
    def commit(self):
        self.conn.commit()
    def close(self):
        self.conn.close()

def init_db(conn_obj):
    """Creates tables if they don't exist, handling syntax for different DBs."""
    cursor = conn_obj.cursor()
    
    # Base types
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if conn_obj.is_sqlite else \
              ("SERIAL PRIMARY KEY" if conn_obj.is_postgres else "INT AUTO_INCREMENT PRIMARY KEY")
    text_type = "TEXT" if (conn_obj.is_sqlite or conn_obj.is_postgres) else "TEXT"
    real_type = "REAL" if conn_obj.is_sqlite else "DECIMAL(10,2)"
    ts_default = "CURRENT_TIMESTAMP"
    
    tables = [
        f"CREATE TABLE IF NOT EXISTS users (id {id_type}, name {text_type}, email VARCHAR(255) UNIQUE, password {text_type}, created_at TIMESTAMP DEFAULT {ts_default})",
        f"CREATE TABLE IF NOT EXISTS expenses (id {id_type}, user_id INTEGER, amount {real_type}, category VARCHAR(100), date VARCHAR(20), description {text_type}, created_at TIMESTAMP DEFAULT {ts_default})",
        f"CREATE TABLE IF NOT EXISTS income (id {id_type}, user_id INTEGER, amount {real_type}, source VARCHAR(100), date VARCHAR(20), created_at TIMESTAMP DEFAULT {ts_default})",
        f"CREATE TABLE IF NOT EXISTS budget (id {id_type}, user_id INTEGER, limit_amount {real_type}, created_at TIMESTAMP DEFAULT {ts_default})"
    ]
    
    for table in tables:
        cursor.execute(table)
    
    conn_obj.commit()
    cursor.close()

def get_db_connection():
    # 1. Try PostgreSQL (Supabase)
    pg_url = os.getenv('SUPABASE_DB_URL')
    if pg_url and psycopg2:
        try:
            connection = psycopg2.connect(pg_url)
            conn_obj = DBConnection(connection, is_postgres=True)
            init_db(conn_obj)
            return conn_obj
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")

    # 2. Try MySQL
    if os.getenv('DB_HOST'):
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'smart_finance_db'),
                auth_plugin='mysql_native_password'
            )
            if connection.is_connected():
                conn_obj = DBConnection(connection)
                init_db(conn_obj)
                return conn_obj
        except Error:
            pass

    # 3. Fallback to SQLite
    conn_obj = DBConnection(get_sqlite_conn_internal(), is_sqlite=True)
    init_db(conn_obj)
    return conn_obj

def get_sqlite_conn_internal():
    db_path = 'finance_tracker.db'
    if os.getenv('VERCEL'):
        db_path = '/tmp/finance_tracker.db'
    
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def close_connection(connection):
    if connection:
        connection.close()

def query_db(query, params=(), one=False):
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE']):
        conn.commit()
    
    rv = []
    try:
        rv = cursor.fetchall()
    except:
        pass

    cursor.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv
