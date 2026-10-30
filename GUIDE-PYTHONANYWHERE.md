# 🚀 Launch KanoGadgets FREE on PythonAnywhere — phone-friendly guide

Cost: **₦0, no card, ever.** Time: **~40 minutes.**
Result: real live site at `https://YOURNAME.pythonanywhere.com` with working login, seller applications, admin approval, WhatsApp ordering.

---

## PART 1 — Sign up (5 min)

1. Chrome → **pythonanywhere.com** → **Start running Python online in less than 60 seconds** → **Create a Beginner account (free)**.
2. **Username matters** — it becomes your web address. Use **`kanogadgets`** if free (→ `https://kanogadgets.pythonanywhere.com`). If taken, try `kanogadgetshub`, `kg-market`, etc.
3. Email + password → confirm email. Done — no card ever.

---

## PART 2 — Clone your repo (3 min)

1. Dashboard → **Consoles** → tap **Bash** (a black terminal opens in the browser!).
2. Paste (long-press → paste), one line at a time:

```bash
git clone https://github.com/abdul-jameel4353/kanoGadgets.git
cd kanoGadgets
```

3. (If the repo is private again: use `git clone https://TOKEN@github.com/abdul-jameel4353/kanoGadgets.git` with your token in place of TOKEN. Never paste the token anywhere else.)

---

## PART 3 — Install packages (5 min)

Still in the Bash console:

```bash
mkvirtualenv --python=python3.10 kg
pip install flask bcrypt pillow
```

(We list them directly; `gunicorn` etc. from requirements.txt isn't used on PythonAnywhere.)

Leave this tab open.

---

## PART 4 — Create the web app (5 min)

1. New browser tab → pythonanywhere.com → **Dashboard → Web tab** → **Add a new web app**.
2. Domain: accept `YOURNAME.pythonanywhere.com` → Next.
3. ⚠️ **IMPORTANT:** choose **Manual configuration** (by "Manual"), NOT Flask/Django helpers.
4. Python version: **3.10** → Next. You're shown a Web settings page — stay here.

---

## PART 5 — Wire it to your app (8 min)

On that same Web settings page, **3 things:**

### (a) Virtualenv
Scroll to **Virtualenv** → tap the red path field → enter:
```
/home/YOURNAME/.virtualenvs/kg
```

### (b) Source code
**Code:** what it usually says → set both **Source code** and **Working directory** to:
```
/home/YOURNAME/kanoGadgets
```

### (c) The WSGI file — the brain connection
1. Find **WSGI configuration file** → it's a link like `/var/www/YOURNAME_pythonanywhere_com_wsgi.py` → **tap it** → an editor opens.
2. **Delete everything inside**, paste exactly this (replace YOURNAME!):

```python
import os, sys

path = '/home/YOURNAME/kanoGadgets'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['KG_SECRET_KEY'] = 'PASTE_A_LONG_RANDOM_STRING_HERE'

import models
models.init_db()
import app as appmod
appmod.seed_categories()

application = appmod.app
```

For `PASTE_A_LONG_RANDOM_STRING_HERE` — bash-contab trick: go back to the console tab and run
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
copy the output, paste it there. (This is your app secret — keep it private.)

3. **Save** the file.

### (d) Static files (one row)
On the Web tab, **Static files** section → add:

| URL | Directory |
|---|---|
| `/static/` | `/home/YOURNAME/kanoGadgets/static/` |

---

## PART 6 — Create the owner + GO LIVE (5 min)

1. Green **Reload** button at the top of the Web tab.
2. Back to the Bash console tab:

```bash
cd /home/YOURNAME/kanoGadgets
workon kg
python3 create_owner.py --email admin@kanogadgets.com --name "Kano Owner"
```
Pick your strong owner password.

3. **Visit `https://YOURNAME.pythonanywhere.com`** — live. 🎉 Log in → `/admin`.

---

## 🧾 PythonAnywhere free-tier rules (normal, just note them)

- Once every **~3 months** the site pauses: log in → Web tab → tap the highlighted **"Run until 3 months from today"** button → back on. Takes 10 seconds.
- Free tier handles modest traffic fine for a Kano-only launch. Upgrade only when you're earning.

## 🆘 If something breaks

| Symptom | Fix |
|---|---|
| **500 / "Something went wrong"** | Web tab → **Error log** link (bottom) → the last Python error line tells us; paste it to me |
| 404 static files | recheck Part 5(d) path — likely a typo |
| App changes don't show | **Reload** button on the Web tab |
| "ModuleNotFoundError: flask" | the virtualenv path in 5(a) is wrong — must be `/home/YOURNAME/.virtualenvs/kg` |
| DB reset worry | it lives at `/home/YOURNAME/kanoGadgets/data/kanogadgets.db` — persists, backed up daily by PA |

## 🔄 Updating the live site later

Edit files on GitHub (like you're already doing) → Bash console:

```bash
cd /home/YOURNAME/kanoGadgets && git pull
```
then **Reload** on the Web tab.
