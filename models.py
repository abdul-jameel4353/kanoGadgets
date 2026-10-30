"""KanoGadgets.com — models & SQLite schema."""
import os, sqlite3
from contextlib import contextmanager

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB = os.path.join(DATA, "kanogadgets.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  username TEXT,                               -- public handle, chosen at signup (sellers)
  hash TEXT NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  role TEXT NOT NULL DEFAULT 'seller',         -- owner | admin | seller | applicant(legacy)
  status TEXT NOT NULL DEFAULT 'active',       -- active | suspended | pending | rejected
  join_reason TEXT,                            -- why they joined (stored at signup)
  application_id INTEGER,                      -- legacy
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS seller_applications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  full_name TEXT NOT NULL,
  email TEXT NOT NULL,
  phone TEXT NOT NULL,
  shop_name TEXT NOT NULL,
  shop_location TEXT NOT NULL,
  shop_address TEXT,
  reason TEXT NOT NULL,
  passport_photo TEXT NOT NULL,
  rules_accepted INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  reviewer_id INTEGER,
  decided_at TEXT,
  rejection_reason TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS seller_profiles(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  display_name TEXT NOT NULL,
  shop_name TEXT NOT NULL,
  shop_description TEXT DEFAULT '',
  location TEXT NOT NULL,
  whatsapp TEXT NOT NULL,
  contact_email TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS categories(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  description TEXT,
  image TEXT,
  icon TEXT DEFAULT '📦',
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS products(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  seller_id INTEGER NOT NULL REFERENCES seller_profiles(id),
  category_id INTEGER REFERENCES categories(id),
  name TEXT NOT NULL,
  brand TEXT,
  model TEXT,
  price INTEGER NOT NULL,
  currency TEXT DEFAULT 'NGN',
  condition TEXT NOT NULL DEFAULT 'New',
  description TEXT,
  location TEXT,
  whatsapp TEXT,
  availability TEXT DEFAULT 'In stock',
  status TEXT NOT NULL DEFAULT 'draft',
  moderation_note TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS product_images(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  file TEXT NOT NULL,
  sort INTEGER DEFAULT 0,
  is_main INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  product_id INTEGER NOT NULL REFERENCES products(id),
  reporter_email TEXT,
  reason TEXT NOT NULL,
  details TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  reviewer_id INTEGER,
  resolved_at TEXT,
  resolution_note TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS moderation_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER,
  target_type TEXT NOT NULL,
  target_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  reason TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS admin_activity(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  actor_id INTEGER,
  actor_name TEXT,
  action TEXT NOT NULL,
  meta TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_products_status ON products(status);
CREATE INDEX IF NOT EXISTS ix_products_seller ON products(seller_id);
CREATE INDEX IF NOT EXISTS ix_products_category ON products(category_id);
"""

def get_db():
    db = sqlite3.connect(DB, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

@contextmanager
def db():
    d = get_db()
    try:
        yield d
        d.commit()
    except Exception:
        d.rollback()
        raise
    finally:
        d.close()

def init_db():
    os.makedirs(DATA, exist_ok=True)
    d = get_db()
    d.executescript(SCHEMA)
    # lightweight migrations for existing databases
    for col, ddl in [("username", "ALTER TABLE users ADD COLUMN username TEXT"),
                     ("join_reason", "ALTER TABLE users ADD COLUMN join_reason TEXT")]:
        try:
            d.execute(f"SELECT {col} FROM users LIMIT 1")
        except sqlite3.OperationalError:
            d.execute(ddl)
    d.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_username ON users(username COLLATE NOCASE) WHERE username IS NOT NULL")
    d.commit()
    return d

def q(sql, params=()):
    d = get_db()
    try:
        return d.execute(sql, params).fetchall()
    finally:
        d.close()

def one(sql, params=()):
    d = get_db()
    try:
        return d.execute(sql, params).fetchone()
    finally:
        d.close()
