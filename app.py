from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, get_db
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "spendly_secret_key" # Required for flashing messages


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        # Basic email validation
        if "@" not in email or "." not in email:
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        # Password length check
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        hashed_pw = generate_password_hash(password)

        try:
            with get_db() as conn:
                conn.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, hashed_pw)
                )
                conn.commit()
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
            return render_template("register.html")

        flash("Account created successfully! Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template("login.html")

        try:
            with get_db() as conn:
                user = conn.execute(
                    "SELECT id, name, password_hash FROM users WHERE email = ?",
                    (email,)
                ).fetchone()

                if user and check_password_hash(user["password_hash"], password):
                    session["user_id"] = user["id"]
                    session["user_name"] = user["name"]
                    flash("Welcome back! 😊", "success")
                    return redirect(url_for("landing"))
                else:
                    flash("Invalid email or password.", "error")
        except sqlite3.Error as e:
            flash("An error occurred during login. Please try again.", "error")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    flash("See you soon! 🥺", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user_id = session["user_id"]

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. User Profile Data
        cursor.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user_row = cursor.fetchone()
        if not user_row:
            flash("User not found.", "error")
            return redirect(url_for("login"))

        # Formatting created_at (YYYY-MM-DD HH:MM:SS) to "Month Year"
        from datetime import datetime
        joined_date = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")

        user_data = {
            "name": user_row["name"],
            "email": user_row["email"],
            "joined": joined_date
        }

        # 2. Summary Statistics
        cursor.execute(
            "SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id = ?",
            (user_id,)
        )
        total_spent_val, transaction_count = cursor.fetchone()
        total_spent_float = total_spent_val if total_spent_val is not None else 0.0

        cursor.execute(
            "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,)
        )
        top_cat_row = cursor.fetchone()
        top_category = top_cat_row["category"] if top_cat_row else "N/A"

        stats = {
            "total_spent": f"₹{total_spent_float:,.2f}",
            "transactions": transaction_count if transaction_count else 0,
            "top_category": top_category
        }

        # 3. Category Breakdown
        cursor.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category",
            (user_id,)
        )
        category_rows = cursor.fetchall()

        categories = []
        if category_rows and total_spent_float > 0:
            for row in category_rows:
                cat_total = row["total"]
                categories.append({
                    "name": row["category"],
                    "amount": f"₹{cat_total:,.2f}",
                    "percentage": round((cat_total / total_spent_float) * 100, 1)
                })

        # 4. Transaction History
        cursor.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC",
            (user_id,)
        )
        transaction_rows = cursor.fetchall()

        transactions = [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": f"₹{row['amount']:,.2f}"
            }
            for row in transaction_rows
        ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats,
        transactions=transactions,
        categories=categories
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Logout — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
