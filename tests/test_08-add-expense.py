import pytest
from app import app as flask_app
from database.db import init_db
from database.queries import insert_expense

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })
    with flask_app.app_context():
        init_db()
        yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client, app):
    """A test client that is already logged in."""
    with app.app_context():
        from database.db import get_db
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Test User", "test@example.com", "hashed_pw")
            )
            conn.commit()
            user = cursor.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()
            user_id = user[0]

    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = "Test User"
    return client

class TestAddExpense:
    # --- Auth Guards ---

    def test_get_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert response.location == '/login' if 'location' in response.headers else '/login' in response.headers.get('Location', '')

    def test_post_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.post('/expenses/add', data={'amount': '10.0', 'category': 'Food', 'date': '2026-03-20'})
        assert response.status_code == 302
        assert '/login' in response.headers.get('Location', '')

    # --- GET Route ---

    def test_get_add_expense_authenticated_renders_form(self, auth_client):
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200

        # Check for form and method
        assert b'<form' in response.data
        assert b'method="POST"' in response.data

        # Check for all 7 fixed categories in the select dropdown
        categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
        for cat in categories:
            assert cat.encode() in response.data, f"Category {cat} missing from form"

    # --- POST Route: Happy Paths ---

    def test_post_add_expense_valid_data_redirects_and_saves(self, auth_client, app):
        # Get user_id from session
        with app.test_request_context():
            # We need to find the user_id of the 'test@example.com' created in auth_client
            from database.db import get_db
            db = get_db()
            user = db.execute('SELECT id FROM users WHERE email = ?', ('test@example.com',)).fetchone()
            user_id = user[0]

        payload = {
            'amount': '50.0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        }
        response = auth_client.post('/expenses/add', data=payload)

        # Redirect to profile
        assert response.status_code == 302
        assert '/profile' in response.headers.get('Location', '')

        # Verify DB side effect
        with app.app_context():
            from database.db import get_db
            db = get_db()
            row = db.execute(
                'SELECT amount, category, date, description FROM expenses WHERE user_id = ?',
                (user_id,)
            ).fetchone()
            assert row is not None
            assert float(row[0]) == 50.0
            assert row[1] == 'Food'
            assert row[2] == '2026-03-20'
            assert row[3] == 'Lunch'

    def test_post_add_expense_no_description_saves_as_null(self, auth_client, app):
        with app.test_request_context():
            from database.db import get_db
            db = get_db()
            user_id = db.execute('SELECT id FROM users WHERE email = ?', ('test@example.com',)).fetchone()[0]

        payload = {
            'amount': '20.0',
            'category': 'Transport',
            'date': '2026-03-21',
            'description': '' # Blank description
        }
        response = auth_client.post('/expenses/add', data=payload)

        assert response.status_code == 302
        assert '/profile' in response.headers.get('Location', '')

        with app.app_context():
            from database.db import get_db
            db = get_db()
            row = db.execute('SELECT description FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,)).fetchone()
            assert row[0] is None, "Description should be stored as NULL for blank input"

    # --- POST Route: Validation Errors ---

    @pytest.mark.parametrize("payload, error_snippet", [
        ({'amount': '', 'category': 'Food', 'date': '2026-03-20'}, b'amount'), # Missing amount
        ({'amount': '0', 'category': 'Food', 'date': '2026-03-20'}, b'positive'), # Zero amount
        ({'amount': '-10', 'category': 'Food', 'date': '2026-03-20'}, b'positive'), # Negative amount
        ({'amount': 'abc', 'category': 'Food', 'date': '2026-03-20'}, b'number'), # Non-numeric amount
        ({'amount': '10', 'category': 'InvalidCat', 'date': '2026-03-20'}, b'category'), # Invalid category
        ({'amount': '10', 'category': 'Food', 'date': 'invalid-date'}, b'date'), # Invalid date
        ({'amount': '10', 'category': 'Food', 'date': ''}, b'date'), # Missing date
    ])
    def test_post_add_expense_validation_errors(self, auth_client, payload, error_snippet):
        response = auth_client.post('/expenses/add', data=payload)

        assert response.status_code == 200 # Re-renders form
        assert error_snippet in response.data, f"Expected error containing {error_snippet} not found"

class TestInsertExpenseQuery:
    """Unit tests for the database helper function."""

    def test_insert_expense_success(self, app):
        with app.app_context():
            from database.db import get_db
            db = get_db()
            # Ensure a user exists
            db.execute('INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)', ('queryuser', 'query@example.com', 'pass'))
            db.commit()
            user_id = db.execute('SELECT id FROM users WHERE email = ?', ('query@example.com',)).fetchone()[0]

            # Use a unique amount for this specific test to avoid conflicts
            amount = 150.0
            insert_expense(user_id, amount, "Food", "2026-03-20", "Lunch")

            row = db.execute('SELECT amount, category, date, description FROM expenses WHERE user_id = ? AND amount = ?', (user_id, amount)).fetchone()
            assert row is not None
            assert row[0] == amount
            assert row[1] == "Food"
            assert row[2] == "2026-03-20"
            assert row[3] == "Lunch"

    def test_insert_expense_null_description(self, app):
        with app.app_context():
            from database.db import get_db
            db = get_db()
            db.execute('INSERT OR IGNORE INTO users (name, email, password_hash) VALUES (?, ?, ?)', ('queryuser2', 'query2@example.com', 'pass'))
            db.commit()
            user_id = db.execute('SELECT id FROM users WHERE email = ?', ('query2@example.com',)).fetchone()[0]

            # Use a unique amount for this specific test
            amount = 250.0
            insert_expense(user_id, amount, "Bills", "2026-03-21", None)

            row = db.execute('SELECT description FROM expenses WHERE user_id = ? AND amount = ?', (user_id, amount)).fetchone()
            assert row[0] is None
