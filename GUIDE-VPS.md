# 🖥️ Deploy KanoGadgets on your own VPS — Phone-friendly guide

Time: **~45 minutes** once you have the VPS. You'll need: the VPS (paid), your GitHub repo (done ✅), and an SSH app on your phone.

The plan in one line: **VPS runs Ubuntu → we install Python + Nginx → clone from GitHub → Gunicorn serves the app → Nginx answers on port 80 → kanogadgets.com points to it.**

---

## PART 0 — Buy the VPS (15 min)

Any works. Cheapest solid options (~$4–6/mo): **Hostinger VPS**, **Contabo**, **DigitalOcean Droplet**, **Hetzner**.

1. Pick the **smallest plan** (1 vCPU / 1 GB RAM is enough for launch).
2. OS: choose **Ubuntu 22.04** or **24.04**.
3. Set a **root password** (or they'll email one). Keep it safe.
4. Note your **server IP address**, e.g. `45.32.118.44`.

---

## PART 1 — Connect from your phone (5 min)

Install **Termux** (F-Droid → search Termux → Install — same as the GitHub guide). Then inside Termux:

```bash
pkg install openssh -y
ssh root@YOUR-IP
```

Type `yes` when it asks about the fingerprint, then your **root password** (invisible while typing — that's normal).
You're in when the screen shows `root@ubuntu:~#`.

> Every command from here is pasted into this Termux window. Long-press → Paste.

---

## PART 2 — Server setup (10 min, copy-paste)

```bash
apt update && apt upgrade -y
apt install -y python3 python3-venv nginx git

mkdir -p /var/www
cd /var/www
git clone https://github.com/YOUR-USERNAME/kanogadgets.git
cd kanogadgets

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

---

## PART 3 — Create the owner + secret key (5 min)

```bash
# generate a random secret and remember it:
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the long hex string you get. Now make the owner account:

```bash
.venv/bin/python3 create_owner.py --email admin@kanogadgets.com --name "Kano Owner"
```
It will ask you for a password — pick a strong one (min 10 chars, mixed). Save it in your password manager.

---

## PART 4 — The service that keeps the app running (5 min)

```bash
# put YOUR secret from Part 3 in place of REPLACE_ME...
sed -i "s/REPLACE_ME_WITH_LONG_RANDOM_SECRET/PASTE-SECRET-HERE/" deploy/gunicorn.service

cp deploy/gunicorn.service /etc/systemd/system/kanogadgets.service
chown -R www-data:www-data /var/www/kanogadgets

systemctl daemon-reload
systemctl enable --now kanogadgets
systemctl status kanogadgets          # shows "active (running)" in green
```

---

## PART 5 — Nginx faces the world (5 min)

```bash
cp deploy/nginx.conf /etc/nginx/sites-available/kanogadgets
ln -s /etc/nginx/sites-available/kanogadgets /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t           # should say "syntax is ok ... test is successful"
systemctl restart nginx
```

⚡ **Test now in Chrome:** `http://YOUR-IP` — the marketplace homepage must load.

---

## PART 6 — Point kanogadgets.com at the VPS (10 min + DNS wait)

1. Wherever you bought the domain (Namecheap, GoDaddy, Truehost NG…), open **DNS settings** for `kanogadgets.com`.
2. Add two **A records**:
   - Host `@` → your VPS IP
   - Host `www` → your VPS IP
3. Wait 5–60 minutes for DNS to travel.

## PART 7 — Free HTTPS (2 min, once DNS resolves)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d kanogadgets.com -d www.kanogadgets.com
```
Answer the prompts (pick **Redirect** when asked). Now **https://kanogadgets.com** works, with the padlock. 🔒

---

## 🔄 Updating the site later (from your phone)

You edit files **on GitHub** (web UI, same as you did). Then in Termux:

```bash
ssh root@YOUR-IP
cd /var/www/kanogadgets && git pull && systemctl restart kanogadgets
```

Thirty seconds — the new version is live. GitHub → GitHub-web-edits → VPS update: your full loop.

---

## 🆘 Troubleshooting

| Symptom | Where to look |
|---|---|
| Site down | `systemctl status kanogadgets` and `systemctl restart kanogadgets` |
| Fix passwords/db | `/var/www/kanogadgets/data/kanogadgets.db` — **never** delete unless you mean it |
| Logs | `journalctl -u kanogadgets -n 50` |
| Nginx error | `nginx -t` shows exactly which line is broken |
| App changes don't appear | You forgot `systemctl restart kanogadgets` after `git pull` |

## 🔐 Security hardening (do in week one)

```bash
# 1) no root password login over SSH — add your SSH key, then:
sed -i 's/#\?PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
# 2) firewall
ufw allow 'Nginx Full' && ufw allow OpenSSH && ufw enable
# 3) automatic security updates
apt install -y unattended-upgrades
```
(This is optional-but-recommended; I can walk you through SSH keys from your phone.)
