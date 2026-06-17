# CSMP Misconfiguration Management System

A comprehensive web application for processing, tracking, and managing cloud security misconfigurations from Falcon CSV files. Features database persistence, automated workflows, and integration with Domo for analytics.

### Core Functionality
- **Falcon CSV Processing**: Upload and process Falcon CSV files with automatic field mapping
- **Developer CSV Handling**: Compare and manage developer-provided CSV data
- **Database Management**: SQLite-backed storage for misconfiguration records
- **Search & Edit**: Interactive search and edit capabilities for existing records
- **Domo Integration**: Automated hourly data migration to Domo for analytics
- **Conflict Resolution**: Intelligent conflict detection and resolution workflow

### Prerequisites

- **Backend**: Python 3.8+
- **Frontend**: Node.js 22+
- **Docker** (optional): For containerized deployment
- **Kubernetes** (optional): For production deployment
- **Tools**: Git, npm/npx

### Set-up

- **git clone <repository-url>**
- **cd csmp-misconfig-mgmt-system**
- **In the frontend/nginx.conf for development change the proxy-pass `http://backend:8000;`**
- **Create config.ini file (contact the developer for the credentials)**


### Option 1: Docker Compose (Recommended for Quick Start)

```bash
# Build and start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Option 2: Local Development Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

```

```bash
cd frontend

# Install dependencies
npm install

# Run frontend
npm run dev
```

### Acess it in:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Health Check: `http://localhost:8000/health`

### Database Setup 
The database is automatically initialized on first startup. Location:
```
backend/app/database/csmp_misconfiguration_management.db
```
To migrate the current database to your local please run this command:
```bash
cd backend
python -c "from app.core.migrate import MigrateAndFetchData; MigrateAndFetchData().restore_database_from_s3()"
```

### Backend API Endpoints

**Authentication**
- `POST /v1/authentication` - Authentication of user

**CSV Processing:**
- `POST /v1/process-falcon-csv` - Process Falcon CSV file
- `POST /v1/process-developer-csv` - Process developer CSV file
- `POST /v1/compare-csv` - Compare CSV files

**Misconfiguration Management:**
- `POST /v1/insert-to-misconfig-records-table` - Insert new misconfiguration
- `POST /v1/insert-to-fixed-misconfig-records-table` - Mark as fixed
- `GET /v1/get-misconfigurations?audit_ticket={ticket}` - Get by audit ticket
- `PUT /v1/update-from-misconfig-records-table` - Update record
- `DELETE /v1/delete-from-misconfig-records-table` - Delete record


