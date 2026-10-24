import pytest
from app import app as flask_app
from database.db import init_db

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
    """A test client that is already logged in."""
    # We use a single client instance to ensure cookies are maintained.
    with client.session_transaction() as sess:
        # We need a user in the DB to be technically correct,
        # but for session-based auth tests, injecting the session
        # is the most reliable way to isolate the route logic.
        sess['user_id'] = 1
        sess['user_name'] = 'Test User'
    return client

class TestAnalyticsComingSoon:

    def test_analytics_unauthenticated_redirects_to_login(self, client):
        """Logged-out users accessing /analytics should be redirected to /login."""
        response = client.get('/analytics')
        assert response.status_code == 302
        assert response.location.endswith('/login')

    def test_analytics_authenticated_access_success(self, auth_client):
        """Logged-in users accessing /analytics should see the page."""
        response = auth_client.get('/analytics')
        assert response.status_code == 200
        assert b'Analytics Dashboard' in response.data
        assert b'Coming Soon' in response.data

    def test_navbar_analytics_link_visibility_logged_out(self, client):
        """The 'Analytics' link should be hidden when logged out."""
        response = client.get('/')
        assert b'Analytics' not in response.data

    def test_navbar_analytics_link_visibility_logged_in(self, auth_client):
        """The 'Analytics' link should be visible when logged in."""
        response = auth_client.get('/')
        assert b'Analytics' in response.data

    def test_navbar_active_state_on_analytics_page(self, auth_client):
        """The 'Analytics' link should have the 'active' class when on the /analytics page."""
        response = auth_client.get('/analytics')
        assert b'active' in response.data
        assert b'Analytics' in response.data

    def test_navbar_active_state_on_profile_page(self, auth_client):
        """The 'Profile' link should have the 'active' class when on the /profile page."""
        response = auth_client.get('/profile')
        assert b'Profile' in response.data
        assert b'active' in response.data
