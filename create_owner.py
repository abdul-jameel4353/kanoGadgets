"""One-time owner-account bootstrap — CLI only, never a public web form.

Usage:
    python3 create_owner.py --email you@kanoplug.com --name "Owner Name"
"""
import os, sys, getpass, secrets, random
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import models

DEFAULT_CATEGORIES = [
    ("Smartphones", "phones", "Phones from budget to flagship", "📱"),
    ("Laptops & Computers", "laptops", "Laptops, desktops and all-in-ones", "💻"),
    ("Headphones & Earbuds", "audio-head", "Over-ear, in-ear and wireless buds", "🎧"),
    ("Smartwatches", "watches", "Fitness and smart timepieces", "⌚"),
    ("Gaming Accessories", "gaming", "Consoles, pads, VR and gear", "🎮"),
    ("Chargers & Cables", "power", "Fast chargers, cables and power banks", "🔌"),
    ("Tablets", "tablets", "Android and iPad-class tablets", "🟦"),
    ("Computer Accessories", "pc-acc", "Keyboards, mice, storage and more", "🖱️"),
    ("Speakers & Audio", "audio-spk", "Bluetooth speakers, soundbars, DJ gear", "🔊"),
    ("Other Gadgets", "other", "Everything else in the gadget center", "📦"),
]

def seed_categories(d):
    existing = [r[0] for r in d.execute("SELECT slug FROM categories")]
    for name, slug, desc, icon in DEFAULT_CATEGORIES:
        if slug not in existing:
            d.execute("INSERT INTO categories(name,slug,description,icon,active) VALUES(?,?,?,?,1)", (name, slug, desc, icon))
    return len(existing) == 0

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    pw1 = getpass.getpass("Owner password (min 10 chars): ")
    if len(pw1) < 10:
        print("✗ password too short"); sys.exit(1)
    pw2 = getpass.getpass("Confirm password: ")
    if pw1 != pw2:
        print("✗ passwords do not match"); sys.exit(1)
    d = models.init_db()
    seed_categories(d)
    h = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt(rounds=12)).decode()
    try:
        cur = d.execute(
            "INSERT INTO users(email,hash,name,role,status) VALUES(?,?,?,'owner','active')",
            (a.email.strip().lower(), h, a.name.strip()))
        oid = cur.lastrowid
        d.execute("INSERT INTO admin_activity(actor_id,actor_name,action) VALUES(?,?,?)",
                  (oid, a.name, f"Owner account created (CLI bootstrap)"))
        d.commit()
        print(f"✓ Owner account created for {a.email}  ·  role=owner")
    except models.sqlite3.IntegrityError:
        print("✗ that email already has an account — owner must be unique")
        sys.exit(1)
    finally:
        d.close()

if __name__ == "__main__":
    main()
