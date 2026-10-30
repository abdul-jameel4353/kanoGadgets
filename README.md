# KanoPlug.com

A complete gadget marketplace for Kano State, Nigeria — public site + private seller dashboard + owner admin,
with real SQLite persistence, bcrypt auth, and role-enforced server-side access control.

## Features
- Public marketplace: browse, search, filter, categories, product details, public seller profiles
- Direct WhatsApp contact (`wa.me` links) — no checkout, no integrated payment
- Seller self-registration (full name, email, WhatsApp phone, public username, reason) — instant access, no approval queue
- Seller dashboard: products, profile, publish instantly; edit/delete own listings only
- Admin: seller list with suspend/reinstate, moderate listings, categories, reports
- Report system (visitor-facing, no account required) with admin resolution
- Product moderation log and admin activity audit
- Mobile-first responsive; navy + electric blue brand; green WhatsApp CTA; red moderation; amber pending

## Run

```bash
pip install -r requirements.txt
export KG_SECRET_KEY="pick-a-long-random-secret"
# 1. create the owner account ONCE (never a public signup form)
python3 create_owner.py --email you@kanoplug.com --name "Owner Name"
# 2. start
python3 run.py        # → http://localhost:5000
```

The first run seeds 10 starter categories and opens. Sign in as the owner, open `/admin`, and review applications.

## Roles

| Role | Can do |
|---|---|
| Visitor | browse, search, view products/sellers, submit a report |
| Seller | self-registers, publish instantly, edit/delete own listings, manage shop profile |
| Admin | moderate listings, manage categories, review applications |
| Owner | everything, including seller suspension/removal |

## Privacy & safety
- Passport files live in `data/private/` (not served at a URL, fetchable only behind admin auth)
- Bcrypt (12 rounds) for passwords; sessions are HttpOnly/SameSite=Lax
- `SECRET_KEY` must be set via `KG_SECRET_KEY` in production; the dev fallback is not for real use
