---
# Spec: Analytics (Coming Soon)

## Overview
This feature introduces the Analytics module to the Spendly expense tracker. At this stage, the goal is to establish the routing, navigation, and a "Coming Soon" landing page based on the provided Figma design, preparing the infrastructure for the full analytics dashboard.

## Depends on
- 02-registration
- 02-login-logout

## Routes
- `GET /analytics` — Render the Analytics "Coming Soon" page — logged-in

## Database changes
No database changes.

## Templates
- **Create:** `templates/analytics.html` (Converted from Figma design)
- **Modify:** `templates/base.html` (Add "Analytics" link to navbar, visible only to logged-in users, with active state handling)

## Files to change
- `app.py` (Add `/analytics` route with authentication check)
- `templates/base.html`

## Files to create
- `templates/analytics.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Match the Figma design exactly for the "Coming Soon" page
- Use existing session-based authentication in `app.py`

## Definition of done
- [ ] `/analytics` route renders the "Coming Soon" page.
- [ ] Logged-out users are redirected to `/login` when accessing `/analytics`.
- [ ] "Analytics" link is visible in the navbar only when a user is logged in.
- [ ] The "Analytics" navbar item is highlighted as active when viewing the page.
- [ ] The `analytics.html` template matches the provided Figma wireframe.
---
