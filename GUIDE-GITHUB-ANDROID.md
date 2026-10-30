# 📱 Uploading KanoGadgets to GitHub — Android Guide (Termux)

Everything happens on your phone. Total: **~20 minutes**, one-time setup.

> You need: the `kanogadgets-github.zip` file on your phone, ~300 MB free space, and mobile data/Wi-Fi.

---

## PART 1 — Install Termux (the terminal)

⚠️ **Do NOT install "Termux" from Google Play Store** — that version is abandoned and broken.

Install it from F-Droid instead:

1. Download **F-Droid** (app store): go to **https://f-droid.org** → **Download APK** → open the file → allow "Install unknown apps" → **Install**.
2. Open F-Droid → search **Termux** → **Install**.
3. Open Termux once — it will show a black screen with `$`.

*Alternative:* open **https://github.com/termux/termux-app/releases** and download the newest `termux-app_vXX_arm64.apk` directly.

---

## PART 2 — Get the zip onto your phone

1. Download `kanogadgets-github.zip` from this workspace — it will land in your phone's **Downloads** folder.
2. In Termux, run:

```bash
termux-setup-storage
```
   → a popup asks for file permission → tap **Allow**.

```bash
cd ~
pkg update -y
pkg install git unzip -y
```

   (The `pkg update` may ask `Y/n` a few times — just type `y` and Enter each time. Takes ~2–4 minutes.)

---

## PART 3 — Unzip the project

```bash
unzip /sdcard/Download/kanogadgets-github.zip -d ~
cd ~/kanogadgets
ls
```

✅ You should see: `app.py  models.py  run.py  requirements.txt  README.md  static/  templates/  previews/  ...`

If `ls` shows file names — perfect.

---

## PART 4 — Create your GitHub repo (in Chrome)

1. Open **Chrome** on your phone → go to **https://github.com** → sign up / log in.
2. Tap the **＋** icon → **New repository**.
3. Fill in:
   - **Name:** `kanogadgets`
   - Choose **Private** (recommended).
   - ⚠️ **Do NOT tick "Add a README"** — the repo must start empty.
4. Tap **Create repository**.
5. On the next page, copy the repo URL shown near the top — looks like:
   `https://github.com/YOUR-USERNAME/kanogadgets.git`
   (Or just remember it — your username + `/kanogadgets.git`.)

---

## PART 5 — Create your token (GitHub's push password)

1. In Chrome (still on github.com), go to **https://github.com/settings/tokens**
2. Tap **Generate new token** → **Generate new token (classic)**.
3. Fill in:
   - **Note:** `phone-push`
   - **Expiration:** 90 days
   - Tick ✅ **`repo`** (top checkbox — it's all you need)
4. **Generate token** → **long-press → copy** the token (`ghp_xxxxx...`).
   Save it in your Notes app — it shows only once.

---

## PART 6 — Push from Termux

Back in Termux (inside `~/kanogadgets` folder — `pwd` should end with `/kanogadgets`):

```bash
# (a) one-time identity — use your name & email
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# (b) connect to your repo — replace YOUR-USERNAME!
git remote add origin https://github.com/YOUR-USERNAME/kanogadgets.git

# (c) push!
git push -u origin main
```

When asked:

```
Username for 'https://github.com':  ← type your GitHub username, Enter
Password for 'https://...':         ← paste your TOKEN (ghp_...), Enter
```

📌 To paste in Termux: long-press the screen → **Paste**.

✅ **Success looks like:**

```
Enumerating objects: 145, done.
Writing objects: 100% (145/145) ...   ← takes a few minutes on mobile data (59 MB)
 * [new branch]      main -> main
```

The upload is ~59 MB — on slow Nigerian networks this can take 3–10 minutes. Don't close Termux; you'll see lines like `Writing objects: 45%` climbing. If it seems stuck above 0%, it's still working.

**Done** — refresh your repo page in Chrome. All 145 files are there. 🎉

---

## PART 7 — Verify on github.com

Refresh the repo page. You should see `app.py`, `README.md`, `templates/`, `static/`, `previews/`... and you should **NOT** see a `data/` folder or any passwords — those are protected by `.gitignore`.

---

## 🔧 Android-specific error fixes

| Error | Fix |
|---|---|
| `pkg: command not found` / Termux crashes | You installed the **Play Store Termux** — uninstall, use the **F-Droid** one (Part 1) |
| `fatal: not a git repository` | Some unzip tools drop the hidden `.git` folder. Fix in 3 lines: `git init -b main` → `git add -A` → `git commit -m "KanoGadgets marketplace"` — then continue Part 6 |
| `remote: Repository not found` | Wrong URL in step (b). `git remote remove origin` then re-add with exact URL copied from the repo page |
| `Invalid username or password` | You used your GitHub **password**. Use the **token** from Part 5 |
| Push stops at `Writing objects: X%` forever | Network dropped. Ctrl+C → run `git push -u origin main` again — it resumes where it stopped |
| `storage permission denied` on unzip step | Re-run `termux-setup-storage` → Allow; or move the zip with a file manager into Termux's folder: `/data/data/com.termux/files/home/` |
| GitHub page won't let me create repo (mobile UI glitch) | In Chrome: ⋮ menu → tick **Desktop site** — the full page appears |
| Screen off / processor slow | Run `termux-wake-lock` before pushing |

---

## 🚀 No-Termux alternative (easier but less reliable)

Install **SPCK Editor** from the Play Store → sign in with GitHub (it uses a token too) → **Import Project** → pick the zip → then tap **Git → Push**. Works on decent phones but can choke on 59 MB. Termux is the sure path.

---

## After the upload — future updates from your phone

```bash
cd ~/kanogadgets
# (edit files, or I send you new versions — put them in this folder)
git add -A
git commit -m "update"
git push
```
