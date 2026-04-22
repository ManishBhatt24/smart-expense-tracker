import sqlite3
import os
from dotenv import load_dotenv

# Try to import optional drivers
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    mysql = None
    MySQLError = Exception

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

load_dotenv()

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

class SQLiteCursor:
    def __init__(self, cursor):
        self.cursor = cursor
    def execute(self, query, params=None):
        query = query.replace('%s', '?')
        # Compatibility for MySQL specific functions in SQLite
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

def get_db_connection():
    # 1. Try Vercel Postgres (PostgreSQL)
    if psycopg2 and os.getenv('POSTGRES_URL'):
        try:
            conn = psycopg2.connect(os.getenv('POSTGRES_URL'), sslmode='require')
            return DBConnection(conn, is_postgres=True)
        except Exception as e:
            print(f"Postgres Connection Error: {e}")

    # 2. Try MySQL
    if mysql:
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'smart_finance_db'),
                auth_plugin='mysql_native_password'
            )
            if connection.is_connected():
                return DBConnection(connection)
        except Exception:
            pass

    # 3. Fallback to SQLite
    return DBConnection(get_sqlite_conn_internal(), is_sqlite=True)

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

def query_db(query, params=(), one=False):
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    
    # Postgres specific date handling if needed (Postgres usually handles strftime like queries differently)
    # But since we use %s and standard SQL, it should work.
    
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
