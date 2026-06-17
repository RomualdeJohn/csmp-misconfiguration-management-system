from app.core.logger import log
from app.core.setup_db import get_db_connection
from app.core.clients import get_config
from app.core.clients import DomoClient, AWSs3Client
from app.core.constant import MISCONFIG_MANAGEMENT_DB, MISCONFIG_RECORDS_TABLE, FIXED_MISCONFIG_RECORDS_TABLE, BACKUP_RETENTION_COUNT

import pandas as pd
from pathlib import Path
from datetime import datetime

class MigrateAndFetchData:
    def __init__(self):

        self.config = get_config()
        self.domo_client = DomoClient().get_client()
        self.aws_s3_client = AWSs3Client().get_client()
        self.bucket_name = self.config['AWS']['s3_backup_bucket']
        self.misconfig_records_table_domo_id = self.config['DOMO']['misconfig_records_table_domo_id']
        self.fixed_misconfig_records_table_domo_id = self.config['DOMO']['fixed_misconfig_records_table_domo_id']
        self.misconfig_records_table_name = MISCONFIG_RECORDS_TABLE
        self.fixed_misconfig_records_table_name = FIXED_MISCONFIG_RECORDS_TABLE
        self.database_name = MISCONFIG_MANAGEMENT_DB
        self.local_database_path = Path(__file__).parent.parent / 'database' / MISCONFIG_MANAGEMENT_DB

        self.table_details = [
            {
                'table_name': self.misconfig_records_table_name,
                'domo_id': self.misconfig_records_table_domo_id
            }
        ]

    def migrate_data_to_domo(self):
        """
        Migrate data from SQLite to Domo
        """

        try:
            allowed_tables = {MISCONFIG_RECORDS_TABLE}
            
            for table_detail in self.table_details:
                with get_db_connection(self.database_name) as conn:

                    table_name = table_detail['table_name']
                    table_domo_id = table_detail['domo_id']
                    
                    if table_name not in allowed_tables:
                        raise ValueError(f"Invalid table name: {table_name}. Only whitelisted tables are allowed.")
                    
                    conn.row_factory = lambda cursor, row: dict(zip([col[0] for col in cursor.description], row))
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {table_name}")
                    rows = cursor.fetchall()

                    df = pd.DataFrame(rows)
                    self.domo_client.ds_update(table_domo_id, df)
                    log.info(f"Successfully uploaded {len(df)} records to Domo dataset table name : {table_name} | dataset id : {table_domo_id}")

        except Exception as e:
            log.error(f"Error migrating data from SQLite to Domo: {e}")
            raise

    def put_db_to_s3(self, file_content, key, bucket_name):
        try:
            response = self.aws_s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=file_content,
                ContentLength=len(file_content),
                ContentType='application/x-sqlite3'
            )
            return response
        except Exception as e:
            log.error(f"Error uploading database to S3: {e}")
            raise

    def backup_database_to_s3(self):
        """
        Backup database to S3
        """
        try:
            file_size = self.local_database_path.stat().st_size

            with open(self.local_database_path, 'rb') as f:
                file_content = f.read()

            # Upload the timestamped backup file to s3
            backup_timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            backup_timestamp_key = f"cspm_backup_database_{backup_timestamp}.db"

            self.put_db_to_s3(file_content, backup_timestamp_key, self.bucket_name)
            log.warning(f"Successfully uploaded {self.local_database_path} to s3://{self.bucket_name}/{backup_timestamp_key}")

            # Upload the latest backup file to s3
            latest_backup_key = f"latest.db"   

            self.put_db_to_s3(file_content, latest_backup_key, self.bucket_name)
            log.warning(f"Successfully uploaded {self.local_database_path} to s3://{self.bucket_name}/{latest_backup_key}")

            self.clean_up_old_backups()

            log.warning(f"Database backup completed: {file_size} bytes")
            
        except Exception as e:
            log.error(f"Unsuccessful database backup upload: {e}")
            raise

    def restore_database_from_s3(self):
        """
        Restore database from S3
        """
        try:
            response = self.aws_s3_client.get_object(
                Bucket=self.bucket_name,
                Key='latest.db'
            )

            file_content = response['Body'].read()
            with open(self.local_database_path, 'wb') as f:
                f.write(file_content)
            log.info(f"Successfully restored database from s3://{self.bucket_name}/latest.db to {self.local_database_path}")
            
        except Exception as e:
            log.error(f"Error restoring database from S3: {e}")
            raise
    
    def clean_up_old_backups(self):

        response = self.aws_s3_client.list_objects_v2(
            Bucket=self.bucket_name
        )

        timestamped_backups_list = []

        for obj in response['Contents']:
            key = obj['Key']

            if key.startswith('latest.db'):
                continue
            
            if 'cspm_backup_database_' in key and key.endswith('.db'):
                timestamped_backups_list.append({
                    'key': key,
                    'last_modified': obj['LastModified']
                })

        timestamped_backups_list.sort(key=lambda x: x['last_modified'], reverse=True)

        log.info(f"found {len(timestamped_backups_list)} timestamped backups")

        if len(timestamped_backups_list) > BACKUP_RETENTION_COUNT:
            backups_to_delete = timestamped_backups_list[BACKUP_RETENTION_COUNT:]
            
            for backup in backups_to_delete:
                key = backup['key']
                log.info(f"Deleting old backup: {key}")
                self.aws_s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            log.info(f"Deleted {len(backups_to_delete)} old backups")
        else:
            log.info("No old backups to delete")
        
        for backup in timestamped_backups_list:
            log.info(f"backup: {backup['key']}, last modified: {backup['last_modified']}")

# if __name__ == '__main__':
#     migrate_and_fetch_data = MigrateAndFetchData()
#     migrate_and_fetch_data.restore_database_from_s3()