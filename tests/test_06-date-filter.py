import pytest
from app import app as flask_app
from database.db import init_db
from datetime import datetime, timedelta

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': ':memory:',
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
def auth_client(client):
    """A test client that is already registered and logged in."""
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })
    return client

def insert_expense(client, user_id, amount, category, date, description="Test"):
    """Helper to insert expenses into the DB."""
    from database.db import get_db
    with get_db() as conn:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
        conn.commit()

class TestDateFilter:

    def test_profile_auth_guard(self, client):
        """Ensure /profile redirects unauthenticated users to login."""
        response = client.get('/profile')
        assert response.status_code == 302
        assert '/login' in response.location

    def test_custom_date_range_filtering(self, auth_client):
        """Verify a valid custom date range filters all sections correctly."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        # Data: 1 in range, 1 out of range
        insert_expense(auth_client, user_id, 100.0, "Food", "2023-01-15")
        insert_expense(auth_client, user_id, 200.0, "Rent", "2023-02-15")

        # Filter for January
        response = auth_client.get('/profile?date_from=2023-01-01&date_to=2023-01-31')

        assert response.status_code == 200
        assert "₹100.00".encode('utf-8') in response.data
        assert b'1' in response.data # transaction count
        assert b'Food' in response.data
        assert b'Rent' not in response.data
        assert b'2023-01-15' in response.data
        assert b'2023-02-15' not in response.data

    def test_preset_this_month(self, auth_client):
        """Verify 'This Month' preset filters data to current month."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        today = datetime.now()
        this_month_date = today.replace(day=1).strftime("%Y-%m-%d")
        last_month_date = (today - timedelta(days=40)).strftime("%Y-%m-%d")

        insert_expense(auth_client, user_id, 50.0, "Food", this_month_date)
        insert_expense(auth_client, user_id, 100.0, "Food", last_month_date)

        # Simulate the logic app.py uses for this month
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        response = auth_client.get(f'/profile?date_from={start_date}&date_to={end_date}')

        assert '₹50.00'.encode('utf-8') in response.data
        assert b'1' in response.data
        assert '₹150.00'.encode('utf-8') not in response.data

    def test_preset_last_3_months(self, auth_client):
        """Verify 'Last 3 Months' (90 days) filtering."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        today = datetime.now()
        within_range = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        out_of_range = (today - timedelta(days=100)).strftime("%Y-%m-%d")

        insert_expense(auth_client, user_id, 50.0, "Food", within_range)
        insert_expense(auth_client, user_id, 100.0, "Food", out_of_range)

        start_date = (today - timedelta(days=90)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        response = auth_client.get(f'/profile?date_from={start_date}&date_to={end_date}')

        assert '₹50.00'.encode('utf-8') in response.data
        assert b'1' in response.data
        assert '₹150.00'.encode('utf-8') not in response.data

    def test_preset_last_6_months(self, auth_client):
        """Verify 'Last 6 Months' (180 days) filtering."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        today = datetime.now()
        within_range = (today - timedelta(days=150)).strftime("%Y-%m-%d")
        out_of_range = (today - timedelta(days=200)).strftime("%Y-%m-%d")

        insert_expense(auth_client, user_id, 50.0, "Food", within_range)
        insert_expense(auth_client, user_id, 100.0, "Food", out_of_range)

        start_date = (today - timedelta(days=180)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        response = auth_client.get(f'/profile?date_from={start_date}&date_to={end_date}')

        assert '₹50.00'.encode('utf-8') in response.data
        assert b'1' in response.data
        assert '₹150.00'.encode('utf-8') not in response.data

    def test_all_time_view(self, auth_client):
        """Verify that no params or an explicit clean URL shows all expenses."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        insert_expense(auth_client, user_id, 100.0, "Food", "2020-01-01")
        insert_expense(auth_client, user_id, 200.0, "Rent", "2023-01-01")

        response = auth_client.get('/profile')

        assert '₹300.00'.encode('utf-8') in response.data
        assert b'2' in response.data

    def test_invalid_date_range_order(self, auth_client):
        """Verify that date_from > date_to flashes error and shows unfiltered view."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        insert_expense(auth_client, user_id, 100.0, "Food", "2023-01-01")

        # date_from is after date_to
        response = auth_client.get('/profile?date_from=2023-12-31&date_to=2023-01-01')

        assert b'Start date must be before end date.' in response.data
        assert '₹100.00'.encode('utf-8') in response.data # Should fall back to unfiltered

    def test_malformed_date_input(self, auth_client):
        """Verify that invalid date strings fall back to unfiltered view."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        insert_expense(auth_client, user_id, 100.0, "Food", "2023-01-01")

        response = auth_client.get('/profile?date_from=not-a-date&date_to=2023-12-31')

        assert response.status_code == 200
        assert '₹100.00'.encode('utf-8') in response.data # Fallback to all time

    def test_empty_results_for_range(self, auth_client):
        """Verify range with no expenses shows ₹0.00 and empty lists."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        insert_expense(auth_client, user_id, 100.0, "Food", "2023-01-01")

        # Range where no data exists
        response = auth_client.get('/profile?date_from=2024-01-01&date_to=2024-01-31')

        assert '₹0.00'.encode('utf-8') in response.data
        assert b'0' in response.data
        assert b'Food' not in response.data

    def test_category_percentage_recalculation(self, auth_client):
        """Verify category percentages are based only on the filtered amount."""
        from database.db import get_db
        with get_db() as conn:
            user_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()[0]

        # Total: 300. Range total: 100
        insert_expense(auth_client, user_id, 50.0, "Food", "2023-01-10")
        insert_expense(auth_client, user_id, 50.0, "Transport", "2023-01-11")
        insert_expense(auth_client, user_id, 200.0, "Rent", "2023-02-01")

        response = auth_client.get('/profile?date_from=2023-01-01&date_to=2023-01-31')

        # For January: 50 Food, 50 Transport. Total 100. Each should be 50.0%
        assert b'50.0%' in response.data
        assert b'Rent' not in response.data
