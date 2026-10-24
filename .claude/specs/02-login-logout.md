---
# Spec: Login and Logout

## Overview
This feature implements the authentication flow for Spendly, allowing registered users to securely sign into their accounts and manage their sessions. It ensures that only authenticated users can access protected areas of the application, forming the foundation for user-specific expense tracking.

## Depends on
- Registration (Step 01)

## Routes
- `POST /login` — Authenticates user credentials and establishes a session — public
- `GET /logout` — Terminates the user session and redirects to landing — logged-in

## Database changes
No database changes.

## Templates
- **Modify:** `login.html` — update to include a form that posts to `/login`
- **Modify:** `base.html` — add conditional navigation links (Login/Register vs Logout/Profile) based on session state

## Files to change
- `app.py` — implement login/logout logic and session management
- `templates/login.html`
- `templates/base.html`

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use Flask `session` for state management

## Definition of done
- [ ] User can log in with valid email and password.
- [ ] User is redirected to a protected page (e.g., `/profile` or `/`) upon successful login.
- [ ] User sees an error message when providing invalid credentials.
- [ ] User can log out, which clears the session and redirects to the landing page.
- [ ] Navigation bar updates dynamically to show "Logout" when logged in and "Login" when logged out.
- [ ] Attempting to access `/logout` without being logged in redirects to `/login`.
---
