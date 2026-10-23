# Spec: Registration

## Overview
This feature implements the user registration process, allowing new users to create an account by providing their name, email, and password. This is a critical early step in the Spendly roadmap to enable personalized expense tracking and secure data storage for each user.

## Depends on
- Database setup (Step 01)

## Routes
- `GET /register` — Display registration form — public
- `POST /register` — Handle registration form submission — public

## Database changes
No database changes (the `users` table already exists with necessary columns: `name`, `email`, `password_hash`).

## Templates
- **Create:** `templates/register.html` (already exists as a placeholder, but needs implementation)
- **Modify:** `templates/base.html` (to ensure navigation links to register/login are present)

## Files to change
- `app.py` — Implement the `POST /register` logic and update the `register` route.

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

## Definition of done
- User can navigate to `/register`.
- User can submit the registration form with valid data.
- A new user is successfully created in the `users` table with a hashed password.
- Duplicate email registration is handled gracefully (shows an error message).
- Invalid inputs (empty fields) are handled gracefully.
- Upon successful registration, the user is redirected to the login page or dashboard.
