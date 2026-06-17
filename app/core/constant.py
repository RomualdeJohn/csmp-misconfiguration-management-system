COLUMNS_TO_EXCLUDE = [
    "Resource Version",
    "Resource Service Category",
    "Resource Tags",
    "Resource Status",
    "Status",
    "Rule Origin",
    "Technique ID",
    "Technique Name",
    "Tactic ID",
    "Tactic Name",
    "Section",
    "Version",
    "Requirement",
    "Frameworks",       
    "Benchmarks",
    "Applicable Profiles",
    "Cloud group",
    "Business impact",  
    "Business unit",
    "Environment",
    "Violation Type"
]

COLUMNS_TO_ADD = [
    "Reason",
    "Comment",
    "Fix Deadline",
]

MISCONFIG_MANAGEMENT_DB = "csmp_misconfiguration_management.db" 

CREATE_MISCONFIG_RECORDS_TABLE_SQL = """
                                    CREATE TABLE IF NOT EXISTS misconfig_records_table (
                                        account_id TEXT NOT NULL,
                                        resource_id TEXT NOT NULL,
                                        
                                        rule_id TEXT NOT NULL,
                                        findings TEXT NOT NULL,
                                        audit_ticket TEXT NOT NULL,
                                        type_audit TEXT NOT NULL,
                                        cloud_provider TEXT NOT NULL,
                                        region TEXT NOT NULL,
                                        account_name TEXT NOT NULL,
                                        resource_type TEXT NOT NULL,
                                        resource_type_name TEXT NOT NULL,
                                        resource_service TEXT NOT NULL,
                                        severity TEXT NOT NULL,
                                        rule_name TEXT NOT NULL,
                                        rule_description TEXT NOT NULL,
                                        remediation TEXT NOT NULL,
                                        reason TEXT,
                                        comment TEXT,
                                        fix_deadline DATE,
                                        last_modified_by TEXT,
                                        last_modified_at DATETIME,
                                        
                                        PRIMARY KEY (account_id, resource_id, rule_id, findings)
                                    );
                                """

CREATE_FIXED_MISCONFIG_RECORDS_TABLE_SQL = """
                                    CREATE TABLE IF NOT EXISTS fixed_misconfig_records_table (
                                        account_id TEXT NOT NULL,
                                        resource_id TEXT NOT NULL,
                                        
                                        rule_id TEXT NOT NULL,
                                        findings TEXT NOT NULL,
                                        audit_ticket TEXT NOT NULL,
                                        type_audit TEXT NOT NULL,
                                        cloud_provider TEXT NOT NULL,
                                        region TEXT NOT NULL,
                                        account_name TEXT NOT NULL,
                                        resource_type TEXT NOT NULL,
                                        resource_type_name TEXT NOT NULL,
                                        resource_service TEXT NOT NULL,
                                        severity TEXT NOT NULL,
                                        rule_name TEXT NOT NULL,
                                        rule_description TEXT NOT NULL,
                                        remediation TEXT NOT NULL,
                                        reason TEXT,
                                        comment TEXT,
                                        fix_deadline DATE,
                                        last_modified_by TEXT,
                                        last_modified_at DATETIME,
                                        
                                        PRIMARY KEY (account_id, resource_id, rule_id, findings)
                                    );
                                """

MISCONFIG_RECORDS_TABLE = "misconfig_records_table"
FIXED_MISCONFIG_RECORDS_TABLE = "fixed_misconfig_records_table"
BUCKET_NAME = "cspm-misconfig-mgmt-system-db-backup"
BACKUP_RETENTION_COUNT = 4

REASON_FIXED = "fixed"
REASON_FALSE_POSITIVE = "false positive"
REASON_RISK_ACCEPTANCE = "risk acceptance"
REASON_BUSINESS_REQUIRED = "business required"
REASON_PUBLICLY = "publicly"
