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

    # Hardcoded data for UI mockup as per Spec Step 03
    user_data = {
        "name": "Kshitiz Malviya",
        "email": "kshitiz@example.com",
        "joined": "October 2023"
    }

    stats = {
        "total_spent": "₹12,450.00",
        "transactions": 42,
        "top_category": "Food"
    }

    transactions = [
        {"date": "2023-10-24", "description": "Starbucks Coffee", "category": "Food", "amount": "₹350.00"},
        {"date": "2023-10-23", "description": "Uber Ride", "category": "Transport", "amount": "₹120.00"},
        {"date": "2023-10-22", "description": "Grocery Store", "category": "Food", "amount": "₹1,200.00"},
        {"date": "2023-10-21", "description": "Netflix Monthly", "category": "Entertainment", "amount": "₹499.00"},
    ]

    categories = [
        {"name": "Food", "amount": "₹5,200", "percentage": 42},
        {"name": "Transport", "amount": "₹2,100", "percentage": 17},
        {"name": "Bills", "amount": "₹3,000", "percentage": 24},
        {"name": "Entertainment", "amount": "₹1,150", "percentage": 9},
        {"name": "Other", "amount": "₹1,000", "percentage": 8},
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
