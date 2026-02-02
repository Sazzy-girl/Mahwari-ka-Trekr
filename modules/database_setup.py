import sqlite3
import os

DB_FILE = "data/mahwari.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            dob TEXT,
            password_hash TEXT,
            pin_hash TEXT,
            security_questions TEXT
        )
    ''')
    
    # Create Cycles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)
