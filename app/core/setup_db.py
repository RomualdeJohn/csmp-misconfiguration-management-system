import sqlite3
from pathlib import Path
from contextlib import contextmanager

from app.core.constant import CREATE_MISCONFIG_RECORDS_TABLE_SQL, CREATE_FIXED_MISCONFIG_RECORDS_TABLE_SQL
from app.core.logger import log

def connect_to_db(database_name: str) -> sqlite3.Connection:
    """
    Connects to the database and returns a new connection to the database using the database name.
    
    Args:
        database [str]: The name of the database to connect to.

    Returns:
        conn [sqlite3.Connection]: A connection to the database.
    
    """
    try:
        db_dir = Path(__file__).resolve().parent.parent / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        db_path = db_dir / database_name
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = sqlite3.Row
        log.debug("Connected to database successfully.")
        return conn

    except sqlite3.Error as e:
        log.error(f"Connecting to database error: {e}")
        raise

@contextmanager
def get_db_connection(database_name: str):
    """
    Context manager for database connections.
    Automatically handles connection setup and cleanup.
    
    Args:
        database_name [str]: The name of the database to connect to.
    
    Yields:
        sqlite3.Connection: A connection to the database.
    """
    db_conn = None
    try:
        db_conn = connect_to_db(database_name)
        yield db_conn
    finally:
        if db_conn:
            db_conn.close()
            log.debug("Database connection closed.")

def create_misconfiguration_records_table(conn: sqlite3.Connection) -> None:
    """
    Creates the misconfiguration records table.

    Args:
        conn [sqlite3.Connection]: An active connection to the database.
    """
    try:
        create_misconfiguration_records_table_sql = CREATE_MISCONFIG_RECORDS_TABLE_SQL 
        conn.execute(create_misconfiguration_records_table_sql)
        conn.commit()
        log.warning("Misconfiguration records table created or already exists successfully.")

    except sqlite3.Error as e:
        log.error(f"Creating table error: {e}")
        raise e

def create_fixed_misconfiguration_records_table(conn: sqlite3.Connection) -> None:
    """
    Creates the fixed misconfiguration records table.

    Args:
        conn [sqlite3.Connection]: An active connection to the database.
    """
    try:
        create_fixed_misconfiguration_records_table_sql = CREATE_FIXED_MISCONFIG_RECORDS_TABLE_SQL 
        conn.execute(create_fixed_misconfiguration_records_table_sql)
        conn.commit()
        log.warning("Fixed misconfiguration records table created or already exists successfully.")

    except sqlite3.Error as e:
        log.error(f"Creating fixed misconfiguration records table error: {e}")
        raise e


