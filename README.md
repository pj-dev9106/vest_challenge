# Portfolio Data Clearinghouse

This is the little “clearinghouse” project for the Vest exercise. It basically ingests some trade files, dumps everything into Postgres, and exposes a few endpoints to look at trades, positions, and a simple compliance rule (the 20% concentration thing). Everything runs in AWS (EC2 + RDS) and deploys through GitHub Actions.

I tried to keep things simple but also close enough to “real” infra.

Currently service is deployed to AWS instance which is created by terraform.
You can check settings in instance.
You can log in to ssh with this command.
```
ssh -i ~/portfolio-app-key.pem ubuntu@35.85.155.242
```


## What this thing does (in plain English)

- There’s an **SFTP server** where files get dropped. Two different file formats.  
- Every few minutes a cron job checks the directory, grabs whatever showed up, and loads them into **one table** in Postgres.
- A Flask app sits in front of it and gives you:
  - `/api/blotter?date=YYYY-MM-DD` → just raw trades for that date  
  - `/api/positions?...` → how each account is allocated by ticker  
  - `/api/alarms?...` → finds cases where one ticker is >20% of the account
- Everything gets put into Docker → GitHub Actions → EC2.
- Logs also print out “alerts” for the concentration rule, like a pretend version of what you’d ship to CloudWatch/SNS.
- API is protected with a super basic API key header.

This is all based on the exercise doc you sent and the AWS environment provided.

## Quick sketch of the setup

There’s an EC2 box running Docker.  
It has:

- `/sftp/inbox` — files land here  
- `/sftp/uploads` — processed files get moved here  
- A cron job every 5 minutes that basically runs:  
  “hey Docker, ingest anything new and archive it”

The app itself is a Flask service container that talks to RDS Postgres.  
Schema is intentionally super simple — one table with all fields from both formats normalized.

## Architecture

```
[SFTP uploads] → /sftp/inbox → cron → manage.py ingest → Postgres → Flask API
```

And the API is just sitting on port 80 of the EC2 machine behind Docker.

## Tech used

Mostly:

- Python + Flask
- SQLAlchemy
- Postgres (RDS)
- Docker + gunicorn
- Terraform (for AWS infra)
- GitHub Actions for CI/CD

## Project Structure

```
app/
  models.py
  routes/api.py
  services/
    ingestion.py
    alerts.py
  utils/auth.py
manage.py
terraform/
.github/workflows/
docker-compose.yml
Dockerfile
```

Not everything is perfect but it’s functional.

## API Core

Everything requires `X-API-Key`.

**Health-check:**  
`GET /health`

**Blotter:**  
`GET /api/blotter?date=2025-01-15`

**Positions:**  
`GET /api/positions?date=2025-01-15`

**Alarms:**  
`GET /api/alarms?date=2025-01-15`  
Returns any account where a single ticker >20%.

## How to run locally

1. Clone and venv:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Start local Postgres:

```
docker-compose up -d db
```

3. Make a `.env`:

```
SECRET_KEY=dev-secret
API_KEY=dev-api-key
DATABASE_URL=postgresql://appuser:AppUserStrongPass123!@localhost:5432/portfolio_clearinghouse
DEBUG=True
```

4. Initialize DB:

```
python manage.py init_db
python manage.py load_sample
```

5. Run the app:

```
python run.py
```

Visit http://localhost:5000/health.

## Tests

Basic tests are under `tests/`.  
Run with:

```
pytest --cov=app
```

## Deployment flow (GitHub Actions)

When `main` is pushed:

1. Install deps  
2. Run the tests  
3. Build the Docker image  
4. SSH into EC2  
5. Pull repo on EC2  
6. Build & run the container  
7. Run ingestion + init_db/load_sample if needed  

Secrets (in GitHub):

- `EC2_HOST`
- `EC2_SSH_KEY`
- `DATABASE_URL`
- `API_KEY`

## SFTP ingestion (how it works)

EC2 has an `sftpuser` chrooted into `/sftp`.  
You upload like:

```
sftp sftpuser@<public-ip>
cd inbox
put format1_sample.csv
```

Cron job (`/usr/local/bin/process_sftp_ingest.sh`) does this every 5 minutes:

- look for `*.csv` → call `ingest_file <file> format1`
- look for `*.txt` → call `ingest_file <file> format2`
- archive them into `/sftp/uploads`

That’s basically it.

## Alerts / logs

Concentration rule logic prints something like:

```
{
  "type": "concentration_violation",
  "account_id": "ACC001",
  "symbol": "AAPL",
  "concentration": 0.27
}
```

In a real setup these would go to CloudWatch + SNS.

## Terraform stuff

Lives in `terraform/`.

Creates:

- RDS Postgres  
- EC2 instance  
- Security groups  
- Required tagging: `CandidateId=kyle-gardner-vest-trial-001`

Run:

```
terraform init
terraform apply -var="allowed_cidr=$(curl -s ifconfig.me)/32"
```

Outputs include DB endpoint + EC2 public IP.

## Cleanup

```
terraform destroy -var="allowed_cidr=$(curl -s ifconfig.me)/32"
```

# SFTP Ingestion (How to Test)

This service supports ingesting trade files via **SFTP**, matching the assessment requirements.

## SFTP Access

SFTP is enabled on the EC2 instance using a secure chroot configuration.

You can connect with:

```bash
sftp sftpuser@35.85.155.242
```

Password (provided separately in the submission email or shared on request):

```
<your-password-here>
```

---

## Directory Layout

Once logged in, you are chrooted into `/sftp` and will see:

```
inbox     # upload CSV/TXT files here
uploads   # processed files are moved here
```

Example session:

```
sftp> pwd
Remote working directory: /
sftp> ls
inbox  uploads
sftp> cd inbox
sftp> put format1_sample.csv
sftp> put format2_sample.txt
sftp> bye
```

---

## How Ingestion Works

On the EC2 instance, a script located at:

```
/usr/local/bin/process_sftp_ingest.sh
```

runs periodically (via cron) and performs the ingestion flow:

1. Scans `/sftp/inbox` for new `*.csv` (format1) and `*.txt` (format2) files  
2. For each file, executes the Dockerized ingestion command:

```bash
docker run --rm \
  -e DATABASE_URL="$DATABASE_URL" \
  -e API_KEY="$API_KEY" \
  -v /sftp:/sftp \
  portfolio-app \
  python manage.py ingest_file /sftp/inbox/<file> <format1|format2>
```

3. Loads parsed trades into the RDS Postgres database  
4. Moves the processed file to `/sftp/uploads` for archiving  

---

## End-to-End Test

1. Upload a file via SFTP into the `inbox` directory  
2. Wait up to a few minutes for ingestion  
   (or I can trigger the script manually during review)  
3. Query the API using the trade date from your file:

```bash
curl -H "X-API-Key: dev-api-key-12345" \
  "http://<EC2_PUBLIC_IP>/api/blotter?date=2025-01-15"
```

If the uploaded file contained trades dated `2025-01-15`, they will appear in the API response.

---


## Things I’d improve if I had more time

- Move secrets to AWS Secrets Manager
- HTTPS (ALB + ACM)
- ECS/Fargate
- Pagination + filters on blotter/positions
- Real alert delivery (SNS/slack webhook)


