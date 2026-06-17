from fastapi import APIRouter, UploadFile, HTTPException, Request, Form, File, Depends
from typing import List, Dict, Any
from datetime import datetime

from app.core import limiter
from app.core.auth import get_current_user
from app.core.constant import COLUMNS_TO_EXCLUDE, COLUMNS_TO_ADD
from app.schemas.schema import InitialFalconCSVResponse, DeveloperReviewCSVResponse
from app.core.services import remove_columns_from_csv, check_if_row_exists_by_reason, parsed_csv_file, check_if_row_conflict, extract_primary_key, get_misconfig_records_table_db, convert_scientific_notation_to_string

from app.core.logger import log

import csv

router = APIRouter(prefix="/v1", tags=["CSV File Processing"])

@router.post("/initial-falcon-csv-processing", response_model=InitialFalconCSVResponse, name="Process the uploaded Falcon .csv file")
@limiter.limit("100/minute")
async def upload_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV Falcon CSV file to be uploaded and parsed"),
    audit_type: str = Form(..., description="Type of the audit (RegularAudit or PreReleaseAudit)"),
    current_user: dict = Depends(get_current_user),
) -> InitialFalconCSVResponse:
    """
    ## Upload and Parse Falcon CSV File
    
    ### Args:
    - **file**: The uploaded CSV file from Falcon to be uploaded and parsed
    - **audit_type**: Type of the audit (RegularAudit or PreReleaseAudit)
        
    ### Returns:
    - **InitialFalconCSVResponse**: Dictionary containing parsed data.

    ### Raises:
    - **HTTPException**: HTTP 400 if invalid file type or CSV parsing error, HTTP 500 on server error.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are allowed."
        )
    
    try:
        contents = await file.read()
        
        csv_reader = parsed_csv_file(contents)
        
        # Convert to list of dictionaries
        parsed_data_for_review: List[Dict[str, str]] = []
        parsed_data_removed: List[Dict[str, str]] = []

        for row in csv_reader:
            if audit_type == "PreReleaseAudit":    
                # Skip if row already exists in the database
                exists, added_dict = check_if_row_exists_by_reason(row)
                if exists:
                    metadata_removed = {
                        "reason": added_dict['reason'],
                        "fix_deadline": added_dict['fix_deadline'],
                        "audit_ticket": added_dict['audit_ticket'],
                        "type_audit": added_dict['type_audit'],
                        "Account ID": row['Account ID'],
                        "Resource Service": row['Resource Service'],
                        "Rule ID": row['Rule ID'],
                        "Findings": row['Findings'],
                        "Severity": row['Severity'],
                        "Cloud Provider": row['Cloud Provider'],
                        "Rule Name": row['Rule Name'],
                        "Resource ID": row['Resource ID'],
                    }
                    parsed_data_removed.append(metadata_removed)
                    continue
            
            # Check for misconfiguration record that are not part of the removed data in the database and pull the data for Reason, Comment and Fix Deadline
            account_id, resource_id, rule_id, findings = extract_primary_key(row)
            misconfig_record = get_misconfig_records_table_db(account_id, resource_id, rule_id, findings)

            field_to_be_added = {key: "" for key in COLUMNS_TO_ADD}

            if misconfig_record:
                reason = misconfig_record.get("reason")
                if reason:
                    reason = reason[0].upper() + reason[1:] if len(reason) > 0 else reason
                fix_deadline = misconfig_record.get("fix_deadline")
                comment = misconfig_record.get("comment")

                if reason.lower() == "fixed":
                    continue
                
                if fix_deadline is None:
                    fix_deadline_value = ""
                elif hasattr(fix_deadline, "isoformat"):
                    fix_deadline_value = fix_deadline.isoformat()
                else:
                    fix_deadline_value = str(fix_deadline)

                field_to_be_added.update(
                    {
                        "Reason": reason or "",
                        "Comment": comment or "",
                        "Fix Deadline": fix_deadline_value or "",
                    }
                )

            row.update(field_to_be_added)
            if any(row.values()):
                parsed_data_for_review.append(row)
        
        fieldnames = csv_reader.fieldnames or []
        
        # Remove excluded columns if defined
        if COLUMNS_TO_EXCLUDE:
            parsed_data_for_review = remove_columns_from_csv(parsed_data_for_review, COLUMNS_TO_EXCLUDE)
            # Update fieldnames to reflect removed columns
            fieldnames = [col for col in fieldnames if col not in COLUMNS_TO_EXCLUDE]
        
        # Add new columns to fieldnames
        if COLUMNS_TO_ADD:
            fieldnames.extend(COLUMNS_TO_ADD)
        
        return {
            "success": True,
            "filename": file.filename,
            "total_rows": len(parsed_data_for_review),
            "total_rows_removed": len(parsed_data_removed),
            "columns": fieldnames,
            "data_for_review": parsed_data_for_review,
            "data_removed": parsed_data_removed,
            "uploaded_at": datetime.utcnow().isoformat(),
            "message": f"Successfully parsed {len(parsed_data_for_review)} rows from {file.filename}",
        }
        
    except csv.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error parsing CSV file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the file: {str(e)}"
        )
    finally:
        await file.close()

@router.post("/developer-review-csv-processing", name="Process the Developer Review .csv file")
@limiter.limit("100/minute")
async def developer_review_csv(
    request: Request,
    file: UploadFile = File(..., description="CSV Falcon CSV file to be uploaded and parsed"),
    audit_ticket: str = Form(..., description="Audit ticket number"),
    type_audit: str = Form(..., description="Type of the audit"),
    current_user: dict = Depends(get_current_user),
) -> DeveloperReviewCSVResponse:
    """
    ## Process Developer Review CSV File
    
    ### Args:
    - **file**: The uploaded CSV file to be processed
    - **audit_ticket**: Audit ticket number
    - **type_audit**: Type of the audit
        
    ### Returns:
    - **DeveloperReviewCSVResponse**: Dictionary containing processed data with conflicts and non-conflicts.

    ### Raises:
    - **HTTPException**: HTTP 400 if invalid file type or CSV parsing error, HTTP 500 on server error.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are allowed."
        )

    try:
        contents = await file.read()
        
        csv_reader = parsed_csv_file(contents)

        parsed_data_with_conflict: List[Dict[str, Any]] = []
        parsed_data_no_conflict: List[Dict[str, Any]] = []

        for row in csv_reader:
            account_id = row.get('Account ID') or row.get('account_id') or None
            resource_id = row.get('Resource ID') or row.get('resource_id') or None
            rule_id = row.get('Rule ID') or row.get('rule_id') or None
            findings = row.get('Findings') or row.get('findings') or None
            
            uploaded_file_data = {"account_id": convert_scientific_notation_to_string(str(account_id)) if account_id else None, 
                            "resource_id": convert_scientific_notation_to_string(str(resource_id)) if resource_id else None, 
                            "rule_id": convert_scientific_notation_to_string(str(rule_id)) if rule_id else None, 
                            "rule_name": row.get('Rule Name') or row.get('rule_name') or None,
                            "findings": convert_scientific_notation_to_string(str(findings)) if findings else None,
                            "comment": row.get('Comment') or row.get('comment') or None,
                            "reason": row.get('Reason') or row.get('reason') or None,
                            "fix_deadline": row.get('Fix Deadline') or row.get('fix_deadline') or None,
                            "severity": row.get('Severity') or row.get('severity') or None,
                            "audit_ticket": audit_ticket if audit_ticket else None,
                            "type_audit": type_audit if type_audit else None,
                            "cloud_provider": row.get('Cloud Provider') or row.get('cloud_provider') or None,
                            "region": row.get('Region') or row.get('region') or None,
                            "account_name": row.get('Account Name') or row.get('account_name') or None,
                            "resource_type": row.get('Resource Type') or row.get('resource_type') or None,
                            "resource_type_name": row.get('Resource Type Name') or row.get('resource_type_name') or None,
                            "resource_service": row.get('Resource Service') or row.get('resource_service') or None,
                            "rule_description": row.get('Rule Description') or row.get('rule_description') or None,
                            "remediation": row.get('Remediation') or row.get('remediation') or None}

            database_data = check_if_row_conflict(row)
            if database_data:
                data = {"uploaded_file_data": uploaded_file_data, "database_data": database_data}
                parsed_data_with_conflict.append(data)
            else:
                parsed_data_no_conflict.append(uploaded_file_data)

        # CSV processing is successful if file was parsed correctly, regardless of conflicts/no-conflicts
        total_rows = len(parsed_data_with_conflict) + len(parsed_data_no_conflict)
        message = f"Successfully processed {file.filename}. Found {len(parsed_data_with_conflict)} conflicts and {len(parsed_data_no_conflict)} non-conflicting records (total: {total_rows} rows)."
        
        return DeveloperReviewCSVResponse(
            response_status="success",
            message=message,
            filename=file.filename,
            audit_ticket=audit_ticket,
            type_audit=type_audit,
            total_no_conlfict=len(parsed_data_no_conflict),
            total_conflicts=len(parsed_data_with_conflict),
            conflicts=parsed_data_with_conflict,
            no_conflicts=parsed_data_no_conflict,
        )

    except csv.Error as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error parsing CSV file: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the file: {str(e)}"
        )
    finally:
        await file.close()