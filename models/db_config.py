import mysql.connector
from mysql.connector import Error
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv('DB_TYPE', 'mysql') # Default to mysql, but will fallback

def get_db_connection():
    # Try MySQL first
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'smart_finance_db'),
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            return connection
    except Error:
        # Fallback to SQLite if MySQL fails
        return get_sqlite_connection()

class DBConnection:
    def __init__(self, conn, is_sqlite):
        self.conn = conn
        self.is_sqlite = is_sqlite
    def cursor(self, dictionary=False):
        cursor = self.conn.cursor()
        if self.is_sqlite:
            # SQLite uses row_factory for dictionaries
            return SQLiteCursor(cursor)
        else:
            # MySQL uses dictionary argument
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
        # For simplicity, we'll try to convert common ones
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
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'smart_finance_db'),
            auth_plugin='mysql_native_password'
        )
        if connection.is_connected():
            return DBConnection(connection, False)
    except Error:
        return DBConnection(get_sqlite_conn_internal(), True)

def get_sqlite_conn_internal():
    db_path = 'finance_tracker.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Initialize ... (same as before)
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    
    # Commit changes for non-SELECT queries
    if any(q in query.upper() for q in ['INSERT', 'UPDATE', 'DELETE']):
        conn.commit()
    
    # Try to fetch results (only for SELECT or queries that return rows)
    rv = []
    try:
        rv = cursor.fetchall()
    except:
        pass # Not a SELECT query

    cursor.close()
    conn.close()
    return (rv[0] if rv else None) if one else rv
