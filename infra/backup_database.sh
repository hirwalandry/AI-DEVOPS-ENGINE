#!/bin/bash

CONTAINER_NAME="enterprise-postgres"
DB_USER="devops_admin"
DB_NAME="ai_devops_db"
BACKUP_DIR="/tmp/db_dumps"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
S3_BUCKET_URI="s3://your-enterprise-cold-storage-bucket/database-backups"
DAYS_TO_RETAIN=14

echo "▶ Starting automated multi-tenant database state backup pipeline..."
mkdir -p $BACKUP_DIR

docker exec $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_FILE

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo "❌ Error: Postgres binary data stream failed during compilation runtime extraction."
    exit 1
fi

echo "✅ Database dump compiled smoothly: $BACKUP_FILE"

aws s3 cp $BACKUP_FILE $S3_BUCKET_URI/backup_${DB_NAME}_${TIMESTAMP}.sql.gz

if [ $? -eq 0 ]; then
    echo "✅ Backup successfully synced to external secure cloud storage."
    rm -f $BACKUP_FILE
else
    echo "❌ Error: External cloud storage synchronization rejected the upload."
    exit 1
fi

echo "▶ Scrubbing expired historical backups from cloud storage..."
aws s3 ls $S3_BUCKET_URI/ | while read -r line; do
    create_date=$(echo "$line" | awk '{print $1" "$2}')
    create_timestamp=$(date -d "$create_date" +%s)
    cutoff_timestamp=$(date -d "$DAYS_TO_RETAIN days ago" +%s)

    if [ $create_timestamp -lt $cutoff_timestamp ]; then
        file_name=$(echo "$line" | awk '{print $4}')
        if [ ! -z "$file_name" ]; then
            aws s3 rm "$S3_BUCKET_URI/$file_name"
            echo "🗑️ Cleaned up expired backup file: $file_name"
        fi
    fi
done

echo "🏁 Data preservation sequence completed successfully."
