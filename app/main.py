from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.migrate import MigrateAndFetchData
from app.routers import misconfiguration
from app.routers import authentication
from app.routers import process_csv
from app.core.services import create_tables_db
from app.core import limiter
from app.core.logger import log
from app.core.clients import get_config
from custom_openapi import custom_openapi

import asyncio
import os


# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
app = FastAPI(
    title="CSPM Misconfiguration Management System API",
    description="This is an API to assess the misconfigurations from the Falcon CSV to the existing records in the datasbase.",
    version="0.1.0",
    # redoc_url="/",
    docs_url="/",
)

origins = [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:8000",
    "http://localhost:80",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:80",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.jpw2-caas1-dev5\.caas\.jpw2f\.r-local\.net",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(process_csv.router)
app.include_router(misconfiguration.router)
app.include_router(authentication.router)
app.openapi = lambda: custom_openapi(app)

migration_task = None

def _enable_auto_backup() -> bool:
    """Check if auto backup should be enabled based on config and environment."""
    env_value = os.getenv('ENABLE_AUTO_BACKUP')
    if env_value is not None:
        return env_value.lower() == 'true'

    try:
        config = get_config()
        return config.getboolean('APP', 'enable_auto_backup', fallback=False)
    except Exception as e:
        log.warning(f"Could not read auto_backup config: {e}. Defaulting to disabled.")
        return False

async def _scheduled_migration():
    """Background task that migrates data to Domo once a day."""
    while True:
        try:
            await asyncio.sleep(86400)
            log.warning("Starting scheduled migration to Domo and S3 backup...")
            
            migrator = MigrateAndFetchData()
            await asyncio.to_thread(migrator.backup_database_to_s3)
            await asyncio.to_thread(migrator.migrate_data_to_domo)
            
            log.warning("Scheduled migration to Domo and S3 backup completed successfully")
        except asyncio.CancelledError:
            log.warning("Migration task cancelled")
            break
        except Exception as e:
            log.error(f"Error in scheduled migration to Domo: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database tables and start background tasks on application startup."""
    global migration_task
    create_tables_db()
    
    if _enable_auto_backup():
        migration_task = asyncio.create_task(_scheduled_migration())
        log.warning("Started periodic migration task (runs once a day)")
    else:
        log.warning("Periodic migration task disabled (set ENABLE_AUTO_BACKUP=true to enable)")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up background tasks on application shutdown."""
    global migration_task
    if migration_task:
        migration_task.cancel()
        try:
            await migration_task
        except asyncio.CancelledError:
            pass
        log.warning("Stopped periodic migration task")

@app.get("/")
async def root():
    return {"message": "The CSPM Misconfiguration Management System API is running."}

@app.get("/health")
async def health():
    """Health check endpoint for container orchestration and monitoring."""
    return {
        "status": "healthy",
        "service": "CSPM Misconfiguration Management System API",
        "version": "0.1.0"
    }


