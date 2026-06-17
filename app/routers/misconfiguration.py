from fastapi import APIRouter, HTTPException, Query, Request, Depends
from typing import Dict, Any

from app.core.logger import log
from app.core import limiter
from app.core.auth import get_current_user
from app.schemas.schema import MisconfigurationInsert, MisconfigurationUpdate, MisconfigurationDelete
from app.core.services import insert_to_misconfig_records_table_db, insert_to_fixed_misconfig_records_table_db, get_all_misconfig_records_table_db, update_misconfig_records_table_db, delete_from_misconfig_records_table_db, get_fixed_misconfig_records_table_db

router = APIRouter(prefix="/v1", tags=["Misconfiguration Management"])

@router.post("/insert-to-misconfig-records-table", name="Insert misconfiguration into the database")
@limiter.limit("500/minute")
async def insert_misconfig_to_misconfig_records_table(
    request: Request,
    data: MisconfigurationInsert,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ## Insert Misconfiguration into the Misconfiguration Records Table
    
    ### Args:
    - **data (MisconfigurationInsert)**: Request body containing the misconfiguration data to be inserted.
    
    ### Returns:
    - **Dict[str, Any]**: Response status and message (HTTP 200 on success).
    
    ### Raises:
    - **HTTPException**: HTTP 500 if insertion fails, HTTP 500 on server error.
    """
    try:
        payload = data.model_dump()
        result, error = insert_to_misconfig_records_table_db(payload=payload)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to insert misconfiguration for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}. Error: {str(error)}"
            )
        
        return {
            "response_status": "success",
            "message": f"Misconfiguration inserted successfully for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while inserting misconfiguration to the misconfiguration records table: {str(e)}"
        )

@router.post("/insert-to-fixed-misconfig-records-table", name="Insert misconfiguration into the fixed misconfiguration records table")
@limiter.limit("500/minute")
async def insert_misconfig_to_fixed_misconfig_records_table(
    request: Request,
    data: MisconfigurationInsert,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ## Insert Misconfiguration into the Fixed Misconfiguration Records Table
    
    ### Args:
    - **data (MisconfigurationInsert)**: Request body containing the misconfiguration data to be inserted.
    
    ### Returns:
    - **Dict[str, Any]**: Response status and message (HTTP 200 on success).
    
    ### Raises:
    - **HTTPException**: HTTP 500 if insertion fails, HTTP 500 on server error.
    """

    try:
        payload = data.model_dump()

        existing_record = get_fixed_misconfig_records_table_db(
            account_id=payload['account_id'],
            resource_id=payload['resource_id'],
            rule_id=payload['rule_id'],
            findings=payload['findings']
        )

        if existing_record:
            log.info(f"Misconfiguration already exists in the fixed misconfiguration records table for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}. Skipping insert.")
            return {
                "response_status": "success",
                "message": (
                    "Misconfiguration already exists in the fixed misconfiguration records table "
                    f"for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, "
                    f"Rule ID: {payload['rule_id']}, Findings: {payload['findings']}. Skipping insert."
                )
            }

        result, error = insert_to_fixed_misconfig_records_table_db(payload=payload)
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to insert misconfiguration for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}. Error: {str(error)}"
            )
        
        return {
            "response_status": "success",
            "message": f"Misconfiguration inserted successfully for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while inserting misconfiguration to the fixed misconfiguration records table: {str(e)}"
        )

@router.get("/get-misconfigurations", name="Get misconfiguration from the misconfiguration records table")
@limiter.limit("100/minute")
async def get_from_misconfig_records_table(
    request: Request,
    audit_ticket: str = Query(...),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ## Get Misconfiguration from the Misconfiguration Records Table
    
    ### Args:
    - **audit_ticket**: Audit ticket number
    
    ### Returns:
    - **Dict[str, Any]**: Dictionary containing success status, message, and list of misconfigurations from the misconfiguration records table (HTTP 200 on success).
    
    ### Raises:
    - **HTTPException**: HTTP 500 on server error.
    """

    try:
        result = get_all_misconfig_records_table_db(audit_ticket=audit_ticket)

        return {
            "response_status": "success",
            "total_misconfigurations": len(result),
            "message": f"{'Successfully fetched all misconfigurations from the misconfiguration records table' if result else 'No misconfigurations found'} for audit ticket: {audit_ticket}.",
            "misconfigurations": result if result else None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while getting misconfigurations from the misconfiguration records table: {str(e)}"
        )

@router.put("/update-from-misconfig-records-table", name="Update misconfiguration in the misconfiguration records table")
@limiter.limit("100/minute")
async def update_misconfig_from_misconfig_records_table(
    request: Request,
    data: MisconfigurationUpdate,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ## Update Misconfiguration in the Misconfiguration Records Table
    
    ### Args:
    - **data (MisconfigurationUpdate)**: Request body containing the misconfiguration data to be updated.

    ### Returns:
    - **Dict[str, Any]**: Dictionary containing response status and message (HTTP 200 on success).

    ### Raises:
    - **HTTPException**: HTTP 404 if record not found, HTTP 500 on server error.
    """

    try:
        payload = data.model_dump()

        result = update_misconfig_records_table_db(payload=payload)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No misconfiguration found to update. Please check the account_id, resource_id, rule_id, and findings for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}."
            )

        return {
            "response_status": "success",
            "message": f"Successfully updated misconfiguration for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}.",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while updating misconfiguration from the misconfiguration records table: {str(e)}"
        )

@router.delete("/delete-from-misconfig-records-table", name="Delete misconfiguration from the misconfiguration records table")
@limiter.limit("100/minute")
async def delete_misconfig_from_misconfig_records_table(
    request: Request,
    request_body: MisconfigurationDelete,
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    ## Delete Misconfiguration from the Misconfiguration Records Table
    
    ### Args:
    - **data (MisconfigurationDelete)**: Request body containing the misconfiguration data to be deleted.
    
    ### Returns:
    - **Dict[str, Any]**: Dictionary containing response status and message (HTTP 200 on success).

    ### Raises:
    - **HTTPException**: HTTP 404 if record not found, HTTP 500 on server error.
    """

    try:
        payload = request_body.model_dump()

        result = delete_from_misconfig_records_table_db(payload=payload)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No misconfiguration found to delete. Please check the account_id, resource_id, rule_id, and findings for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}."
            )

        return {
            "response_status": "success",
            "message": f"Successfully deleted misconfiguration for Account ID: {payload['account_id']}, Resource ID: {payload['resource_id']}, Rule ID: {payload['rule_id']}, Findings: {payload['findings']}."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while deleting misconfiguration from the misconfiguration records table: {str(e)}"
        )