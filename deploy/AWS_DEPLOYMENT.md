# Deploying the Task Manager on AWS (EC2)

Live demo (while the server is running): http://54.253.173.245
(The address changes if the server is stopped and started again.)

Architecture on one EC2 server:

```
Browser --(port 80)--> Nginx --> Gunicorn (Django) --> PostgreSQL
                         \--> /media/ (profile pictures)
Static files (CSS/JS) are served by WhiteNoise inside Django.
```

## Part A: in the AWS console (about 10 minutes)

1. Create an AWS account on the **Free plan** (no charges; about $100-$200 of credits for up to 6 months).
   - On the Free plan the project is tied to one region (ours: **Asia Pacific (Sydney) ap-southeast-2**).
     Other regions need a paid plan, so stay in the assigned region.
2. **Billing alert first:** Budgets > Create budget > template "Zero spend budget" > your email > Create.
3. EC2 > **Launch instance**:
   - Name: `task-manager`
   - Image: **Ubuntu Server 24.04 LTS** (Free tier eligible), 64-bit (x86)
   - Instance type: **t3.micro** (Free tier eligible)
   - Key pair: create `task-manager-key` (ED25519, .pem) as a backup way in; keep the file private, never commit it
   - Network settings:
     - **Allow SSH traffic from: Anywhere (0.0.0.0/0)** (the browser terminal, EC2 Instance Connect,
       connects from AWS's network, so "My IP" would block it; Ubuntu allows key-based logins only)
     - **Allow HTTP traffic from the internet** (port 80) - required for the website
   - Storage: default (8 GiB gp3); File systems: None
   - Launch instance > View all instances; wait for **Running** and **3/3 checks passed**
4. Note the **Public IPv4 address**.
5. Select the instance > **Connect** > **EC2 Instance Connect** > username `ubuntu` > Connect.

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

Run the automated tests on the server (they use a temporary test database):

```bash
cd /srv/task-management && .venv/bin/python manage.py test --noinput
```

Result on 13 Nov 2026: `Ran 29 tests ... OK`.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| Site times out in the browser, but `curl -sI http://localhost/` on the server gives 200 | Port 80 not open in the security group | Instance > Security tab > security group > Edit inbound rules > Add rule: **HTTP, port 80, 0.0.0.0/0** > Save |
| "Bad Request (400)" | The address is not in `DJANGO_ALLOWED_HOSTS` (for example after Stop/Start) | Run `update_server.sh` |
| "Region unavailable" | Free plan is tied to one region | Use the assigned region |

## Part C: test on the live site

Open `http://<Public IPv4 address>` and run: register, log in with email, create / complete / delete a task,
search and filter, History, upload a profile picture, phone view, `/admin/`.

## Updating after new commits

```bash
bash /srv/task-management/deploy/update_server.sh
```

## Cost safety

- The Free plan cannot charge you; usage is taken from the free credits (t3.micro is about $0.013 per hour).
- After the demo: EC2 > Instances > select > **Instance state > Stop** (or **Terminate** to delete it for good).
- After Stop/Start the public IP changes: run `update_server.sh` to update the allowed address.

## Not included (future work)

- HTTPS needs a domain name and a certificate (for example Let's Encrypt with certbot). Then set `DJANGO_HTTPS=True`.
- A managed database (Amazon RDS) and S3 for uploaded files would be the next step for a larger setup.
- Restrict SSH to the EC2 Instance Connect address range instead of 0.0.0.0/0.
