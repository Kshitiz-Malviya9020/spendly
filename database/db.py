import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    with get_db() as conn:
        # Create users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)

        # Create expenses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()

def seed_db():
    """Inserts sample data for development, preventing duplication."""
    with get_db() as conn:
        # Check if users table already contains data
        user = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        if user:
            return

        # Insert demo user
        hashed_pw = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", hashed_pw)
        )
        user_id = cursor.lastrowid

        # Sample expenses across all categories
        # Categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other
        sample_expenses = [
            (user_id, 12.50, "Food", "2023-10-01", "Lunch at cafe"),
            (user_id, 45.00, "Food", "2023-10-02", "Grocery shopping"),
            (user_id, 20.00, "Transport", "2023-10-03", "Uber to office"),
            (user_id, 120.00, "Bills", "2023-10-04", "Electricity bill"),
            (user_id, 30.00, "Health", "2023-10-05", "Pharmacy"),
            (user_id, 50.00, "Entertainment", "2023-10-06", "Movie tickets"),
            (user_id, 80.00, "Shopping", "2023-10-07", "New t-shirt"),
            (user_id, 15.00, "Other", "2023-10-08", "Misc expense"),
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            sample_expenses
        )
        conn.commit()
