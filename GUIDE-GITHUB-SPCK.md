# 📱 Upload KanoGadgets to GitHub — Android, NO Termux (SPCK method)

For: repo already created (with README is fine), no terminal apps.
Time: **~15 minutes**. Apps needed: **SPCK Editor** + a file manager that can unzip (ZArchiver, or your phone's built-in "Files" app).

---

## PART 1 — Install the apps (Play Store is fine here)

1. Install **SPCK Editor** — Play Store: https://play.google.com/store/apps/details?id=io.spck
2. Install **ZArchiver** (only if your phone can't unzip) or confirm your **Files** app opens zips.
3. Download `kanogadgets-github.zip` from this workspace → it lands in **Downloads**.

---

## PART 2 — Unzip the project

Using your Files app or ZArchiver:

1. Open `kanogadgets-github.zip` → **Extract**.
2. Destination: create a folder named **`kg`** in internal storage root (→ `/storage/emulated/0/kg/`).
3. After extraction you should have: `storage/kg/kanogadgets/` containing `app.py`, `templates/`, `static/`…

---

## PART 3 — Make your GitHub token (Chrome)

1. Chrome → **https://github.com/settings/tokens** → sign in if asked.
2. **Generate new token → Generate new token (classic)**.
3. Note: `spck-push` · Expiration: 90 days · Tick ✅ **`repo`** only.
4. **Generate token** → **COPY** `ghp_xxxxxxxx...` (long-press → Copy). Save into Notes — shown once.

---

## PART 4 — Sign SPCK into GitHub

1. Open **SPCK Editor**.
2. If a login/welcome screen appears, skip it.
3. Tap ☰ (top-left) → **Settings** → **Git** (or **Version Control**): SPCK asks for GitHub credentials when pushing; we'll feed the token at push time. No account login needed inside SPCK.

---

## PART 5 — Clone YOUR repo into SPCK

⚠️ Not "Import" — **Clone** first, so SPCK keeps your repo and its README history.

1. In SPCK, tap **＋ / Create Project → Git Clone** (or "Clone Repository").
2. **Repository URL:** `https://github.com/YOUR-USERNAME/kanogadgets.git` (copy it from your repo page).
3. It may ask credentials right away:
   - **Username:** your GitHub username
   - **Password:** paste the **token** (`ghp_…`)
4. SPCK downloads your repo — you'll see its `README.md`.

---

## PART 6 — Put the project files INTO the cloned repo

1. Open the cloned **kanogadgets** project in SPCK.
2. Tap the **⋮ menu → Import → From Zip** → pick `/storage/emulated/0/kg/kanogadgets-github.zip`.
   - If SPCK asks about conflicts: choose **Overwrite existing** (our README.md replaces the starter one — correct).
3. Wait for the import to finish — SPCK now shows `app.py`, `templates/`, `static/`, `previews/`…

> If "Import from Zip" is missing in your SPCK version, do it manually: open the app's file panel → **Import files** → browse to `storage/kg/kanogadgets/` → select all top-level items (`app.py`, `run.py`, `models.py`, `requirements.txt`, `README.md`, `templates`, `static`, `previews`) → Import. (Never import the hidden `.git` folder that's inside the zip — SPCK has its own already.)

---

## PART 7 — Commit & Push

1. In SPCK with the project open, tap the **Git** icon (usually bottom bar or ⋮ → Git).
2. **Commit:** type `KanoGadgets marketplace — initial upload` → **Commit all**.
3. **Push.** Credentials if asked = same username + **token**.
4. Watch the progress — ~59 MB on mobile data takes a few minutes; keep the screen on.

✅ Refresh your repo page in Chrome: all 145 files are there, and your original README commit is intact in the history.

---

## 🔧 SPCK-specific error fixes

| Problem | Fix |
|---|---|
| Can't find "Git Clone" | Look under ＋ → "Import project" has options: choose **Git**; SPCK versions differ, the word is "Clone" or "Clone Repo…" |
| Push fails: `Authentication failed` | Password field = **token**, not GitHub password |
| `Repository not found` | URL typo — copy it straight from the repo address bar |
| App freezes during import of 59 MB | Let it sit 2–3 min; phones uncompress slowly. If it dies, retry with `static/uploads` and `previews/*.png` skipped, upload those later right in the GitHub web UI folder |
| Everything fails repeatedly | Fall back to Termux (see `GUIDE-GITHUB-ANDROID.md`) — 20 minutes, 100% reliable over one command line |

---

## After upload — future updates from your phone

In SPCK: project open → Git → **Pull** (get latest) → make edits → **Commit** → **Push** — three taps.
