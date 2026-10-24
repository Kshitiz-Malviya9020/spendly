from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, get_db
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

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

    # --- Date Filtering Logic ---
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    try:
        if date_from:
            datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            datetime.strptime(date_to, "%Y-%m-%d")

        if date_from and date_to and date_from > date_to:
            flash("Start date must be before end date.", "error")
            date_from, date_to = None, None
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", "error")
        date_from, date_to = None, None

    # Calculate preset dates for the template
    today = datetime.now().date()
    presets = {
        "this_month_start": today.replace(day=1).isoformat(),
        "this_month_end": today.isoformat(),
        "last_3_months_start": (today - timedelta(days=90)).isoformat(),
        "last_3_months_end": today.isoformat(),
        "last_6_months_start": (today - timedelta(days=180)).isoformat(),
        "last_6_months_end": today.isoformat(),
    }

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

        joined_date = datetime.strptime(user_row["created_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %Y")

        user_data = {
            "name": user_row["name"],
            "email": user_row["email"],
            "joined": joined_date
        }

    # Fetch data using query helpers
    from database.queries import get_summary_stats, get_category_breakdown, get_recent_transactions

    stats_data = get_summary_stats(user_id, date_from, date_to)
    categories_data = get_category_breakdown(user_id, date_from, date_to)
    transactions_data = get_recent_transactions(user_id, date_from, date_to)

    # Format data for the template
    stats = {
        "total_spent": f"₹{stats_data['total_spent']:,.2f}",
        "transactions": stats_data['transactions'],
        "top_category": stats_data['top_category']
    }

    categories = [
        {**cat, "amount": f"₹{cat['amount']:,.2f}"}
        for cat in categories_data
    ]

    transactions = [
        {**tx, "amount": f"₹{tx['amount']:,.2f}"}
        for tx in transactions_data
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats,
        transactions=transactions,
        categories=categories,
        presets=presets,
        date_from=date_from,
        date_to=date_to
    )


@app.route("/analytics")
def analytics():
    if not session.get("user_id"):
        return redirect(url_for("login"))
    return render_template("analytics.html")


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
