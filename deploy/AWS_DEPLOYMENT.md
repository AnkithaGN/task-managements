# Deploying the Task Manager on AWS (EC2)

Architecture on one EC2 server:

```
Browser --(port 80)--> Nginx --> Gunicorn (Django) --> PostgreSQL
                         \--> /media/ (profile pictures)
Static files (CSS/JS) are served by WhiteNoise inside Django.
```

## Part A: in the AWS console (you, about 10 minutes)

1. Sign in to https://console.aws.amazon.com and choose the region **Asia Pacific (Mumbai) ap-south-1**.
2. **Billing alert first:** search "Budgets" > Create budget > "Zero spend budget" > your email > Create.
3. Search **EC2** > **Launch instance**:
   - Name: `task-manager`
   - Image: **Ubuntu Server 24.04 LTS** (marked "Free tier eligible")
   - Instance type: the one marked **Free tier eligible** (t2.micro or t3.micro)
   - Key pair: **Proceed without a key pair** (we will use the browser terminal)
   - Network settings: tick **Allow SSH traffic** (from "My IP") and **Allow HTTP traffic from the internet**
   - Storage: keep the default (8 GB gp3)
   - Click **Launch instance**
4. Open the instance > wait until **Instance state = Running** and **2/2 checks passed**.
5. Note the **Public IPv4 address** (for example 13.233.10.20).
6. Click **Connect** > **EC2 Instance Connect** > **Connect**. A terminal opens in the browser.

## Part B: on the server (copy-paste, about 10 minutes)

```bash
curl -fsSL https://raw.githubusercontent.com/AnkithaGN/task-managements/main/deploy/setup_server.sh -o setup_server.sh
bash setup_server.sh
```

Type a new database password when asked (it is not shown). At the end it prints `Open: http://<your IP>`.

Create an admin account:

```bash
cd /srv/task-management && .venv/bin/python manage.py createsuperuser
```

## Part C: test on the live site

Open `http://<Public IPv4 address>` and run: register, log in with email, create / complete / delete a task,
search and filter, History, upload a profile picture, log out. Record results in the test sheet (DEP-03, DEP-04).

## Updating after new commits

```bash
bash /srv/task-management/deploy/update_server.sh
```

## Cost safety

- Free tier covers one small instance for 750 hours a month in the first 12 months (check your account's offer).
- After the demo: EC2 > Instances > select > **Instance state > Stop** (or **Terminate** to delete it for good).
- After Stop/Start the public IP changes: run `update_server.sh` to update the allowed address.

## Not included (future work)

- HTTPS needs a domain name and a certificate (for example Let's Encrypt with certbot). Then set `DJANGO_HTTPS=True`.
- A managed database (Amazon RDS) and S3 for uploaded files would be the next step for a larger setup.
