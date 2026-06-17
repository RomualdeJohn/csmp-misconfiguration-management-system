# CSMP Misconfiguration Management System

A backend API for tracking and managing cloud security misconfigurations. Built for security teams that need to review Falcon scanner findings, assign remediation owners, and monitor fix progress across audits.

## What it does

Security teams run Falcon scans and get CSV exports with hundreds of misconfigurations. This system ingests those CSVs, deduplicates findings against the existing database, and preserves previously entered metadata (reasons, comments, deadlines) so teams don't lose context between audit cycles.

Core features:
- **CSV ingestion** — Upload Falcon scan results; the system handles deduplication and enriches new records with prior metadata
- **Misconfiguration tracking** — Full CRUD for managing findings, with fields for reason, comments, fix deadlines, and last-modified attribution
- **Developer review workflow** — A separate processing step flags conflicts between developer-submitted CSVs and the current database state
- **Domo integration** — Data gets pushed to Domo for reporting and analytics
- **S3 backup** — The SQLite database is backed up to S3; Kubernetes pods restore from backup on startup

## Stack

- **FastAPI** + **Uvicorn** — async REST API
- **SQLite** (WAL mode) — local database
- **Pydantic v2** — request/response validation
- **JWT** — authentication via JIRA credentials
- **boto3** — AWS S3 for database backups
- **pydomo** — Domo API for data warehouse sync
- **pandas** — CSV processing
- **slowapi** — rate limiting
- **Docker** + **Kubernetes** — containerized deployment

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/authentication` | Login with JIRA credentials, returns JWT |
| `POST` | `/v1/initial-falcon-csv-processing` | Upload Falcon scan CSV for an audit |
| `POST` | `/v1/developer-review-csv-processing` | Process developer review CSV, surfaces conflicts |
| `GET` | `/v1/get-misconfigurations` | Fetch records by audit ticket |
| `POST` | `/v1/insert-to-misconfig-records-table` | Add misconfiguration records |
| `PUT` | `/v1/update-from-misconfig-records-table` | Update reason, comment, fix deadline |
| `DELETE` | `/v1/delete-from-misconfig-records-table` | Remove a record |
| `POST` | `/v1/insert-to-fixed-misconfig-records-table` | Move record to fixed table |
| `GET` | `/health` | Health check |

All endpoints except `/health` require a `Bearer` token in the `Authorization` header.

## Running locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Interactive docs available at `http://localhost:8000/docs`.

## Running with Docker

```bash
docker build -t csmp-misconfig-api .
docker run -p 8000:8000 csmp-misconfig-api
```

## Configuration

The app reads from `app/config.ini`. Required sections:

```ini
[APP]
jwt_secret_key = your_secret

[DOMO]
client_id = ...
client_secret = ...
misconfig_records_table_domo_id = ...
fixed_misconfig_records_table_domo_id = ...

[AWS]
access_key_id = ...
secret_access_key = ...
region = us-east-1
s3_backup_bucket = your-bucket-name
endpoint_url = ...
```

## Audit types

The system supports two audit types passed during CSV processing:

- `RegularAudit` — standard periodic security audit
- `PreReleaseAudit` — scan run before a release

Please contact me if you have questions in my linkedin account https://www.linkedin.com/in/romualdebaoy/
