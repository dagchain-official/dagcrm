# DAGOS CRM — Production Deployment Guide

Host the CRM for your client on a DigitalOcean droplet with a domain and free HTTPS.

- **Droplet:** `fxartha-crm` · **IP:** `206.189.20.129`
- **Domain:** `dagcrm.com`
- **Stack:** Docker Compose → Postgres + Django (gunicorn) + FastAPI + React (static) + **Caddy** (automatic HTTPS)

Everything runs with a few commands. Follow the steps in order.

---

## Step 1 — Point the domain to the server (do this first)

At your domain registrar (where you bought `dagcrm.com`), open **DNS settings** and add two **A records**:

| Type | Host / Name | Value |
|------|-------------|-------|
| A    | `@`         | `206.189.20.129` |
| A    | `www`       | `206.189.20.129` |

DNS can take 5 minutes to a few hours to propagate. Do the rest meanwhile; HTTPS only works once this resolves.

---

## Step 2 — Connect to the server (SSH)

From your Windows machine (PowerShell or Git Bash):

```bash
ssh root@206.189.20.129
```

(Your SSH key was added when the droplet was created, so it logs in without a password.)

---

## Step 3 — Install Docker

Run these on the server:

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
```

Verify:

```bash
docker --version
docker compose version
```

---

## Step 4 — Open the firewall (recommended)

```bash
ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw --force enable
```

---

## Step 5 — Get the code onto the server

Easiest is to clone your GitHub repo:

```bash
cd /opt
git clone https://github.com/Himanshu08-tech/Dagos-CRM.git crm
cd crm
```

> If the repo is private, either make it temporarily public, use a GitHub token, or upload the folder with `scp`.

---

## Step 6 — Create the secrets file

Copy the example and fill in real values:

```bash
cp .env.prod.example .env.prod
nano .env.prod
```

Set:

```
DOMAIN=dagcrm.com
SECRET_KEY=<paste a long random string>
POSTGRES_DB=dagos
POSTGRES_USER=dagos
POSTGRES_PASSWORD=<a strong password>
```

Generate a strong `SECRET_KEY` quickly:

```bash
openssl rand -base64 48
```

Save in nano: `Ctrl+O`, `Enter`, then `Ctrl+X`.

---

## Step 7 — Build and start everything

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

First build takes a few minutes. Check status:

```bash
docker compose -f docker-compose.prod.yml ps
```

`db`, `backend`, `ai-service`, `caddy` should be **running** (`frontend` shows **exited** — that's correct, it only builds the site and stops).

---

## Step 8 — Create the admin login + roles/permissions

Run the seed **once** to create the admin account and the roles/permission matrix:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py seed
```

This creates the login:

- **Email:** `admin@dagos.com`
- **Password:** `admin123`

---

## Step 9 — Open the site

Visit **https://dagcrm.com** — Caddy fetches an SSL certificate automatically on the first visit (give it ~30 seconds). Log in with the admin account above.

> **Do immediately:** go to the **gear icon → Change Password** and set a strong admin password.

---

## You're live 🎉

The CRM now runs at `https://dagcrm.com` for your client:
- `https://dagcrm.com` — the app
- `https://dagcrm.com/api/` — API
- `https://dagcrm.com/admin/` — Django admin

---

## Everyday operations

**View logs**
```bash
docker compose -f docker-compose.prod.yml logs -f backend
```

**Restart**
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod restart
```

**Deploy an update (after pushing new code to GitHub)**
```bash
cd /opt/crm
git pull
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

**Back up the database**
```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U dagos dagos > backup_$(date +%F).sql
```

---

## Optional settings

- **Remove demo data:** the seed adds sample businesses/leads. Delete them from the app once real data is in, or ask to run a clean-seed instead.
- **FXArtha auto-sync:** background sync is off under gunicorn by default. To enable, add `FORCE_AUTOSYNC: "1"` under `backend → environment` in `docker-compose.prod.yml` and set a valid FXArtha API key in the Integration Hub.
- **Real outgoing email (password resets, notifications):** add SMTP vars to the backend environment: `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Site not loading / no HTTPS | Confirm the DNS A records point to `206.189.20.129` (`ping dagcrm.com`). Certs only issue after DNS resolves. |
| `frontend` shows exited | Normal — it only builds the static site and stops. |
| 502 / API errors | `docker compose -f docker-compose.prod.yml logs backend` to see the error. |
| Changed `.env.prod` | Re-run the `up -d` command to apply. |
