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
            mobile_number TEXT,
            dob TEXT,
            password_hash TEXT,
            pin_hash TEXT,
            security_questions TEXT,
            hue INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            user_id TEXT
        )
    ''')
    
    # Create Cycles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            start_date TEXT,
            end_date TEXT,
            duration INTEGER DEFAULT 28,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Migration for existing DB
    migrate_db()

def migrate_db():
    conn = get_connection()
    c = conn.cursor()
    # Migrations
    cols = [
        ("users", "hue", "INTEGER DEFAULT 0"),
        ("users", "language", "TEXT DEFAULT 'en'"),
        ("users", "user_id", "TEXT"),
        ("cycles", "duration", "INTEGER DEFAULT 28")
    ]
    
    for table, col, dtype in cols:
        try:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")
            conn.commit()
        except sqlite3.OperationalError:
            pass # Column likely exists
    
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)
