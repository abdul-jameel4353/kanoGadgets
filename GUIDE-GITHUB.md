# 📤 Uploading KanoGadgets to GitHub — Step-by-Step for Beginners

Total time: **~15 minutes**. You need: an internet connection, the `kanogadgets-github.zip` file, and about 6 commands.

---

## PART 1 — Create a free GitHub account

1. Go to **https://github.com** and click **Sign up**.
2. Enter your email → create a password → pick a username (e.g. `yourname-dev`).
3. Solve the puzzle, click **Continue**, verify the code they email you.
4. Skip the survey screens (click **Skip personalization** or answer anything).
5. You're in — leave the tab open.

---

## PART 2 — Get the project files onto your computer

1. Download `kanogadgets-github.zip` from this workspace to your computer.
2. **Unzip it:**
   - **Windows:** right-click the zip → **Extract All…** → Extract.
   - **Mac:** double-click the zip.
   - **Linux:** right-click → **Extract Here**, or `unzip kanogadgets-github.zip`.
3. You now have a folder called `kanogadgets`. This folder already contains a hidden `.git` folder — **do not delete it**; it holds the ready-made commit so you don't need to set up git history yourself.

---

## PART 3 — Install Git (once, ~2 minutes)

1. Go to **https://git-scm.com/downloads**
2. **Windows:** click **64-bit Git for Windows Setup**, run the installer, and just click **Next → Next → Install** through everything (the defaults are all fine).
3. **Mac:** open **Terminal** (Cmd+Space, type "terminal"), type `git --version`. If it's missing, run `xcode-select --install` and accept.
4. **Linux (Ubuntu/Debian):** `sudo apt install git -y`
5. Verify it works — open a terminal (Windows: search **Git Bash** in the Start menu and open it) and type:

```bash
git --version
```

You should see something like `git version 2.43.0`.

---

## PART 4 — Create an EMPTY repository on GitHub

⚠️ **Important:** the repository must start completely empty — do NOT tick "Add a README" or ".gitignore".

1. On github.com, click the **＋** (top right) → **New repository**.
2. Fill in:
   - **Repository name:** `kanogadgets`
   - **Description:** `Multi-vendor gadget marketplace for Kano State, Nigeria` (optional)
   - Choose **Private** (recommended — this is your business) or Public.
   - **Do NOT tick** "Add a README file", "Add .gitignore", or "Choose a license".
3. Click **Create repository**.
4. You'll land on a page that says *"Quick setup"*. **Leave it open** — you need the URL it shows, like:
   `https://github.com/YOUR-USERNAME/kanogadgets.git`

---

## PART 5 — Create a Personal Access Token (your GitHub "password" for pushing)

GitHub does NOT accept your account password when pushing code. You need a token:

1. While logged in, go to **https://github.com/settings/tokens**
   (or: profile photo → **Settings** → bottom of the left menu → **Developer settings** → **Personal access tokens** → **Tokens (classic)**)
2. Click **Generate new token** → **Generate new token (classic)**.
3. Fill in:
   - **Note:** `kanogadgets-push`
   - **Expiration:** 90 days (or No expiration — your choice)
   - **Tick ONE box only:** ✅ `repo` (the top one — it covers everything you need)
4. Scroll down → **Generate token**.
5. **COPY the token immediately** — it looks like `ghp_xxxxxxxxxxxxxxxxxxxx`. It appears only once. Paste it somewhere safe (a text note) for the next step.

---

## PART 6 — Push the code

Open a terminal in the unzipped `kanogadgets` folder:

- **Windows:** inside the `kanogadgets` folder, hold **Shift** + right-click on empty space → **Open Git Bash here** (or "Open in Terminal").
- **Mac/Linux:** right-click the folder → **New Terminal at Folder**, or `cd ~/Downloads/kanogadgets` (adjust path).

Now run these **4 commands, one at a time:**

```bash
# 1. confirm you're in the right place (should print app.py, run.py etc.)
ls

# 2. tell git who you are (only needed the first time ever on this computer)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# 3. connect the folder to your GitHub repo (use YOUR username!)
git remote add origin https://github.com/YOUR-USERNAME/kanogadgets.git

# 4. push!
git push -u origin main
```

When it asks for login:
- **Username:** your GitHub username
- **Password:** paste the **TOKEN** from Part 5 — *not* your GitHub password.
  (On Windows a green Credential Manager popup may appear instead — enter username + token there.)

✅ **Success looks like:**

```
Enumerating objects: 145, done.
Writing objects: 100% (145/145), 55.20 MiB ...
To https://github.com/your-username/kanogadgets.git
 * [new branch]      main -> main
branch 'main' set up to track 'origin/main'.
```

Now refresh your GitHub repository page in the browser — **all the files are there.** 🎉

---

## PART 7 — Verify it's correct on GitHub

On your repo page, refresh and check:

| You should see | Where |
|---|---|
| `app.py`, `run.py`, `models.py`, `README.md` | top level file list |
| `templates/` with base, public, seller, admin folders | click `templates` |
| `previews/` with 32 .html files | click `previews` |
| `static/fonts`, `static/cat` (10 category photos) | click `static` |

| You should NOT see | Why |
|---|---|
| `data/` folder | contains the database — excluded on purpose |
| `static/uploads/` | product photos + passports stay private |
| `.env`, any password | secrets come from server config, not code |

Open `README.md` on GitHub — anyone cloning later gets exact run instructions.

---

## 🔧 ERROR FIXES (copy-paste the error to me if unsure)

| Error you might see | What it means | Fix |
|---|---|---|
| `Username for 'https://github.com':` then `Password for ...` → `Invalid credentials` | you typed your GitHub **password** | Use the **token** from Part 5, not your password |
| `remote: Repository not found` | typo in the URL, or repo doesn't exist | `git remote remove origin` then re-run step 3 of Part 6 with the exact URL from your repo page |
| `fatal: not a git repository` | you opened the terminal in the wrong folder | `cd` into the `kanogadgets` folder (must contain `app.py`) |
| `remote: Support for password authentication was removed` | old password login attempt | Do Part 5 — token required |
| `failed to push some refs` / `fetch first` | GitHub repo wasn't empty (README added) | delete the repo on GitHub → recreate it empty → retry, OR `git pull origin main --rebase` then push again |
| Saving token forever | optional quality-of-life | `git config --global credential.helper store` before pushing once |
| If popup/green window shows instead of terminal prompt (Windows) | Git Credential Manager | enter username + token in the popup |

---

## AFTER UPLOAD — how to update later

When you change files (e.g. I fix a bug for you), run from the `kanogadgets` folder:

```bash
git add .
git commit -m "describe the change"
git push
```

That's the whole loop. No tokens, no setup ever again on that computer.

---

### 🆕 Bonus: live hosting later
When you're ready to put the site on a real server (VPS / Render / Railway), say the word — I'll generate deployment files and walk you through it.
