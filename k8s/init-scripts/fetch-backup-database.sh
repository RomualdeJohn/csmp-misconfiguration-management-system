#!/bin/sh
set -e

echo "Reading AWS credentials from config.ini"

export AWS_ACCESS_KEY_ID=$(grep -A 10 "\[AWS\]" /config/config.ini | grep "access_key_id" | cut -d'=' -f2 | tr -d ' ')
export AWS_SECRET_ACCESS_KEY=$(grep -A 10 "\[AWS\]" /config/config.ini | grep "secret_access_key" | cut -d'=' -f2 | tr -d ' ')
export AWS_REGION=$(grep -A 10 "\[AWS\]" /config/config.ini | grep "region" | cut -d'=' -f2 | tr -d ' ')

S3_BUCKET=$(grep -A 10 "\[AWS\]" /config/config.ini | grep "s3_backup_bucket" | cut -d'=' -f2 | tr -d ' ')
S3_ENDPOINT=$(grep -A 10 "\[AWS\]" /config/config.ini | grep "endpoint_url" | cut -d'=' -f2 | tr -d ' ')

echo "AWS configuration is loaded!"
echo "S3 Endpoint: ${S3_ENDPOINT}"

echo "Checking if latest.db exists in S3 bucket..."
if aws s3 ls s3://${S3_BUCKET}/latest.db --endpoint-url=${S3_ENDPOINT} >/dev/null 2>&1; then
    echo "Found latest.db in S3, downloading..."
    aws s3 cp s3://${S3_BUCKET}/latest.db /data/csmp_misconfiguration_management.db --endpoint-url=${S3_ENDPOINT}
    echo "Successfully downloaded latest.db from S3"
else
    echo "No backup database (latest.db) found in S3. Proceeding without restore."
fi

if [ -f /data/csmp_misconfiguration_management.db ]; then
  chown 1000:1000 /data/csmp_misconfiguration_management.db || echo "Warning: Could not change ownership of database file"
  chmod 664 /data/csmp_misconfiguration_management.db || echo "Warning: Could not set permissions on database file"
fi
chown 1000:1000 /data || echo "Warning: Could not change ownership of database directory"
chmod 775 /data || echo "Warning: Could not set permissions on database directory"

echo "Fetching backup database is completed"

