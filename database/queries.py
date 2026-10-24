import sqlite3
from database.db import get_db

def get_summary_stats(user_id, date_from=None, date_to=None):
    """
    Returns total spent, transaction count, and top category for a user,
    optionally filtered by a date range.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Total Spent and Transaction Count
        query = "SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        cursor.execute(query, params)
        total_spent_val, transaction_count = cursor.fetchone()
        total_spent_float = total_spent_val if total_spent_val is not None else 0.0

        # 2. Top Category
        query_cat = "SELECT category FROM expenses WHERE user_id = ?"
        params_cat = [user_id]
        if date_from:
            query_cat += " AND date >= ?"
            params_cat.append(date_from)
        if date_to:
            query_cat += " AND date <= ?"
            params_cat.append(date_to)

        query_cat += " GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1"

        cursor.execute(query_cat, params_cat)
        top_cat_row = cursor.fetchone()
        top_category = top_cat_row["category"] if top_cat_row else "N/A"

        return {
            "total_spent": total_spent_float,
            "transactions": transaction_count if transaction_count else 0,
            "top_category": top_category
        }

def get_category_breakdown(user_id, date_from=None, date_to=None):
    """
    Returns a breakdown of spending by category, optionally filtered by date range.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        query += " GROUP BY category"

        cursor.execute(query, params)
        category_rows = cursor.fetchall()

        # Calculate total for percentages
        total_spent = sum(row["total"] for row in category_rows)

        categories = []
        if category_rows and total_spent > 0:
            for row in category_rows:
                cat_total = row["total"]
                categories.append({
                    "name": row["category"],
                    "amount": cat_total,
                    "percentage": round((cat_total / total_spent) * 100, 1)
                })
        return categories

def get_recent_transactions(user_id, date_from=None, date_to=None):
    """
    Returns transaction history for a user, optionally filtered by date range.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT date, description, category, amount FROM expenses WHERE user_id = ?"
        params = [user_id]
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)

        query += " ORDER BY date DESC"

        cursor.execute(query, params)
        transaction_rows = cursor.fetchall()

        return [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": row["amount"]
            }
            for row in transaction_rows
        ]

def insert_expense(user_id, amount, category, date, description):
    """
    Inserts a new expense into the database.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()
