---
# Spec: Backend Routes for Profile Page

## Overview
This feature replaces the hardcoded mockup data in the `/profile` route with real data fetched from the SQLite database. It allows users to see their actual profile information, spending statistics, category breakdowns, and transaction history based on their authenticated session.

## Depends on
- Step 03: Profile Page UI (The UI is already created, this step provides the data)
- Step 04: Login and Logout (Required for authentication)

## Routes
- `GET /profile` — Fetches user profile, statistics, category totals, and expense list for the logged-in user — logged-in

## Database changes
No database changes.

## Templates
- **Modify:** `templates/profile.html` — Ensure the template correctly renders the dynamic data passed from the route (though the UI is already built, the route logic needs to match the template's expected keys).

## Files to change
- `app.py` — Update the `/profile` route to query the database.

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
- Logged-in user can visit `/profile` and see their own name and email.
- The "Total Spent" stat displays the sum of all expenses for the current user.
- The "Total Transactions" stat displays the count of all expenses for the current user.
- The "Top Category" shows the category with the highest total spend.
- The category breakdown list shows the correct total and percentage for each category used by the user.
- The transactions table lists all expenses belonging to the user, ordered by date (descending).
- Unauthenticated users are redirected to the login page when attempting to access `/profile`.
---
