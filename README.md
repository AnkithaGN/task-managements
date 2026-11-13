# TaskManager: Task Management Web Application

A web application where each user registers, logs in with email and password, and manages their own tasks:
create, view, edit, delete, complete, search, filter and sort, with a dashboard, profile picture and activity history.

Built during a 10-day internship (November 2026) by **Ankitha**, mentored by **Pradeep**.

## Features

| Area | What it does |
|---|---|
| Authentication | Register, log in with **email + password**, log out, change password; all pages protected |
| Dashboard | Total / pending / completed / overdue counts, progress bar, per-category cards, upcoming tasks |
| Tasks | Title, description, due date, priority, category (Personal, Work, Study); create, view, edit, delete with confirmation; mark completed / pending |
| Rules | Required fields; today is a valid due date; past dates refused for new or changed dates; unchanged old dates kept when editing |
| Search and filters | Search by title; filter by category, priority, status in any combination; sort by due date, priority, title or newest; 10 per page |
| Overdue | "Due today / in 3 days / 2 days overdue" labels and highlighted rows |
| Profile | Name, email, profile picture (JPG/PNG/WEBP/GIF, max 2 MB) |
| History | Timeline of created, updated, completed, reopened and deleted tasks (deleted tasks stay in history) |
| Security | Users can only see and change their own tasks (others get 404); CSRF protection; database constraints; passwords hashed |
| Admin | Django Admin manages all tasks, categories, profiles and history |
| Design | Responsive (phone to desktop), colourful theme, JavaScript delete confirmation and form checks |

## Technology

Python 3.12 · Django 6.1 · PostgreSQL 16 · HTML, CSS, JavaScript · Gunicorn · Nginx · WhiteNoise · AWS EC2 (Ubuntu 24.04)

## Run it locally (Ubuntu / WSL)

```bash
git clone https://github.com/AnkithaGN/task-managements.git
cd task-managements
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env: secret key and database details
python manage.py migrate     # also adds the Personal, Work and Study categories
python manage.py createsuperuser
python manage.py runserver   # open http://127.0.0.1:8000/
```

A PostgreSQL database and user must exist first (see `.env.example` for the names).

## Tests

```bash
python manage.py test
```

29 automated tests (authentication, task rules, cross-user security, dashboard counts, filters, sorting,
pagination, profile picture, history) run on a separate test database.
The full manual and automated test record is in `docs/Task_Management_Test_Cases.xlsx`.

## Deploy to AWS

Live demo (while the AWS server is running): http://54.253.173.245

See [`deploy/AWS_DEPLOYMENT.md`](deploy/AWS_DEPLOYMENT.md): one EC2 server with Nginx, Gunicorn and PostgreSQL,
set up by `deploy/setup_server.sh`.

## Project structure

```
config/      settings, main URLs
accounts/    registration, email login, profile, profile picture
tasks/       task model, forms, views, dashboard, history, static CSS/JS
templates/   base layout, shared form layout, 404 and 500 pages
deploy/      AWS setup and update scripts
docs/        test cases
```

## Future work

Task sharing between users, due-date email reminders, HTTPS with a domain name, Amazon RDS and S3 for a larger deployment.
