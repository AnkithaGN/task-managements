#!/usr/bin/env bash
# ---------------------------------------------------------------
# deploy/update_server.sh
# Bring the AWS server up to date after pushing new code to GitHub.
# Run ON THE SERVER:  bash /srv/task-management/deploy/update_server.sh
# ---------------------------------------------------------------
set -euo pipefail
cd /srv/task-management

git pull
.venv/bin/pip install -r requirements.txt -q
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py collectstatic --noinput

# If the server's public address changed (after Stop/Start), update the allowed host.
PUBLIC_IP="$(curl -fsS http://checkip.amazonaws.com | tr -d '[:space:]')"
sed -i "s|^DJANGO_ALLOWED_HOSTS=.*|DJANGO_ALLOWED_HOSTS=${PUBLIC_IP},localhost,127.0.0.1|" .env
sed -i "s|^DJANGO_CSRF_TRUSTED_ORIGINS=.*|DJANGO_CSRF_TRUSTED_ORIGINS=http://${PUBLIC_IP}|" .env

sudo systemctl restart taskmanager
echo "Updated. Open: http://${PUBLIC_IP}"
