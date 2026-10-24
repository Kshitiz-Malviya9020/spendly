import pytest
from app import app, session
from database.db import init_db, get_db
from database.queries import insert_expense
from datetime import datetime

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_key'
    with app.test_client() as client:
        with app.app_context():
            init_db()
            # Create a test user
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    ("Test User", "test@example.com", "hashed_pw")
                )
                conn.commit()
                # Get the user_id whether it was just inserted or already existed
                user_row = cursor.execute(
                    "SELECT id FROM users WHERE email = ?",
                    ("test@example.com",)
                ).fetchone()
                user_id = user_row["id"]
        yield client, user_id

def test_insert_expense_valid(client):
    client_obj, user_id = client
    amount = 50.0
    category = "Food"
    date = "2026-03-20"
    description = "Lunch"

    insert_expense(user_id, amount, category, date, description)

    with get_db() as conn:
        row = conn.execute(
            "SELECT amount, category, date, description FROM expenses WHERE user_id = ? AND amount = ?",
            (user_id, amount)
        ).fetchone()
        assert row is not None
        assert row["category"] == category
        assert row["date"] == date
        assert row["description"] == description

def test_insert_expense_no_description(client):
    client_obj, user_id = client
    amount = 20.0
    category = "Transport"
    date = "2026-03-21"
    description = None

    insert_expense(user_id, amount, category, date, description)

    with get_db() as conn:
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ? AND amount = ?",
            (user_id, amount)
        ).fetchone()
        assert row["description"] is None

def test_add_expense_get_unauthenticated(client):
    client_obj, user_id = client
    response = client_obj.get("/expenses/add", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location

def test_add_expense_get_authenticated(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.get("/expenses/add")
    assert response.status_code == 200
    assert b"amount" in response.data
    assert b"category" in response.data
    assert b"date" in response.data
    assert b"Save Expense" in response.data

    # Check for all 7 categories
    for cat in ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]:
        assert cat.encode() in response.data

def test_add_expense_post_unauthenticated(client):
    client_obj, user_id = client
    response = client_obj.post("/expenses/add", data={
        "amount": "50.0",
        "category": "Food",
        "date": "2026-03-20",
        "description": "Lunch"
    }, follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location

def test_add_expense_post_authenticated_valid(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "50.0",
        "category": "Food",
        "date": "2026-03-20",
        "description": "Lunch"
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/profile" in response.location

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND amount = ?",
            (user_id, 50.0)
        ).fetchone()
        assert row is not None

def test_add_expense_post_authenticated_missing_amount(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "",
        "category": "Food",
        "date": "2026-03-20",
        "description": "Lunch"
    })

    assert response.status_code == 200
    assert b"Amount is required" in response.data

def test_add_expense_post_authenticated_zero_amount(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "0",
        "category": "Food",
        "date": "2026-03-20",
        "description": "Lunch"
    })

    assert response.status_code == 200
    assert b"Amount must be a positive number" in response.data

def test_add_expense_post_authenticated_invalid_amount(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "abc",
        "category": "Food",
        "date": "2026-03-20",
        "description": "Lunch"
    })

    assert response.status_code == 200
    assert b"Invalid amount format" in response.data

def test_add_expense_post_authenticated_invalid_category(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "50.0",
        "category": "InvalidCat",
        "date": "2026-03-20",
        "description": "Lunch"
    })

    assert response.status_code == 200
    assert b"Invalid category selected" in response.data

def test_add_expense_post_authenticated_invalid_date(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    response = client_obj.post("/expenses/add", data={
        "amount": "50.0",
        "category": "Food",
        "date": "not-a-date",
        "description": "Lunch"
    })

    assert response.status_code == 200
    assert b"Invalid date format" in response.data

def test_add_expense_post_authenticated_no_description(client):
    client_obj, user_id = client
    with client_obj.session_transaction() as sess:
        sess["user_id"] = user_id

    # Use a unique amount to avoid conflicts with previous tests
    amount = 99.99
    response = client_obj.post("/expenses/add", data={
        "amount": str(amount),
        "category": "Food",
        "date": "2026-03-20",
        "description": ""
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/profile" in response.location

    with get_db() as conn:
        row = conn.execute(
            "SELECT description FROM expenses WHERE user_id = ? AND amount = ?",
            (user_id, amount)
        ).fetchone()
        assert row["description"] is None
