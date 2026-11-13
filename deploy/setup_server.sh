#!/usr/bin/env bash
# ---------------------------------------------------------------
# deploy/setup_server.sh
# One-time setup of the Task Manager on a fresh AWS EC2 Ubuntu 24.04 server.
#
# Run ON THE SERVER (EC2 Instance Connect terminal):
#   curl -fsSL https://raw.githubusercontent.com/AnkithaGN/task-managements/main/deploy/setup_server.sh -o setup_server.sh
#   bash setup_server.sh
#
# What it does:
#   1. Installs Python, PostgreSQL, Nginx and Git
#   2. Creates the database and a limited database user (asks you for a password)
#   3. Downloads the code from GitHub into /srv/task-management
#   4. Creates a private .env (new secret key, DEBUG=False, this server's address)
#   5. Runs migrations and collectstatic
#   6. Starts Gunicorn (the Python web server) as a system service
#   7. Puts Nginx in front of it on port 80
# Nothing secret is printed or saved anywhere except the .env file (readable only by you).
# ---------------------------------------------------------------
set -euo pipefail

REPO="https://github.com/AnkithaGN/task-managements.git"
APP_DIR="/srv/task-management"
APP_USER="$(whoami)"

echo "== 1/7 Installing system packages =="
sudo apt-get update -y
sudo apt-get install -y python3-venv python3-pip postgresql nginx git curl

echo "== 2/7 Database =="
read -rsp "Choose a password for the database user taskapp_user (it will not be shown): " DB_PASSWORD
echo
# The password is passed as a psql variable through stdin, so it never appears in the process list or history.
sudo -u postgres psql -v ON_ERROR_STOP=1 -v pw="$DB_PASSWORD" <<'SQL'
SELECT 'CREATE ROLE taskapp_user WITH LOGIN CREATEDB' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'taskapp_user')\gexec
ALTER ROLE taskapp_user WITH PASSWORD :'pw';
SELECT 'CREATE DATABASE task_management OWNER taskapp_user' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'task_management')\gexec
ALTER ROLE taskapp_user SET client_encoding TO 'utf8';
ALTER ROLE taskapp_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE taskapp_user SET timezone TO 'UTC';
SQL

echo "== 3/7 Code =="
sudo mkdir -p "$APP_DIR"
sudo chown "$APP_USER":www-data "$APP_DIR"
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

echo "== 4/7 Private settings (.env) =="
PUBLIC_IP="$(curl -fsS http://checkip.amazonaws.com | tr -d '[:space:]')"
SECRET_KEY="$(.venv/bin/python -c 'from django.core.management.utils import get_random_secret_key as g; print(g())')"
umask 077
cat > .env <<ENV
DJANGO_SECRET_KEY='${SECRET_KEY}'
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=${PUBLIC_IP},localhost,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=http://${PUBLIC_IP}
DJANGO_HTTPS=False

DB_NAME=task_management
DB_USER=taskapp_user
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432
ENV
umask 022
unset DB_PASSWORD SECRET_KEY

echo "== 5/7 Migrate and collect static files =="
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput
mkdir -p media
sudo chown -R "$APP_USER":www-data media
chmod 775 media

echo "== 6/7 Gunicorn service =="
sudo tee /etc/systemd/system/taskmanager.service > /dev/null <<SERVICE
[Unit]
Description=Task Manager (Django + Gunicorn)
After=network.target postgresql.service

[Service]
User=${APP_USER}
Group=www-data
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/.venv/bin/gunicorn config.wsgi:application --workers 2 --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE
sudo systemctl daemon-reload
sudo systemctl enable --now taskmanager
sudo systemctl restart taskmanager

echo "== 7/7 Nginx =="
sudo tee /etc/nginx/sites-available/taskmanager > /dev/null <<NGINX
server {
    listen 80 default_server;
    server_name _;
    client_max_body_size 3M;          # profile pictures are limited to 2 MB

    # Uploaded profile pictures are served directly by Nginx
    location /media/ {
        alias ${APP_DIR}/media/;
    }

    # Everything else goes to Django (Gunicorn). Static files are served by WhiteNoise.
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX
sudo ln -sf /etc/nginx/sites-available/taskmanager /etc/nginx/sites-enabled/taskmanager
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo
echo "=============================================================="
echo " Done! Open:  http://${PUBLIC_IP}"
echo " Create an admin login:  cd ${APP_DIR} && .venv/bin/python manage.py createsuperuser"
echo "=============================================================="
