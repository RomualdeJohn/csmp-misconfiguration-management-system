import sqlite3
import csv
import io
import re

from typing import List, Dict, Tuple, Any, Optional
from jira import JIRA, JIRAError
from datetime import datetime
from dateutil import parser as date_parser

from app.core.logger import log
from app.core.setup_db import get_db_connection, create_misconfiguration_records_table, create_fixed_misconfiguration_records_table
from app.core.constant import MISCONFIG_MANAGEMENT_DB, REASON_FALSE_POSITIVE, REASON_RISK_ACCEPTANCE, REASON_FIXED, REASON_BUSINESS_REQUIRED, REASON_PUBLICLY

FIXED = 'fixed'
FALSE_POSITIVE = 'false positive'
RISK_ACCEPTANCE = 'risk acceptance'


def convert_scientific_notation_to_string(value: str) -> str:
    """
    Convert scientific notation to full number string.
    This prevents SQLite from storing large numbers in scientific notation.
    
    Args:
        value: String value that may be in scientific notation
        
    Returns:
        str: Full number as string, or original value if not scientific notation
    """
    if not value or not isinstance(value, str):
        return str(value) if value is not None else ''
    
    # Check if value is in scientific notation
    scientific_pattern = r'^[\d.]+[eE][+-]?\d+$'
    if re.match(scientific_pattern, value.strip()):
        try:
            num_value = float(value)
            if num_value.is_integer():
                return str(int(num_value))
            else:
                return str(int(num_value))
        except (ValueError, OverflowError):
            return value
    
    return value


def create_tables_db() -> None:
    """
    Create the tables in the database.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            create_misconfiguration_records_table(db_conn)
            # create_fixed_misconfiguration_records_table(db_conn)
    except Exception as e:
        log.error(f"Error creating tables: {e}")
        return None

def authenticate_jira(jira_username: str, jira_password: str) -> bool:
    """
    Authenticate with the Jira API server with given credentials.

    Args:
        jira_username [str]: The username of the user.
        jira_password [str]: The password of the user.

    Returns:
        bool: True if authentication successful, False otherwise.
    """
    try:
        url = "https://jira.rakuten-it.com/jira"
        
        log.info(f"Authenticating with Jira API server with username: {jira_username}")
        jira = JIRA({"server": url}, 
                    basic_auth=(jira_username, jira_password), 
                    max_retries=0,
                    )
        if jira:
            log.info(f"Authenticated with Jira API server successfully with username: {jira_username}")
            return True
        else:
            return False

    except JIRAError as e:
        log.error(f"Failed to authenticate with Jira API server: {e}")
        return False

def get_misconfig_records_table_db(account_id: str, resource_id: str, rule_id: str, findings: str) -> Dict[str, str]:
    """
    Get the misconfiguration records from the database.

    Args:
        account_id [str]: The account ID.
        resource_id [str]: The resource ID.
        rule_id [str]: The rule ID.
        findings [str]: The findings.

    Returns:
        Dict[str, str]: The misconfiguration records.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        SELECT * FROM misconfig_records_table 
                        WHERE account_id = ? AND resource_id = ? AND rule_id = ? AND findings = ?
                    """

            values = (str(account_id), str(resource_id), str(rule_id), str(findings))
            cursor = db_conn.cursor()
            cursor.execute(query, values)
            result = cursor.fetchone()

            log.debug(f"Misconfiguration found: {result} for account_id={account_id}, resource_id={resource_id}, rule_id={rule_id}, findings={findings}")

            if result:
                return {key: result[key] for key in result.keys()}
            return None

    except sqlite3.Error as e:
        log.warning(f"Error getting misconfiguration: {e}")
        return None
    except Exception as e:
        log.error(f"Error getting misconfiguration: {e}")
        return None

def get_all_misconfig_records_table_db(audit_ticket: str) -> List[Dict[str, str]]:
    """
    Get all the misconfiguration records from the database.

    Args:
        audit_ticket [str]: The audit ticket.

    Returns:
        List[Dict[str, str]]: The misconfiguration records.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        SELECT 'misconfig' AS source, m.*
                        FROM misconfig_records_table m
                        WHERE m.audit_ticket = ?
                    """

            cursor = db_conn.cursor()
            cursor.execute(query, (audit_ticket,))
            result = cursor.fetchall()
            
            if result:
                return [{key: row[key] for key in row.keys()} for row in result]
            return []

    except sqlite3.Error as e:
        log.warning(f"Error fetching all misconfiguration: {e}")
        return []
    except Exception as e:
        log.error(f"Error fetching all misconfiguration: {e}")
        return []

def get_fixed_misconfig_records_table_db(account_id: str, resource_id: str, rule_id: str, findings: str) -> Dict[str, str] | None:
    """
    Get the fixed misconfiguration records from the database.

    Args:
        account_id [str]: The account ID.
        resource_id [str]: The resource ID.
        rule_id [str]: The rule ID.
        findings [str]: The findings.

    Returns:
        Dict[str, str] | None: The fixed misconfiguration records.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        SELECT * FROM fixed_misconfig_records_table 
                        WHERE account_id = ? AND resource_id = ? AND rule_id = ? AND findings = ?
                    """

            values = (str(account_id), str(resource_id), str(rule_id), str(findings))
            cursor = db_conn.cursor()
            cursor.execute(query, values)
            result = cursor.fetchone()

            if result:
                return {key: result[key] for key in result.keys()}
            return None

    except sqlite3.Error as e:
        log.warning(f"Error getting fixed misconfiguration: {e}")
        return None
    except Exception as e:
        log.error(f"Error getting fixed misconfiguration: {e}")
        return None

def insert_to_misconfig_records_table_db(payload: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Insert the misconfiguration records into the database.

    Args:
        payload [Dict[str, str]]: The payload containing the misconfiguration records.

    Returns:
        Tuple[bool, Optional[str]]: Tuple containing success status and optional error message.
    """
    try:
        if payload.get('reason') not in [REASON_FALSE_POSITIVE, REASON_RISK_ACCEPTANCE, REASON_FIXED, REASON_BUSINESS_REQUIRED, REASON_PUBLICLY]:
            return False, 'invalid reason'

        fix_deadline = payload.get('fix_deadline')
        comment = payload.get('comment')

        is_fix_deadline_invalid = fix_deadline is None or fix_deadline == '' or str(fix_deadline).strip().upper() == 'N/A'
        is_comment_invalid = comment is None or comment == '' or str(comment).strip() == ''
        
        if payload.get('reason') == REASON_RISK_ACCEPTANCE and (is_fix_deadline_invalid or is_comment_invalid):
            return False, 'risk acceptance reason requires a fix deadline and comment'

        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        INSERT INTO misconfig_records_table 
                        (account_id, resource_id, rule_id, findings, audit_ticket, type_audit, cloud_provider, region, 
                        account_name, resource_type, resource_type_name, resource_service, 
                        severity, rule_name, rule_description, remediation, reason, comment, fix_deadline, last_modified_by, last_modified_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
            
            values = (
                str(payload.get('account_id', '')), str(payload.get('resource_id', '')), str(payload.get('rule_id', '')), str(payload.get('findings', '')), 
                payload['audit_ticket'], payload['type_audit'], payload['cloud_provider'], payload['region'], 
                payload['account_name'], payload['resource_type'], payload['resource_type_name'], payload['resource_service'], 
                payload['severity'], payload['rule_name'], payload['rule_description'], payload['remediation'], 
                payload.get('reason'), payload.get('comment'), payload.get('fix_deadline'),
                payload.get('last_modified_by'), payload.get('last_modified_at')
            )

            cursor = db_conn.cursor()
            cursor.execute(query, values)

            rows_inserted = cursor.rowcount

            db_conn.commit()

            if rows_inserted > 0:
                return True, None
            else:
                return False, 'no row inserted'

    except sqlite3.Error as e:
        log.warning(f"Error inserting misconfiguration: {e}")
        return False, e
    except Exception as e:
        log.error(f"Error inserting misconfiguration: {e}")
        return False, e

def insert_to_fixed_misconfig_records_table_db(payload: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Insert the fixed misconfiguration records into the database.

    Args:
        payload [Dict[str, str]]: The payload containing the fixed misconfiguration records.

    Returns:
        Tuple[bool, Optional[str]]: Tuple containing success status and optional error message.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        INSERT INTO fixed_misconfig_records_table 
                        (account_id, resource_id, rule_id, findings, audit_ticket, type_audit, cloud_provider, region, 
                        account_name, resource_type, resource_type_name, resource_service, 
                        severity, rule_name, rule_description, remediation, reason, comment, fix_deadline, last_modified_by, last_modified_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """

            values = (
                str(payload.get('account_id', '')), str(payload.get('resource_id', '')), str(payload.get('rule_id', '')), str(payload.get('findings', '')), 
                payload['audit_ticket'], payload['type_audit'], payload['cloud_provider'], payload['region'], 
                payload['account_name'], payload['resource_type'], payload['resource_type_name'], payload['resource_service'], 
                payload['severity'], payload['rule_name'], payload['rule_description'], payload['remediation'], 
                payload.get('reason'), payload.get('comment'), payload.get('fix_deadline'),
                payload.get('last_modified_by'), payload.get('last_modified_at')
            )

            cursor = db_conn.cursor()
            cursor.execute(query, values)

            rows_inserted = cursor.rowcount

            db_conn.commit()

            if rows_inserted > 0:
                return True, None
            else:
                return False, 'no row inserted'

    except sqlite3.Error as e:
        log.warning(f"Error inserting to fixed misconfiguration records table: {e}")
        return False, e
    except Exception as e:
        log.error(f"Error inserting to fixed misconfiguration records table: {e}")
        return False, e

def update_misconfig_records_table_db(payload: Dict[str, str]) -> None:
    """
    Update the misconfiguration records in the database.

    Args:
        payload [Dict[str, str]]: The payload containing the misconfiguration records.

    Returns:
        None: The misconfiguration records updated in the database.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        UPDATE misconfig_records_table 
                        SET reason = ?, comment = ?, fix_deadline = ?, audit_ticket = ?, last_modified_by = ?, last_modified_at = ?
                        WHERE account_id = ? AND resource_id = ? AND rule_id = ? AND findings = ?
                    """

            values = (payload['reason'], payload['comment'], payload['fix_deadline'], payload['audit_ticket'], payload['last_modified_by'], payload['last_modified_at'], 
                     str(payload.get('account_id', '')), str(payload.get('resource_id', '')), str(payload.get('rule_id', '')), str(payload.get('findings', '')))

            cursor = db_conn.cursor()
            cursor.execute(query, values)
            
            rows_updated = cursor.rowcount
            
            db_conn.commit()

            if rows_updated > 0:
                return True
            else:
                return False
            
    except sqlite3.Error as e:
        log.warning(f"Error updating misconfiguration: {e}")
        return False
    except Exception as e:
        log.error(f"Error updating misconfiguration: {e}")
        return False

def delete_from_misconfig_records_table_db(payload: Dict[str, str]) -> None:
    """
    Delete the misconfiguration records from the database.

    Args:
        payload [Dict[str, str]]: The payload containing the misconfiguration records.

    Returns:
        None: The misconfiguration records deleted from the database.
    """
    try:
        with get_db_connection(MISCONFIG_MANAGEMENT_DB) as db_conn:
            query = """
                        DELETE FROM misconfig_records_table 
                        WHERE account_id = ? AND resource_id = ? AND rule_id = ? AND findings = ?
                    """

            values = (str(payload.get('account_id', '')), str(payload.get('resource_id', '')), str(payload.get('rule_id', '')), str(payload.get('findings', '')))

            cursor = db_conn.cursor()
            cursor.execute(query, values)
            
            rows_deleted = cursor.rowcount

            db_conn.commit()

            if rows_deleted > 0:
                return True
            else:
                return False

    except sqlite3.Error as e:
        log.warning(f"Error deleting from misconfiguration records table: {e}")
        return False
    except Exception as e:
        log.error(f"Error deleting from misconfiguration records table: {e}")
        return False

def parsed_csv_file(contents: str) -> List[Dict[str, str]]:
    """
    Parse the CSV file.

    Args:
        contents [str]: The contents of the CSV file.

    Returns:
        List[Dict[str, str]]: The parsed CSV file.
    """
    try:
        try:
            decoded_content = contents.decode('utf-8')
        except UnicodeDecodeError:
            decoded_content = contents.decode('latin-1')
        
        csv_reader = csv.DictReader(io.StringIO(decoded_content))

        return csv_reader

    except Exception as e:
        log.error(f"Error parsing CSV file: {e}")
        return None

def remove_columns_from_csv(
    data: List[Dict[str, str]], 
    columns_to_remove: List[str]
) -> List[Dict[str, str]]:
    """
    Remove specified columns from CSV data.
    
    Args:
        data: List of dictionaries representing CSV rows
        columns_to_remove: List of column names to remove
        
    Returns:
        List[Dict[str, str]]: Data with specified columns removed
    """
    if not columns_to_remove:
        return data
    
    filtered_data = []
    for row in data:
        filtered_row = {k: v for k, v in row.items() if k not in columns_to_remove}
        filtered_data.append(filtered_row)
    
    return filtered_data

def extract_primary_key(row: Dict[str, str]) -> Tuple[str, str, str, str]:
    """
    Extract the primary key from the row.

    Args:
        row [Dict[str, str]]: The row containing the primary key.

    Returns:
        Tuple[str, str, str, str]: The primary key.
    """
    try:
        account_id = row.get('account_id') or row.get('Account ID', '')
        resource_id = row.get('resource_id') or row.get('Resource ID', '')
        rule_id = row.get('rule_id') or row.get('Rule ID', '')
        findings = row.get('findings') or row.get('Findings', '')
        
        account_id = convert_scientific_notation_to_string(str(account_id))
        resource_id = convert_scientific_notation_to_string(str(resource_id))
        rule_id = convert_scientific_notation_to_string(str(rule_id))
        findings = convert_scientific_notation_to_string(str(findings))
        
        return account_id, resource_id, rule_id, findings
    except Exception as e:
        log.error(f"Error extracting primary key: {e}")
        return None

def extract_result(result: Dict[str, Any]) -> Tuple[str, str, str, str, str, str] | None:
    """
    Extract the result from the dictionary.

    Args:
        result [Dict[str, Any]]: The dictionary containing the result.

    Returns:
        Tuple[str, str, str, str, str, str] | None: The result.
    """
    try:
        reason = result['reason'] if 'reason' in result.keys() else None
        fix_deadline = result['fix_deadline'] if 'fix_deadline' in result.keys() else None
        comment = result['comment'] if 'comment' in result.keys() else None
        audit_ticket = result['audit_ticket'] if 'audit_ticket' in result.keys() else None
        type_audit = result['type_audit'] if 'type_audit' in result.keys() else None
        severity = result['severity'] if 'severity' in result.keys() else None
        rule_name = result['rule_name'] if 'rule_name' in result.keys() else None
        last_modified_by = result['last_modified_by'] if 'last_modified_by' in result.keys() else None
        last_modified_at = result['last_modified_at'] if 'last_modified_at' in result.keys() else None

        extracted = {
            "reason": reason,
            "fix_deadline": fix_deadline,
            "comment": comment,
            "audit_ticket": audit_ticket,
            "type_audit": type_audit,
            "severity": severity,
            "rule_name": rule_name,
            "last_modified_by": last_modified_by,
            "last_modified_at": last_modified_at
        }

        if extracted is not None:
            return extracted    
        else:
            return None 

    except Exception as e:
        log.warning(f"Error extracting result: {e}")
        return None

def check_if_row_exists_by_reason(row: Dict[str, str]) -> Tuple[bool, Dict[str, Any] | None]:
    """
    Check if the row exists in the database and if it meets the conditions to skip it.

    Args:
        row [Dict[str, str]]: Dictionary containing the row data
        
    Returns:
        Tuple[bool, Dict[str, Any] | None]: Tuple containing:
            - bool: True if the row exists in the database and meets the conditions to skip it, False otherwise
            - Dict[str, Any] | None: Dictionary with metadata if row should be skipped, None otherwise
    """
    
    try:

        account_id, resource_id, rule_id, findings = extract_primary_key(row)
        
        if not account_id or not resource_id or not rule_id or not findings:
            log.info(f"Skipping check: missing required fields (account_id={account_id}, resource_id={resource_id}, rule_id={rule_id}, findings={findings})")
            return False, None
        
        result = get_misconfig_records_table_db(account_id, resource_id, rule_id, findings)
        
        if result is not None:
            

            extracted = extract_result(result)

            added_dict = {
                "reason": extracted['reason'],
                "fix_deadline": extracted['fix_deadline'],
                "audit_ticket": extracted['audit_ticket'],
                "type_audit": extracted['type_audit'],
                "rule_name": extracted['rule_name']
            }
            
            if extracted['reason'].lower() == REASON_FIXED:
                log.info(f"Row already exists in the database with label fixed: Account ID = {account_id}")
                return True, added_dict

            if extracted['reason'].lower() == REASON_FALSE_POSITIVE:
                log.info(f"Row already exists in the database with label false positive: Account ID = {account_id}")
                return True, added_dict
            
            if extracted['reason'].lower() == REASON_RISK_ACCEPTANCE:
                fix_deadline_str = result['fix_deadline'] if 'fix_deadline' in result.keys() else None
                if fix_deadline_str:
                    try:
                        fix_deadline = date_parser.parse(fix_deadline_str)
                        if fix_deadline > datetime.now():
                            log.info(f"Row already exists in the database with label risk acceptance and fix deadline not expired: Account ID = {account_id}")
                            return True, added_dict
                    except (ValueError, TypeError) as e:
                        log.warning(f"Error parsing fix_deadline '{fix_deadline_str}': {e}")
            
            log.info(f"Row already exists in the database but not labeled as false positive or risk acceptance, or labeled as risk acceptance and fix deadline is expired: Account ID = {account_id} | Reason = {extracted['reason']} | Fix Deadline = {extracted['fix_deadline']}")
            return False, None
        else:
            log.info(f"Row does not exist in the database: Account ID = {account_id}")
            return False, None

    except KeyError as e:
        log.warning(f"Missing required column in row: {e}")
        return False, None
    except Exception as e:
        log.error(f"Error checking database: {e}")
        return False, None

def check_if_row_conflict(row: Dict[str, str]) -> Dict[str, Any] | None:
    """
    Check if the row conflicts with the database.

    Args:
        row [Dict[str, str]]: The row containing the primary key.

    Returns:
        Dict[str, Any] | None: The row conflicts with the database.
    """
    try:
        account_id, resource_id, rule_id, findings = extract_primary_key(row)

        if not account_id or not resource_id or not rule_id or not findings:
            log.info(f"Skipping check: missing required fields (account_id={account_id}, resource_id={resource_id}, rule_id={rule_id}, findings={findings})")
            return None
        
        result = get_misconfig_records_table_db(account_id, resource_id, rule_id, findings)
        
        if result is not None:
            log.info(f"Row conflict found: Account ID = {account_id}")

            extracted = extract_result(result)

            # Return all fields from database for potential insertion into fixed_misconfig_records_table
            database_data = {
                "account_id": result.get('account_id') or account_id,
                "resource_id": result.get('resource_id') or resource_id,
                "rule_id": result.get('rule_id') or rule_id,
                "findings": result.get('findings') or findings,
                "rule_name": extracted.get('rule_name') or result.get('rule_name'),
                "comment": extracted.get('comment') or result.get('comment'),
                "reason": extracted.get('reason') or result.get('reason'),
                "fix_deadline": extracted.get('fix_deadline') or result.get('fix_deadline'),
                "audit_ticket": extracted.get('audit_ticket') or result.get('audit_ticket'),
                "type_audit": extracted.get('type_audit') or result.get('type_audit'),
                "severity": extracted.get('severity') or result.get('severity'),
                "last_modified_by": extracted.get('last_modified_by') or result.get('last_modified_by'),
                "last_modified_at": extracted.get('last_modified_at') or result.get('last_modified_at'),
                "cloud_provider": result.get('cloud_provider'),
                "region": result.get('region'),
                "account_name": result.get('account_name'),
                "resource_type": result.get('resource_type'),
                "resource_type_name": result.get('resource_type_name'),
                "resource_service": result.get('resource_service'),
                "rule_description": result.get('rule_description'),
                "remediation": result.get('remediation'),
            }  
            return database_data

    except Exception as e:
        log.error(f"Error checking if row conflict: {e}")
        return None