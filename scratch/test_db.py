import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

try:
    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        auth_plugin='mysql_native_password'
    )
    if connection.is_connected():
        print("MySQL is accessible.")
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS smart_finance_db")
        print("Database checked/created.")
        connection.close()
except Error as e:
    print(f"MySQL connection failed: {e}")
