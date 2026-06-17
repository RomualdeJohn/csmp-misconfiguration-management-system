from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class InitialFalconCSVResponse(BaseModel):
    """Response schema for CSV upload endpoint."""
    success: bool = Field(..., description="Whether the upload was successful")
    filename: str = Field(..., description="Name of the uploaded file")
    total_rows: int = Field(..., description="Total number of rows parsed")
    total_rows_removed: int = Field(..., description="Total number of rows removed")
    columns: List[str] = Field(..., description="Column names from the CSV")
    data_for_review: List[Dict[str, Any]] = Field(..., description="Parsed CSV data for review")
    data_removed: List[Dict[str, Any]] = Field(..., description="Parsed CSV data removed")
    uploaded_at: str = Field(..., description="Timestamp of upload (ISO format)")
    message: str = Field(..., description="Success message")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "filename": "falcon_report.csv",
                "total_rows": 10,
                "columns": ["col_head1", "col_head2", "col_head3", "col_head4"],
                "data": [
                    {
                        "col_head1": "value1",
                        "col_head2": "value2",
                        "col_head3": "value3",
                        "col_head4": "value4"
                    }
                ],
                "uploaded_at": "YYYY-MM-DDTHH:MM:SS",
                "message": "Successfully parsed 10 rows from falcon_report.csv",
            }
        }

class DeveloperReviewCSVResponse(BaseModel):
    """Response schema for Developer Review CSV file."""
    response_status: str = Field(..., description="Response status")
    message: str = Field(..., description="Message")
    filename: str = Field(..., description="Name of the uploaded file")
    audit_ticket: str | None = Field(None, description="Audit ticket number")
    type_audit: str | None = Field(None, description="Type of the audit")
    total_no_conlfict: int = Field(..., description="Total number of rows no conflict")
    total_conflicts: int = Field(..., description="Total number of rows conflicts")
    conflicts: List[Dict[str, Any]] = Field(..., description="Conflicts data")
    no_conflicts: List[Dict[str, Any]] = Field(..., description="No conflicts data")

class MisconfigurationInsert(BaseModel):
    """Schema for inserting misconfiguration records."""
    account_id: str = Field(..., description="Account ID")
    resource_id: str = Field(..., description="Resource ID")
    rule_id: str = Field(..., description="Rule ID")
    findings: str = Field(..., description="Findings")
    audit_ticket: str = Field(..., description="Audit ticket number")
    type_audit: str = Field(..., description="Type of audit")
    cloud_provider: str = Field(..., description="Cloud provider")
    region: str = Field(..., description="Region")
    account_name: str = Field(..., description="Account name")
    resource_type: str = Field(..., description="Resource type")
    resource_type_name: str = Field(..., description="Resource type name")
    resource_service: str = Field(..., description="Resource service")
    severity: str = Field(..., description="Severity")
    rule_name: str = Field(..., description="Rule name")
    rule_description: str = Field(..., description="Rule description")
    remediation: str = Field(..., description="Remediation")
    reason: Optional[str] = Field(None, description="Reason")
    comment: Optional[str] = Field(None, description="Comment")
    fix_deadline: Optional[str] = Field(None, description="Fix deadline")
    last_modified_by: Optional[str] = Field(None, description="Last modified by")
    last_modified_at: Optional[str] = Field(None, description="Last modified at")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "account-id-example",
                "resource_id": "resource-id-example",
                "rule_id": "rule-id-example",
                "findings": "findings-example",
                "audit_ticket": "AUDIT-123",
                "type_audit": "IoM",
                "cloud_provider": "azure",
                "region": "us-east-1",
                "account_name": "account-name-example",
                "resource_type": "storage",
                "resource_type_name": "storage-account",
                "resource_service": "resource-service-example",
                "severity": "high",
                "rule_name": "rule-name-example",
                "rule_description": "Security group allows access from 0.0.0.0/0",
                "remediation": "Update security group to restrict access",
                "reason": "false positive",
                "comment": "Already resolved",
                "fix_deadline": "2025-12-31",
                "last_modified_by": "john-doe",
                "last_modified_at": "2025-01-15T10:30:00Z"
            }
        }

class MisconfigurationUpdate(BaseModel):
    """Schema for updating misconfiguration records."""
    account_id: str = Field(..., description="Account ID")
    resource_id: str = Field(..., description="Resource ID")
    rule_id: str = Field(..., description="Rule ID")
    findings: str = Field(..., description="Findings")
    audit_ticket: str = Field(..., description="Audit ticket number")
    reason: Optional[str] = Field(None, description="Reason")
    comment: Optional[str] = Field(None, description="Comment")
    fix_deadline: Optional[str] = Field(None, description="Fix deadline")
    last_modified_by: Optional[str] = Field(None, description="Last modified by")
    last_modified_at: Optional[str] = Field(None, description="Last modified at")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "account-id-example",
                "resource_id": "resource-id-example",
                "rule_id": "rule-id-example",
                "findings": "findings-example",
                "audit_ticket": "AUDIT-123",
                "reason": "false positive",
                "comment": "Already resolved",
                "fix_deadline": "2024-12-31",
                "last_modified_by": "john-doe",
                "last_modified_at": "2025-01-01T00:00:00Z"
            }
        }

class MisconfigurationDelete(BaseModel):
    """Schema for deleting misconfiguration records."""
    account_id: str = Field(..., description="Account ID")
    resource_id: str = Field(..., description="Resource ID")
    rule_id: str = Field(..., description="Rule ID")
    findings: str = Field(..., description="Findings")

    class Config:
        json_schema_extra = {
            "example": {
                "account_id": "account-id-example",
                "resource_id": "resource-id-example",
                "rule_id": "rule-id-example",
                "findings": "findings-example"
            }
        }
