"""KanoGadgets.com — public marketplace + seller dashboard + owner admin.

Stack: Flask + SQLite + bcrypt. Every protected route is enforced server-side.
No external auth keys are required for the core; a real SMS/Google sign-in would
replace the local password login when keys are supplied.
"""
import os, re, uuid, sqlite3, unicodedata, urllib.parse, datetime
from functools import wraps

from flask import (Flask, request, session, redirect, url_for,
                   render_template, abort, send_from_directory, flash, g)
import bcrypt

import models

BASE = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, instance_relative_config=False)
app.config.update(
    SECRET_KEY=os.environ.get("KG_SECRET_KEY") or os.environ.get("SECRET_KEY", "dev-secret-change-in-production"),
    UPLOAD_FOLDER=os.path.join(BASE, "static", "uploads"),
    PRIVATE_FOLDER=os.path.join(BASE, "data", "private"),           # passport photos — never public
    MAX_CONTENT_LENGTH=12 * 1024 * 1024,                            # 12 MB request cap
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(days=2),
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["PRIVATE_FOLDER"], exist_ok=True)

img_exts = {".jpg", ".jpeg", ".png", ".webp"}
passport_exts = img_exts.copy()


# ------------------------------------------------------------------ helpers
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return models.one("SELECT * FROM users WHERE id=?", (uid,))


def requires(role=None, roles=None):
    """Enforce auth + role on the server. Never trust frontend-only role info."""
    allowed = {role} if role else set(roles or [])
    def deco(fn):
        @wraps(fn)
        def wrap(*a, **k):
            u = current_user()
            if not u:
                if request.path.startswith("/api/") or request.is_json:
                    return {"ok": False, "error": "auth_required"}, 401
                return redirect(url_for("login", next=request.path))
            if u["status"] == "suspended":
                session.clear()
                flash("Your account has been suspended. Contact the marketplace owner.", "err")
                return redirect(url_for("login"))
            if allowed and u["role"] not in allowed:
                abort(403, f"Access denied — required: {', '.join(sorted(allowed))}, your role: {u['role']}")
            g.user = u
            return fn(*a, **k)
        return wrap
    return deco


requires_seller = requires(role="seller")
requires_admin = requires(roles=["owner", "admin"])


def slugify(text):
    s = unicodedata.normalize("NFKD", text.lower())
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "item"


def norm_phone(raw):
    """Normalise a Nigerian number to WhatsApp international digits (2348…)."""
    if not raw:
        return None
    d = re.sub(r"\D", "", raw)
    if d.startswith("00"):
        d = d.lstrip("0")
    if d.startswith("0"):
        d = "234" + d[1:]
    if d.startswith("234") and len(d) == 13:
        return d
    if len(d) == 10 and d.startswith(("7", "8", "9")):
        return "234" + d
    return d if 11 <= len(d) <= 15 else None


def wa_link(number, text=""):
    d = re.sub(r"\D", "", number or "")
    if not (11 <= len(d) <= 15):
        return None
    return f"https://wa.me/{d}" + (f"?text={urllib.parse.quote(text)}" if text else "")


def money(n):
    try:
        return f"₦{int(float(n)):,}"
    except Exception:
        return "₦—"


def save_image(fs, extset, folder=None, max_bytes=8 * 1024 * 1024):
    if not fs or not fs.filename:
        return None
    ext = os.path.splitext(fs.filename)[1].lower()
    if ext not in extset:
        return None
    data = fs.read(max_bytes + 1)
    if len(data) > max_bytes:
        return None
    folder = folder or app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    out = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(folder, out), "wb") as fh:
        fh.write(data)
    return out


def now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds")


def exec_db(sql, params=()):
    d = models.get_db()
    cur = d.execute(sql, params)
    d.commit(); d.close()
    return cur


# ------------------------------------------------------------------ public marketplace
@app.route("/")
def index():
    cats = models.q("SELECT * FROM categories WHERE active=1 ORDER BY name LIMIT 12")
    featured = models.q("""
        SELECT p.*, sp.shop_name, sp.location AS shop_location,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p
        JOIN seller_profiles sp ON sp.id=p.seller_id
        JOIN users u ON u.id=sp.user_id
        WHERE p.status='published' AND u.status='active'
        ORDER BY p.created_at DESC LIMIT 8""")
    return render_template("public/home.html", cats=cats, featured=featured, money=money)


@app.route("/browse")
def browse():
    search = request.args.get("q", "").strip()
    cat_id = request.args.get("cat", type=int)
    cond = request.args.get("cond", "")
    minp = request.args.get("min", type=int)
    maxp = request.args.get("max", type=int)
    sort = request.args.get("sort", "latest")

    sql = """
        SELECT p.*, sp.shop_name, sp.location AS shop_location,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p
        JOIN seller_profiles sp ON sp.id=p.seller_id
        JOIN users u ON u.id=sp.user_id
        WHERE p.status='published' AND u.status='active'"""
    conds, params = [], []
    if search:
        like = f"%{search}%"
        conds.append("(p.name LIKE ? OR p.brand LIKE ? OR p.model LIKE ? OR p.description LIKE ?)")
        params += [like, like, like, like]
    if cat_id:
        conds.append("p.category_id=?"); params.append(cat_id)
    if cond in ("New", "Used"):
        conds.append("p.condition=?"); params.append(cond)
    if minp is not None or maxp is not None:
        conds.append("p.price BETWEEN ? AND ?")
        params += [minp or 0, maxp if maxp else 2147483647]
    if conds:
        sql += " AND " + " AND ".join(conds)
    sql += {"latest": " ORDER BY p.created_at DESC",
            "price_asc": " ORDER BY p.price ASC",
            "price_desc": " ORDER BY p.price DESC"}.get(sort, " ORDER BY p.created_at DESC")
    sql += " LIMIT 120"

    products = models.q(sql, params)
    cats = models.q("SELECT id,name FROM categories WHERE active=1 ORDER BY name")
    return render_template("public/browse.html", products=products, cats=cats,
                           money=money, search=search, sel_cond=cond, sel_sort=sort,
                           sel_cat=cat_id, sel_min=minp, sel_max=maxp)


@app.route("/search")
def search():
    return browse()


@app.route("/categories")
def categories_page():
    cats = models.q("SELECT * FROM categories WHERE active=1 ORDER BY name")
    return render_template("public/categories.html", cats=cats)


@app.route("/category/<slug>")
def category_page(slug):
    cat = models.one("SELECT * FROM categories WHERE slug=? AND active=1", (slug,))
    if not cat:
        abort(404)
    products = models.q("""
        SELECT p.*, sp.shop_name, sp.location AS shop_location,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p JOIN seller_profiles sp ON sp.id=p.seller_id JOIN users u ON u.id=sp.user_id
        WHERE p.category_id=? AND p.status='published' AND u.status='active'
        ORDER BY p.created_at DESC""", (cat["id"],))
    return render_template("public/category.html", cat=cat, products=products, money=money)


@app.route("/product/<int:pid>")
def product_page(pid):
    p = models.one("""
        SELECT p.*, sp.shop_name, sp.location AS shop_location, sp.display_name,
               sp.user_id AS seller_user_id
        FROM products p JOIN seller_profiles sp ON sp.id=p.seller_id WHERE p.id=?""", (pid,))
    if not p or p["status"] != "published":
        abort(404)
    seller = models.one("SELECT sp.*, u.status FROM seller_profiles sp JOIN users u ON u.id=sp.user_id WHERE sp.id=?",
                        (p["seller_id"],))
    if seller["status"] != "active":
        abort(404)  # suspended seller → listing not publicly exposed
    imgs = models.q("SELECT file FROM product_images WHERE product_id=? ORDER BY sort", (pid,))
    related = models.q("""
        SELECT p.*, sp.shop_name,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p JOIN seller_profiles sp ON sp.id=p.seller_id JOIN users u ON u.id=sp.user_id
        WHERE p.category_id=? AND p.id!=? AND p.status='published' AND u.status='active'
        ORDER BY RANDOM() LIMIT 4""", (p["category_id"], pid))
    wa = wa_link(seller["whatsapp"],
                 f"Hello, I found your product on KanoGadgets.com. I'm interested in {p['name']}. Is it still available?")
    return render_template("public/product.html", p=p, imgs=imgs, seller=seller,
                           related=related, money=money, wa_link=wa)


@app.route("/seller/<int:sid>")
def public_seller(sid):
    sp = models.one("SELECT sp.*, u.status FROM seller_profiles sp JOIN users u ON u.id=sp.user_id WHERE sp.id=?", (sid,))
    if not sp or sp["status"] != "active":
        abort(404)
    products = models.q("""
        SELECT p.*, (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p WHERE p.seller_id=? AND p.status='published' ORDER BY p.created_at DESC""", (sid,))
    wa = wa_link(sp["whatsapp"], "Hello, I found your shop on KanoGadgets.com and I'd like to chat.")
    return render_template("public/seller.html", sp=sp, products=products, money=money, wa_link=wa)


@app.route("/rules")
def rules_page():
    return render_template("public/rules.html")


@app.route("/privacy")
def privacy():
    return render_template("public/privacy.html")


@app.route("/terms")
def terms():
    return render_template("public/terms.html")


@app.route("/report-problem", methods=["GET", "POST"])
def report_general():
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()
        email = request.form.get("contact", "").strip()
        if not reason or not details:
            flash("Please give a reason and a short description.", "err")
        else:
            d = models.get_db()
            d.execute("INSERT INTO admin_activity(actor_id,actor_name,action,meta) VALUES(NULL,'GENERAL_REPORT',?,?)",
                      (reason, f"{email}: {details[:500]}"))
            d.commit(); d.close()
            flash("Report received. Thank you for helping keep KanoGadgets.com safe.", "ok")
            return redirect(url_for("index"))
    return render_template("public/report_general.html")


@app.route("/report/<int:pid>", methods=["GET", "POST"])
def report_product(pid):
    p = models.one("SELECT id,name FROM products WHERE id=? AND status='published'", (pid,))
    if not p:
        abort(404)
    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()
        email = request.form.get("contact", "").strip()
        if not reason:
            flash("Please choose a reason.", "err")
        else:
            d = models.get_db()
            d.execute("INSERT INTO reports(product_id,reporter_email,reason,details) VALUES(?,?,?,?)",
                      (pid, email or None, reason, details))
            d.commit(); d.close()
            flash("Report submitted. Our team will review it.", "ok")
            return redirect(url_for("product_page", pid=pid))
    return render_template("public/report.html", p=p)


# ------------------------------------------------------------------ auth
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        pw = request.form.get("password", "")
        u = models.one("SELECT * FROM users WHERE email=?", (email,))
        if not u or not bcrypt.checkpw(pw.encode(), u["hash"].encode()):
            flash("Invalid email or password.", "err")
            return redirect(url_for("login"))
        if u["status"] == "suspended":
            flash("Your account is suspended.", "err")
            return redirect(url_for("login"))
        session.permanent = True
        session.clear()
        session["uid"] = u["id"]
        nxt = request.args.get("next", "")
        if u["role"] == "seller":
            fallback = url_for("seller_home")
        elif u["role"] in ("owner", "admin"):
            fallback = url_for("admin_home")
        else:
            fallback = url_for("become_seller")
        return redirect(nxt if nxt.startswith("/") and not nxt.startswith("//") else fallback)
    return render_template("public/login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Signed out.", "ok")
    return redirect(url_for("index"))


# ------------------------------------------------------------------ seller registration (instant — no review queue)
@app.route("/become-seller", methods=["GET", "POST"])
def become_seller():
    if request.method == "POST":
        f = request.form
        full_name = f.get("full_name", "").strip()
        email     = f.get("email", "").strip().lower()
        phone_raw = f.get("phone", "").strip()
        username  = f.get("username", "").strip()
        reason    = f.get("reason", "").strip()
        pw1, pw2  = f.get("password", ""), f.get("confirm", "")
        errs = []
        for label, val in [("Full name", full_name), ("Email", email), ("Phone (WhatsApp)", phone_raw),
                           ("Username", username), ("Reason for joining", reason)]:
            if not val:
                errs.append(f"{label} is required")
        if email and not re.match(r"^[\w.+-]+@[\w-]+\.[\w.]+$", email):
            errs.append("Enter a valid email address")
        phone = norm_phone(phone_raw)
        if phone_raw and not phone:
            errs.append("Enter a valid Nigerian phone number — e.g. 0803 123 4567 or +234 803 123 4567")
        if username:
            if not re.fullmatch(r"[A-Za-z0-9_.\-]{3,24}", username):
                errs.append("Username: 3–24 chars — letters, digits, dot, dash or underscore only")
            elif models.one("SELECT 1 FROM users WHERE username=? COLLATE NOCASE", (username,)):
                errs.append("That username is taken — pick another one")
        if pw1 and len(pw1) < 10:
            errs.append("Password must be at least 10 characters")
        elif pw1 != pw2:
            errs.append("Passwords do not match")
        if f.get("rules") != "on":
            errs.append("You must accept the Seller Rules & Regulations")
        if email and models.one("SELECT 1 FROM users WHERE email=?", (email,)):
            errs.append("That email already has an account — sign in instead")
        if errs:
            for e in errs:
                flash(e, "err")
            return render_template("public/become_seller.html", form=dict(f), errs=errs[0] if errs else None), 400

        h = bcrypt.hashpw(pw1.encode(), bcrypt.gensalt(rounds=12)).decode()
        d = models.get_db()
        try:
            cur = d.execute(
                "INSERT INTO users(email,username,hash,name,phone,role,status,join_reason) "
                "VALUES(?,?,?,?,?,'seller','active',?)",
                (email, username, h, full_name, phone, reason))
            uid = cur.lastrowid
            d.execute("""INSERT INTO seller_profiles(user_id,display_name,shop_name,location,whatsapp,contact_email)
                         VALUES(?,?,?,?,?,?)""",
                      (uid, username, f"{username}'s shop", "Kano Gadget Center", phone, email))
            d.commit()
        finally:
            d.close()
        session.clear()
        session["uid"] = uid
        session.permanent = True
        flash(f"Welcome to KanoGadgets, {username}! Your seller account is live — add your first product now.", "ok")
        return redirect(url_for("seller_home"))
    return render_template("public/become_seller.html", form={})


@app.route("/application/done")
def application_done():
    return redirect(url_for("become_seller"))


# (legacy invite-token route removed — sellers register instantly now)


# ------------------------------------------------------------------ seller dashboard
@app.route("/seller")
@requires_seller
def seller_home():
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    if not sp:
        return redirect(url_for("seller_profile", complete=1))
    stats = {
        "total":     models.one("SELECT COUNT(*) FROM products WHERE seller_id=?", (sp["id"],))[0],
        "published": models.one("SELECT COUNT(*) FROM products WHERE seller_id=? AND status='published'", (sp["id"],))[0],
        "drafts":    models.one("SELECT COUNT(*) FROM products WHERE seller_id=? AND status='draft'", (sp["id"],))[0],
    }
    recent = models.q("SELECT * FROM products WHERE seller_id=? ORDER BY updated_at DESC LIMIT 5", (sp["id"],))
    return render_template("seller/dashboard.html", sp=sp, stats=stats, recent=recent, money=money)


@app.route("/seller/products")
@requires_seller
def seller_products():
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    rows = models.q("""
        SELECT p.*, (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p WHERE p.seller_id=? ORDER BY p.created_at DESC""", (sp["id"],))
    return render_template("seller/products.html", products=rows, money=money)


@app.route("/seller/add", methods=["GET", "POST"])
@requires_seller
def seller_add_product():
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    cats = models.q("SELECT * FROM categories WHERE active=1 ORDER BY name")
    if request.method == "POST":
        f = request.form
        files = request.files.getlist("images")
        errs = []
        for k, label in [("name", "Product name"), ("price", "Price"), ("category_id", "Category"),
                         ("condition", "Condition"), ("location", "Location"), ("whatsapp", "WhatsApp number")]:
            if not f.get(k, "").strip():
                errs.append(f"{label} is required")
        try:
            price = int(float(f["price"].replace(",", "")))
            if price <= 0:
                raise ValueError
        except Exception:
            errs.append("Price must be a positive number (₦)")
        wa = norm_phone(f.get("whatsapp", ""))
        if not wa:
            errs.append("WhatsApp number looks invalid — use 08031234567 or +2348031234567")
        saved = [save_image(fs, img_exts) for fs in files if fs and fs.filename]
        saved = [x for x in saved if x]
        if not saved:
            errs.append("Upload at least one product image")
        if errs:
            for e in errs:
                flash(e, "err")
            return render_template("seller/add_product.html", cats=cats, sp=sp, form=dict(f), errs=errs), 400
        d = models.get_db()
        d.execute("""INSERT INTO products(seller_id,category_id,name,brand,model,price,condition,
                     description,location,whatsapp,status,availability)
                     VALUES(?,?,?,?,?,?,?,?,?,?,'published',?)""",
                  (sp["id"], int(f["category_id"]), f["name"].strip(), f.get("brand", "").strip(),
                   f.get("model", "").strip(), price, f["condition"], f.get("description", "").strip(),
                   f["location"].strip(), wa, f.get("availability", "In stock")))
        pid = d.execute("SELECT last_insert_rowid()").fetchone()[0]
        for i, fn in enumerate(saved):
            d.execute("INSERT INTO product_images(product_id,file,sort,is_main) VALUES(?,?,?,?)",
                      (pid, fn, i, 1 if i == 0 else 0))
        d.commit(); d.close()
        flash("Published! Your product is live on the marketplace.", "ok")
        return redirect(url_for("seller_products"))
    return render_template("seller/add_product.html", cats=cats, sp=sp, form={})


@app.route("/seller/product/<int:pid>/edit", methods=["GET", "POST"])
@requires_seller
def seller_edit_product(pid):
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    p = models.one("SELECT * FROM products WHERE id=?", (pid,))
    if not p or p["seller_id"] != sp["id"]:
        abort(403, "That product does not belong to you.")
    cats = models.q("SELECT * FROM categories WHERE active=1 ORDER BY name")
    if request.method == "POST":
        f = request.form
        try:
            price = int(float(f["price"].replace(",", "")))
        except Exception:
            flash("Invalid price.", "err")
            return redirect(request.url)
        wa = norm_phone(f.get("whatsapp", ""))
        if not wa:
            flash("Invalid WhatsApp number.", "err")
            return redirect(request.url)
        d = models.get_db()
        d.execute("""UPDATE products SET name=?,category_id=?,brand=?,model=?,price=?,condition=?,
                     description=?,location=?,whatsapp=?,availability=?,updated_at=? WHERE id=?""",
                  (f["name"].strip(), int(f["category_id"]), f.get("brand", "").strip(),
                   f.get("model", "").strip(), price, f["condition"], f.get("description", "").strip(),
                   f["location"].strip(), wa, f.get("availability", "In stock"), now(), pid))
        for fs in request.files.getlist("images"):
            if fs and fs.filename:
                fn = save_image(fs, img_exts)
                if fn:
                    mx = models.one("SELECT COALESCE(MAX(sort),0)+1 FROM product_images WHERE product_id=?", (pid,))[0]
                    d.execute("INSERT INTO product_images(product_id,file,sort) VALUES(?,?,?)", (pid, fn, mx))
        d.commit(); d.close()
        flash("Saved.", "ok")
        return redirect(url_for("seller_products"))
    imgs = models.q("SELECT * FROM product_images WHERE product_id=? ORDER BY sort", (pid,))
    return render_template("seller/edit.html", p=p, cats=cats, imgs=imgs)


@app.route("/seller/product/<int:pid>/delete", methods=["POST"])
@requires_seller
def seller_delete_product(pid):
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    p = models.one("SELECT * FROM products WHERE id=?", (pid,))
    if not p or p["seller_id"] != sp["id"]:
        abort(403, "That product does not belong to you.")
    d = models.get_db()
    d.execute("DELETE FROM product_images WHERE product_id=?", (pid,))
    d.execute("DELETE FROM products WHERE id=?", (pid,))
    d.commit(); d.close()
    flash("Product deleted.", "ok")
    return redirect(url_for("seller_products"))


@app.route("/seller/profile", methods=["GET", "POST"])
@requires_seller
def seller_profile():
    sp = models.one("SELECT * FROM seller_profiles WHERE user_id=?", (g.user["id"],))
    if request.method == "POST":
        f = request.form
        wa = norm_phone(f.get("whatsapp", ""))
        if not wa:
            flash("Invalid WhatsApp number.", "err")
            return redirect(url_for("seller_profile"))
        d = models.get_db()
        d.execute("""UPDATE seller_profiles SET display_name=?,shop_name=?,shop_description=?,
                     location=?,whatsapp=?,contact_email=?,updated_at=? WHERE user_id=?""",
                  (f["display_name"].strip(), f["shop_name"].strip(), f.get("shop_description", "").strip(),
                   f["location"].strip(), wa, f.get("contact_email", "").strip(), now(), g.user["id"]))
        d.commit(); d.close()
        flash("Shop profile updated.", "ok")
        return redirect(url_for("seller_profile"))
    return render_template("seller/profile.html", sp=sp)


@app.route("/seller/rules")
@requires_seller
def seller_rules():
    return render_template("public/rules.html", back="seller_home")


@app.route("/seller/support")
@requires_seller
def seller_support():
    return render_template("seller/support.html")


# ------------------------------------------------------------------ admin
@app.route("/admin")
@requires_admin
def admin_home():
    stats = {
        "sellers":   models.one("SELECT COUNT(*) FROM users WHERE role='seller' AND status='active'")[0],
        "products":  models.one("SELECT COUNT(*) FROM products")[0],
        "published": models.one("SELECT COUNT(*) FROM products WHERE status='published'")[0],
        "flagged":   models.one("SELECT COUNT(*) FROM reports WHERE status='open' OR status='under_review'")[0],
        "new_sellers": models.one("SELECT COUNT(*) FROM users WHERE role='seller' AND created_at >= datetime('now','-7 days')")[0],
    }
    recent_apps = models.q("""
        SELECT u.id, u.name AS full_name, u.username, u.email, u.phone, u.join_reason, u.created_at, u.status,
               sp.shop_name
        FROM users u LEFT JOIN seller_profiles sp ON sp.user_id=u.id
        WHERE u.role='seller' ORDER BY u.created_at DESC LIMIT 6""")
    recent_products = models.q("""
        SELECT p.*, sp.shop_name,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p JOIN seller_profiles sp ON sp.id=p.seller_id ORDER BY p.created_at DESC LIMIT 6""")
    return render_template("admin/dashboard.html", stats=stats, recent_apps=recent_apps,
                           recent_products=recent_products, money=money)


@app.route("/admin/applications")
@app.route("/admin/application/<int:aid>")
@requires_admin
def admin_applications_legacy(aid=None):
    # seller review queue retired — registration is instant now; suspension covers abuse
    flash("Sellers now register instantly — review/suspend them from the Sellers page.", "ok")
    return redirect(url_for("admin_sellers"))


@app.route("/admin/sellers")
@requires_admin
def admin_sellers():
    sellers = models.q("""
        SELECT sp.*, u.email, u.status AS acc_status, u.role,
               (SELECT COUNT(*) FROM products WHERE seller_id=sp.id) AS listings
        FROM seller_profiles sp JOIN users u ON u.id=sp.user_id
        ORDER BY sp.created_at DESC""")
    return render_template("admin/sellers.html", sellers=sellers)


@app.route("/admin/seller/<int:uid>/toggle", methods=["POST"])
@requires_admin
def admin_seller_toggle(uid):
    u = models.one("SELECT * FROM users WHERE id=?", (uid,))
    if not u or u["role"] != "seller":
        abort(404)
    new = "suspended" if u["status"] == "active" else "active"
    d = models.get_db()
    d.execute("UPDATE users SET status=?,updated_at=? WHERE id=?", (new, now(), uid))
    d.execute("INSERT INTO moderation_log(actor_id,target_type,target_id,action) VALUES(?,?,?,?)",
              (g.user["id"], "seller", uid, f"status→{new}"))
    d.commit(); d.close()
    flash(f"Seller {new}.", "ok")
    return redirect(url_for("admin_sellers"))


@app.route("/admin/products")
@requires_admin
def admin_products():
    cat = request.args.get("cat", type=int)
    seller = request.args.get("seller", "").strip()
    status = request.args.get("status", "")
    sql = """
        SELECT p.*, sp.shop_name, c.name AS cat_name,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS main_img
        FROM products p
        JOIN seller_profiles sp ON sp.id=p.seller_id
        LEFT JOIN categories c ON c.id=p.category_id"""
    conds, params = [], []
    if cat:
        conds.append("p.category_id=?"); params.append(cat)
    if seller:
        conds.append("sp.shop_name LIKE ?"); params.append(f"%{seller}%")
    if status:
        conds.append("p.status=?"); params.append(status)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY p.created_at DESC LIMIT 200"
    rows = models.q(sql, params)
    cats = models.q("SELECT id,name FROM categories WHERE active=1 ORDER BY name")
    return render_template("admin/products.html", products=rows, cats=cats, money=money,
                           sel_cat=cat, sel_seller=seller, sel_status=status)


@app.route("/admin/product/<int:pid>/moderate", methods=["POST"])
@requires_admin
def admin_moderate_product(pid):
    p = models.one("SELECT * FROM products WHERE id=?", (pid,))
    if not p:
        abort(404)
    act = request.form.get("action")
    reason = request.form.get("reason", "").strip()
    mapping = {"remove": "removed", "suspend": "suspended", "restore": "published"}
    if act not in mapping:
        abort(400)
    new_status = mapping[act]
    d = models.get_db()
    d.execute("UPDATE products SET status=?,moderation_note=?,updated_at=? WHERE id=?",
              (new_status, reason or None, now(), pid))
    d.execute("INSERT INTO moderation_log(actor_id,target_type,target_id,action,reason) VALUES(?,?,?,?,?)",
              (g.user["id"], "product", pid, f"status→{new_status}", reason))
    d.commit(); d.close()
    flash(f"Product {new_status}.", "ok")
    return redirect(request.referrer or url_for("admin_products"))


@app.route("/admin/reports")
@requires_admin
def admin_reports():
    rows = models.q("""
        SELECT r.*, p.name AS product_name, sp.shop_name,
               (SELECT file FROM product_images WHERE product_id=p.id AND is_main=1 LIMIT 1) AS img
        FROM reports r JOIN products p ON p.id=r.product_id
        JOIN seller_profiles sp ON sp.id=p.seller_id
        WHERE r.status != 'resolved' ORDER BY r.created_at DESC""")
    return render_template("admin/reports.html", reports=rows)


@app.route("/admin/report/<int:rid>/resolve", methods=["POST"])
@requires_admin
def admin_resolve_report(rid):
    act = request.form.get("action")
    if act not in ("resolve", "dismiss"):
        abort(400)
    d = models.get_db()
    d.execute("UPDATE reports SET status=?,reviewer_id=?,resolved_at=? WHERE id=?",
              ("resolved" if act == "resolve" else "dismissed", g.user["id"], now(), rid))
    d.commit(); d.close()
    flash("Report updated.", "ok")
    return redirect(url_for("admin_reports"))


@app.route("/admin/categories", methods=["GET", "POST"])
@requires_admin
def admin_categories():
    if request.method == "POST":
        f = request.form
        name = f["name"].strip()
        icon = f.get("icon", "📦").strip() or "📦"
        desc = f.get("description", "").strip()
        if not name:
            flash("Name required.", "err")
            return redirect(url_for("admin_categories"))
        d = models.get_db()
        try:
            d.execute("INSERT INTO categories(name,slug,description,icon) VALUES(?,?,?,?)",
                      (name, slugify(name), desc, icon))
            d.commit()
            flash("Category added.", "ok")
        except sqlite3.IntegrityError:
            flash("That category name already exists.", "err")
        finally:
            d.close()
        return redirect(url_for("admin_categories"))
    cats = models.q("""
        SELECT c.*, (SELECT COUNT(*) FROM products WHERE category_id=c.id) AS listings
        FROM categories c ORDER BY c.name""")
    return render_template("admin/categories.html", cats=cats)


@app.route("/admin/category/<int:cid>/toggle", methods=["POST"])
@requires_admin
def admin_category_toggle(cid):
    c = models.one("SELECT * FROM categories WHERE id=?", (cid,))
    if not c:
        abort(404)
    d = models.get_db()
    d.execute("UPDATE categories SET active=? WHERE id=?", (0 if c["active"] else 1, cid))
    d.execute("INSERT INTO moderation_log(actor_id,target_type,target_id,action) VALUES(?,?,?,?)",
              (g.user["id"], "category", cid, "deactivated" if c["active"] else "activated"))
    d.commit(); d.close()
    flash(f"Category {'deactivated' if c['active'] else 'activated'}.", "ok")
    return redirect(url_for("admin_categories"))


@app.route("/admin/moderation")
@requires_admin
def admin_moderation_log():
    rows = models.q("SELECT m.*, u.name AS actor_name FROM moderation_log m LEFT JOIN users u ON u.id=m.actor_id ORDER BY m.created_at DESC LIMIT 200")
    return render_template("admin/moderation.html", rows=rows)


# ------------------------------------------------------------------ private files (passport photos)
@app.route("/private/passport/<int:aid>")
@requires_admin
def private_passport(aid):
    a = models.one("SELECT passport_photo FROM seller_applications WHERE id=?", (aid,))
    if not a:
        abort(404)
    return send_from_directory(app.config["PRIVATE_FOLDER"], a["passport_photo"], as_attachment=False)


# ------------------------------------------------------------------ misc
@app.route("/uploads/<path:fn>")
def uploads(fn):
    return send_from_directory(app.config["UPLOAD_FOLDER"], fn)


@app.template_filter("money")
def _money(n):
    return money(n)


@app.context_processor
def inject():
    return dict(user=current_user(), now=datetime.datetime.now)


# ------------------------------------------------------------------ boot
def seed_categories():
    d = models.get_db()
    existing = [r[0] for r in d.execute("SELECT slug FROM categories")]
    default = [
        ("Smartphones", "phones", "Phones from budget to flagship", "📱"),
        ("Laptops & Computers", "laptops", "Laptops, desktops and all-in-ones", "💻"),
        ("Headphones & Earbuds", "audio-head", "Over-ear, in-ear and wireless buds", "🎧"),
        ("Smartwatches", "watches", "Fitness and smart watches", "⌚"),
        ("Gaming Accessories", "gaming", "Consoles, pads, VR and gear", "🎮"),
        ("Chargers & Cables", "power", "Fast chargers, cables and power banks", "🔌"),
        ("Tablets", "tablets", "Android and iPad-class tablets", "🟦"),
        ("Computer Accessories", "pc-acc", "Keyboards, mice, storage and more", "🖱️"),
        ("Speakers & Audio", "audio-spk", "Bluetooth speakers, soundbars, DJ gear", "🔊"),
        ("Other Gadgets", "other", "Everything else in the gadget center", "📦"),
    ]
    for name, slug, desc, icon in default:
        if slug not in existing:
            d.execute("INSERT INTO categories(name,slug,description,icon) VALUES(?,?,?,?)",
                      (name, slug, desc, icon))
    d.commit(); d.close()


if __name__ == "__main__":
    models.init_db()
    seed_categories()
    app.run(host=os.environ.get("HOST", "0.0.0.0"),
            port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("DEBUG") == "1")
