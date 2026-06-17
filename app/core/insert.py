import sys
import sqlite3
import csv
from pathlib import Path
from datetime import datetime

# Add backend directory to Python path so we can import app modules
backend_path = Path(__file__).resolve().parent.parent.parent  # Gets backend/ directory
sys.path.insert(0, str(backend_path))

from app.core.logger import log
from app.core.setup_db import connect_to_db, create_misconfiguration_records_table
from app.core.constant import MISCONFIG_MANAGEMENT_DB

def insert_misconfiguration_record(cursor, data: dict) -> None:
    """
    Insert a misconfiguration record using an existing database cursor.
    
    Args:
        cursor: The database cursor object from an active connection.
        data: A dictionary containing the record fields.
    """
    try:
        cursor.execute("""
            INSERT INTO misconfig_records_table 
            (account_id, resource_id, rule_id, findings, audit_ticket, type_audit, cloud_provider, region, 
             account_name, resource_type, resource_type_name, resource_service, 
             severity, rule_name, rule_description, remediation, reason, comment, fix_deadline, 
             last_modified_by, last_modified_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['account_id'], data['resource_id'], data['rule_id'], data['findings'],
            data['audit_ticket'], data['type_audit'], data['cloud_provider'], data['region'], data['account_name'], 
            data['resource_type'], data['resource_type_name'], data['resource_service'],
            data['severity'], data['rule_name'], data['rule_description'], data['remediation'], data['reason'], data['comment'], data['fix_deadline'],
            data.get('last_modified_by'), data.get('last_modified_at')
        ))
    except sqlite3.Error as e:
        log.error(f"Error during insert: {e}")
        raise

def clear_table(cursor) -> None:
    """
    Clear all records from the misconfig_records_table.
    
    Args:
        cursor: The database cursor object from an active connection.
    """
    try:
        cursor.execute("DELETE FROM misconfig_records_table")
        log.info("Cleared all records from misconfig_records_table")
    except sqlite3.Error as e:
        log.error(f"Error clearing table: {e}")
        raise

def convert_date_format(date_str: str) -> str:
    """
    Convert date format from YYYY/MM/DD to YYYY-MM-DD.
    
    Args:
        date_str: Date string in YYYY/MM/DD format
        
    Returns:
        Date string in YYYY-MM-DD format or empty string if conversion fails
    """
    if not date_str or date_str.strip() == '':
        return ''
    
    try:
        # Try parsing YYYY/MM/DD format
        date_obj = datetime.strptime(date_str.strip(), '%Y/%m/%d')
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        # If already in YYYY-MM-DD format, return as is
        try:
            datetime.strptime(date_str.strip(), '%Y-%m-%d')
            return date_str.strip()
        except ValueError:
            log.warning(f"Unable to parse date format: {date_str}")
            return ''

def map_csv_row_to_db_data(row: dict) -> dict:
    """
    Map CSV row data to database format.
    
    Args:
        row: Dictionary containing CSV row data
        
    Returns:
        Dictionary with database field names
    """
    # Convert date format
    fix_deadline = convert_date_format(row.get('Fix Deadline', ''))
    
    return {
        'account_id': row.get('Account ID', '').strip(),
        'resource_id': row.get('Resource ID', '').strip(),
        'rule_id': row.get('Rule ID', '').strip(),
        'findings': row.get('Findings', '').strip(),
        'audit_ticket': row.get('Audit Ticket', '').strip(),  # Not in CSV, set to empty
        'type_audit': row.get('Type', '').strip(),    # Not in CSV, set to empty
        'cloud_provider': row.get('Cloud Provider', '').strip(),
        'region': row.get('Region', '').strip(),
        'account_name': row.get('Account Name', '').strip(),
        'resource_type': row.get('Resource Type', '').strip(),
        'resource_type_name': row.get('Resource Type Name', '').strip(),
        'resource_service': row.get('Resource Service', '').strip(),
        'severity': row.get('Severity', '').strip(),
        'rule_name': row.get('Rule Name', '').strip(),
        'rule_description': row.get('Rule Description', '').strip(),
        'remediation': row.get('Remediation', '').strip(),
        'reason': row.get('Reason', '').strip(),
        'comment': row.get('Comment', '').strip(),
        'fix_deadline': fix_deadline,
        'last_modified_by': 'ts-romualdejohn.baoy',
        'last_modified_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

if __name__ == "__main__":
    conn = None
    try:
        # Get the project root directory (parent of backend)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        csv_file_path = project_root / "insert-data-1.csv"
        
        if not csv_file_path.exists():
            log.error(f"CSV file not found: {csv_file_path}")
            sys.exit(1)
        
        conn = connect_to_db(MISCONFIG_MANAGEMENT_DB)
        
        log.info("Setting up database table...")
        create_misconfiguration_records_table(conn)

        cursor = conn.cursor()
        
        # Clear existing data
        log.info("Clearing existing data from database...")
        clear_table(cursor)
        conn.commit()
        
        # Read and insert CSV data
        log.info(f"Reading CSV file: {csv_file_path}")
        records_inserted = 0
        records_failed = 0
        
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    # Map CSV row to database format
                    db_data = map_csv_row_to_db_data(row)
                    
                    # Skip rows with missing required fields
                    if not db_data['account_id'] or not db_data['resource_id'] or not db_data['rule_id'] or not db_data['findings']:
                        log.warning(f"Skipping row {row_num}: Missing required fields")
                        records_failed += 1
                        continue
                    
                    # Insert record
                    insert_misconfiguration_record(cursor, db_data)
                    records_inserted += 1
                    
                    if records_inserted % 100 == 0:
                        log.info(f"Inserted {records_inserted} records...")
                        
                except Exception as e:
                    log.error(f"Error inserting row {row_num}: {e}")
                    records_failed += 1
                    continue
        
        conn.commit()
        log.info(f"Successfully inserted {records_inserted} records. {records_failed} records failed.")

    except (sqlite3.Error, Exception) as e:
        log.error(f"An error occurred: {e}. Rolling back transaction.")
        if conn:
            conn.rollback()
            
    finally:
        if conn:
            conn.close()
            log.info("Database connection closed.")